# 原子操作性能分析指南

## 并发原语概述

Go 提供多种并发原语，选择不当会导致性能问题：

| 原语 | 适用场景 | 性能特点 |
|------|----------|----------|
| `sync.Mutex` | 复杂临界区 | 中等开销 |
| `sync.RWMutex` | 读多写少 | 读操作低开销 |
| `atomic.*` | 简单计数器 | 最低开销 |
| `sync.Map` | 读多写少的Map | 读优化 |
| `channel` | 通信和同步 | 较高开销 |

## 常见性能问题

### 1. 锁粒度过大

```go
// 问题模式 - 大锁
type Cache struct {
    mu    sync.Mutex
    data  map[string][]byte
    stats map[string]int64
}

func (c *Cache) Get(key string) []byte {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.stats["reads"]++  // 统计也被锁住
    return c.data[key]
}
```

**优化建议**：
```go
// 分离锁
type Cache struct {
    dataMu  sync.RWMutex
    data    map[string][]byte
    statsMu sync.Mutex
    stats   map[string]int64
}

// 或使用 atomic 处理统计
type Cache struct {
    mu    sync.RWMutex
    data  map[string][]byte
    reads atomic.Int64
}
```

### 2. 误用 Mutex 代替 RWMutex

```go
// 问题模式 - 读多写少场景使用 Mutex
type Config struct {
    mu   sync.Mutex  // 应该用 RWMutex
    data map[string]string
}

func (c *Config) Get(key string) string {
    c.mu.Lock()      // 读操作也获取排他锁
    defer c.mu.Unlock()
    return c.data[key]
}
```

**检测信号**：
- `sync.Mutex` 保护的数据读操作远多于写操作
- Get/Read 类方法使用 Lock() 而非 RLock()

**优化建议**：
```go
type Config struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Config) Get(key string) string {
    c.mu.RLock()  // 读锁
    defer c.mu.RUnlock()
    return c.data[key]
}
```

### 3. 原子操作使用不当

#### 非原子的"读-改-写"
```go
// 问题模式 - 竞态条件
var counter int64

func increment() {
    if counter < 100 {        // 读
        counter++             // 改-写（非原子）
    }
}
```

**优化建议**：
```go
var counter atomic.Int64

func increment() {
    for {
        old := counter.Load()
        if old >= 100 {
            return
        }
        if counter.CompareAndSwap(old, old+1) {
            return
        }
    }
}
```

#### 过度使用 atomic
```go
// 问题模式 - atomic 操作复杂数据
type Stats struct {
    count    atomic.Int64
    sum      atomic.Int64
    min      atomic.Int64
    max      atomic.Int64
}

func (s *Stats) Record(val int64) {
    s.count.Add(1)
    s.sum.Add(val)
    // min/max 需要 CAS 循环，复杂且可能有一致性问题
}
```

**优化建议**：
```go
// 复杂场景使用 Mutex
type Stats struct {
    mu    sync.Mutex
    count int64
    sum   int64
    min   int64
    max   int64
}
```

### 4. 锁竞争严重

```go
// 问题模式 - 热点锁
var globalCounter struct {
    sync.Mutex
    value int64
}

// 所有 goroutine 竞争同一把锁
func increment() {
    globalCounter.Lock()
    globalCounter.value++
    globalCounter.Unlock()
}
```

**检测信号**：
- 单个 Mutex 被大量 goroutine 访问
- 临界区内有 I/O 或耗时操作

**优化建议**：
```go
// 方案1: 使用 atomic
var globalCounter atomic.Int64

func increment() {
    globalCounter.Add(1)
}

// 方案2: 分片减少竞争
type ShardedCounter struct {
    shards [16]struct {
        sync.Mutex
        value int64
    }
}

func (c *ShardedCounter) Inc(id int) {
    shard := &c.shards[id%16]
    shard.Lock()
    shard.value++
    shard.Unlock()
}
```

### 5. Channel 误用

#### 用 Channel 做计数器
```go
// 问题模式 - 性能差
counter := make(chan int, 1)
counter <- 0

func increment() {
    v := <-counter
    counter <- v + 1
}
```

**优化建议**：使用 `atomic.Int64`

#### 无缓冲 Channel 阻塞
```go
// 问题模式 - 同步阻塞
ch := make(chan Result)  // 无缓冲

go func() {
    ch <- expensiveWork()  // 阻塞直到有接收者
}()
```

**检测关键词**：
- `make(chan T)` 无缓冲 Channel
- Channel 发送在循环中

### 6. sync.Map 误用

```go
// 问题模式 - 写多场景使用 sync.Map
var m sync.Map

func process(items []Item) {
    for _, item := range items {
        m.Store(item.Key, item.Value)  // 频繁写入
    }
}
```

**适用条件**：
- `sync.Map` 适合：读多写少、key 稳定
- `sync.Map` 不适合：频繁写入、需要遍历

**优化建议**：频繁写入场景使用 `sync.RWMutex` + `map`

## 检测方法

### 搜索关键词

1. **锁相关**：
   - `sync.Mutex`, `sync.RWMutex`
   - `.Lock()`, `.Unlock()`, `.RLock()`, `.RUnlock()`

2. **原子操作**：
   - `atomic.`, `sync/atomic`
   - `.Add(`, `.Load(`, `.Store(`, `.Swap(`

3. **并发容器**：
   - `sync.Map`, `sync.Pool`
   - `sync.WaitGroup`, `sync.Once`

4. **Channel**：
   - `make(chan`, `<-`, `close(`

### 分析流程

1. 识别共享数据和保护机制
2. 分析读写比例
3. 评估锁粒度
4. 检查原子操作正确性
5. 识别潜在竞争热点

## 执行步骤

1. 搜索 `sync.Mutex` 和 `sync.RWMutex` 使用
2. 分析锁保护的数据访问模式
3. 搜索 `atomic.` 相关操作
4. 检查 Channel 使用方式
5. 使用 `go build -race` 检测数据竞争
6. 生成优化建议报告

## 性能测试命令

```bash
# 竞态检测
go build -race ./...
go test -race ./...

# 基准测试
go test -bench=. -benchmem ./...

# 锁竞争分析（需要 pprof）
go test -bench=. -mutexprofile=mutex.out ./...
go tool pprof mutex.out
```