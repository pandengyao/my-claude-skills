# 内存泄漏检测指南

## 常见内存泄漏模式

### 1. 未关闭的资源

#### 文件句柄泄漏
```go
// 危险模式 - 缺少 Close
func readFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    // 缺少 defer f.Close()
    return ioutil.ReadAll(f)
}
```

#### HTTP 响应体泄漏
```go
// 危险模式 - 未关闭 Body
resp, err := http.Get(url)
if err != nil {
    return err
}
// 缺少 defer resp.Body.Close()
```

#### 数据库连接泄漏
```go
// 危险模式 - 未关闭 Rows
rows, err := db.Query("SELECT * FROM users")
if err != nil {
    return err
}
// 缺少 defer rows.Close()
for rows.Next() {
    // ...
}
```

### 2. Goroutine 泄漏

#### 阻塞的 channel 发送
```go
// 危险模式 - goroutine 永远阻塞
func leak() {
    ch := make(chan int)
    go func() {
        ch <- 1  // 永远阻塞，没有接收者
    }()
    // 函数返回，goroutine 泄漏
}
```

#### 阻塞的 channel 接收
```go
// 危险模式 - goroutine 永远等待
func leak() {
    ch := make(chan int)
    go func() {
        <-ch  // 永远等待，没有发送者
    }()
}
```

#### 无法退出的循环
```go
// 危险模式 - 没有退出机制
func leak() {
    go func() {
        for {
            // 没有 select case <-ctx.Done()
            doWork()
        }
    }()
}
```

#### Context 未传递
```go
// 危险模式 - 子 goroutine 无法取消
func process(ctx context.Context) {
    go func() {
        // 没有使用 ctx，无法响应取消
        for {
            doWork()
        }
    }()
}
```

### 3. Timer/Ticker 泄漏

```go
// 危险模式 - Timer 未 Stop
func timeout() {
    timer := time.NewTimer(time.Second)
    // 提前返回时 timer 未停止
    if condition {
        return  // 泄漏！
    }
    <-timer.C
}

// 危险模式 - Ticker 未 Stop
func periodic() {
    ticker := time.NewTicker(time.Second)
    // 缺少 defer ticker.Stop()
    for range ticker.C {
        // ...
    }
}
```

### 4. 切片内存泄漏

```go
// 潜在泄漏 - 保持对大底层数组的引用
func getFirst(data []byte) []byte {
    return data[:1]  // 仍然引用整个底层数组
}

// 正确做法
func getFirst(data []byte) []byte {
    result := make([]byte, 1)
    copy(result, data[:1])
    return result
}
```

### 5. Map 内存泄漏

```go
// 潜在泄漏 - Map 只增不减
var cache = make(map[string][]byte)

func add(key string, data []byte) {
    cache[key] = data  // 无限增长
}
// 缺少清理机制
```

### 6. 全局变量持有引用

```go
// 潜在泄漏 - 全局切片持续增长
var globalLog []string

func log(msg string) {
    globalLog = append(globalLog, msg)  // 无限增长
}
```

## 检测关键词

使用 `search_files` 搜索：

1. **资源打开**：
   - `os.Open`, `os.Create`, `os.OpenFile`
   - `http.Get`, `http.Post`, `http.Do`
   - `db.Query`, `db.QueryRow`, `db.Exec`
   - `sql.Open`, `gorm.Open`

2. **并发相关**：
   - `go func()` 检查是否有退出机制
   - `make(chan` 检查是否有关闭/退出
   - `select {` 检查是否有 `ctx.Done()` case

3. **定时器**：
   - `time.NewTimer`, `time.NewTicker`
   - `time.After`（在循环中使用时危险）

## 执行步骤

1. 搜索资源创建语句（Open, Query, NewTimer 等）
2. 检查是否有对应的 Close/Stop
3. 检查 defer 的位置是否正确（应在 err check 之后）
4. 搜索 `go func()` 并检查退出机制
5. 检查全局变量是否有清理逻辑
6. 生成泄漏风险报告

## 正确模式示例

```go
// 正确的资源管理
func readFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()  // ✅ 正确位置
    return ioutil.ReadAll(f)
}

// 正确的 goroutine 管理
func worker(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():  // ✅ 可以退出
            return
        default:
            doWork()
        }
    }
}

// 正确的 Ticker 使用
func periodic(ctx context.Context) {
    ticker := time.NewTicker(time.Second)
    defer ticker.Stop()  // ✅ 确保停止
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            doWork()
        }
    }
}
```