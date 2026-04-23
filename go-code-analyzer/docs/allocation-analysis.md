# 内存分配合理性评估指南

## 评估维度

### 1. 不必要的内存分配

#### 循环内重复分配
```go
// 低效模式
for i := 0; i < 1000; i++ {
    buf := make([]byte, 1024)  // 每次循环都分配
    process(buf)
}
```

**优化建议**：
```go
// 提取到循环外
buf := make([]byte, 1024)
for i := 0; i < 1000; i++ {
    process(buf)
    // 如需重置：buf = buf[:0] 或 clear(buf)
}
```

#### 不必要的中间变量
```go
// 低效模式
func process(data []byte) string {
    temp := string(data)      // 分配 1
    result := strings.ToLower(temp)  // 分配 2
    return result
}
```

**优化建议**：
```go
// 减少中间分配
func process(data []byte) string {
    return strings.ToLower(string(data))
}
// 或使用 bytes.ToLower 避免 string 转换
```

### 2. 对象池使用建议

#### 适合使用 sync.Pool 的场景
```go
// 高频创建销毁的对象
type Buffer struct {
    data []byte
}

// 使用对象池
var bufferPool = sync.Pool{
    New: func() interface{} {
        return &Buffer{data: make([]byte, 4096)}
    },
}

func getBuffer() *Buffer {
    return bufferPool.Get().(*Buffer)
}

func putBuffer(b *Buffer) {
    b.data = b.data[:0]  // 重置
    bufferPool.Put(b)
}
```

**适用条件**：
- 对象创建频率高（> 1000/秒）
- 对象生命周期短
- 对象大小相对固定
- 对象可安全重用

**检测关键词**：
- 循环内 `new()` 或 `make()`
- 高频调用的函数中创建大对象
- HTTP handler 中创建临时缓冲区

### 3. 值类型 vs 指针类型选择

#### 小结构体（< 64 bytes）
```go
// 推荐值类型
type Point struct {
    X, Y float64  // 16 bytes
}

func distance(a, b Point) float64 {  // 值传递 OK
    return math.Sqrt((a.X-b.X)*(a.X-b.X) + (a.Y-b.Y)*(a.Y-b.Y))
}
```

#### 大结构体（> 64 bytes）
```go
// 推荐指针类型
type BigData struct {
    Data [1024]byte
    Meta string
}

func process(d *BigData) {  // 指针传递
    // ...
}
```

#### 需要修改的场景
```go
// 必须使用指针
func (u *User) UpdateName(name string) {
    u.Name = name  // 修改原对象
}
```

**评估标准**：

| 结构体大小 | 是否修改 | 推荐 |
|-----------|----------|------|
| < 64 B | 否 | 值类型 |
| < 64 B | 是 | 指针类型 |
| >= 64 B | 任意 | 指针类型 |
| 含指针/切片 | 任意 | 指针类型 |

### 4. 切片容量规划

#### 预估容量
```go
// 已知大小时预分配
items := make([]Item, 0, expectedCount)

// 未知但可估算
items := make([]Item, 0, 100)  // 合理初始值
```

#### 避免过度预分配
```go
// 不推荐 - 浪费内存
items := make([]Item, 0, 1000000)  // 可能用不了这么多

// 推荐 - 分批处理
const batchSize = 1000
items := make([]Item, 0, batchSize)
```

### 5. 字符串处理优化

#### 避免 []byte <-> string 转换
```go
// 低效模式
func process(data []byte) []byte {
    s := string(data)           // 分配
    s = strings.ToUpper(s)      // 分配
    return []byte(s)            // 分配
}

// 高效模式
func process(data []byte) []byte {
    return bytes.ToUpper(data)  // 原地修改
}
```

#### 使用 strings.Builder
```go
// 推荐
var b strings.Builder
b.Grow(estimatedSize)  // 预分配
for _, s := range parts {
    b.WriteString(s)
}
result := b.String()
```

## 检测方法

1. **搜索循环内分配**：
   - `for` + `make(` 或 `new(`
   - `range` + 对象创建

2. **搜索高频函数**：
   - HTTP handler 函数
   - 消息处理函数
   - 循环调用的函数

3. **分析结构体大小**：
   - 检查结构体定义
   - 评估传递方式

## 执行步骤

1. 使用 `go build -gcflags="-m"` 分析逃逸
2. 搜索循环内的内存分配
3. 识别高频调用路径
4. 检查大结构体传递方式
5. 评估 sync.Pool 适用性
6. 生成优化建议报告