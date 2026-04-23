# Goroutine 管理分析指南

## 常见问题

### 1. 无限制创建 Goroutine
```go
// 危险模式
func handleRequests(requests []Request) {
    for _, req := range requests {
        go process(req)  // 可能创建数百万 goroutine
    }
}
```

**问题**：
- 内存耗尽（每个 goroutine 约 2KB 栈）
- 调度开销过大
- 资源竞争加剧

### 2. Goroutine 泄漏
```go
// 危险模式
func leak() {
    ch := make(chan int)
    go func() {
        ch <- 1  // 永远阻塞
    }()
    // 没有接收者，goroutine 泄漏
}
```

## 检测关键词

- `go func()` 在循环内
- `go` 关键字无数量限制
- 无 `context` 取消机制

## 优化方案

### Worker Pool 模式
```go
func WorkerPool(jobs <-chan Job, results chan<- Result, workers int) {
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }()
    }
    wg.Wait()
    close(results)
}
```

### 使用 Semaphore 限制
```go
import "golang.org/x/sync/semaphore"

var sem = semaphore.NewWeighted(100)  // 最多 100 并发

func process(ctx context.Context, req Request) {
    sem.Acquire(ctx, 1)
    defer sem.Release(1)
    // 处理请求
}
```

### 使用 errgroup
```go
import "golang.org/x/sync/errgroup"

func processAll(ctx context.Context, items []Item) error {
    g, ctx := errgroup.WithContext(ctx)
    g.SetLimit(10)  // 限制并发数
    
    for _, item := range items {
        item := item
        g.Go(func() error {
            return process(ctx, item)
        })
    }
    return g.Wait()
}
```

## 推荐并发数

| 任务类型 | 推荐并发数 |
|----------|-----------|
| CPU 密集 | runtime.NumCPU() |
| I/O 密集 | NumCPU * 2-4 |
| 网络请求 | 100-1000 |
| 数据库操作 | 连接池大小 |