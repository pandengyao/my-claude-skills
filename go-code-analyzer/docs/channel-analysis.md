# Channel 分析指南

## Channel 选择原则

| 类型 | 适用场景 | 开销 |
|------|----------|------|
| 无缓冲 | 同步通信、握手 | 高（阻塞） |
| 有缓冲 | 异步通信、削峰 | 中 |
| 大缓冲 | 批量处理 | 内存占用 |

## 检测模式

### 1. 无缓冲 Channel 滥用
```go
// 可能问题
ch := make(chan Data)  // 无缓冲
go func() {
    ch <- data  // 阻塞直到被接收
}()
```

### 2. 缓冲区过大
```go
ch := make(chan Data, 1000000)  // 可能浪费内存
```

### 3. Channel 作为计数器（性能差）
```go
// 不推荐
counter := make(chan int, 1)
counter <- 0
func inc() {
    v := <-counter
    counter <- v + 1
}
```

### 4. select 无 default
```go
// 可能阻塞
select {
case v := <-ch1:
    process(v)
case v := <-ch2:
    process(v)
// 无 default，会阻塞
}
```

## 搜索关键词

- `make(chan` - Channel 创建
- `<-` - Channel 操作
- `select {` - 多路复用

## 优化建议

### 缓冲区大小选择
```go
// CPU 密集型任务
ch := make(chan Task, runtime.NumCPU())

// I/O 密集型任务
ch := make(chan Task, 100)

// 批量处理
ch := make(chan Item, batchSize)
```

### 使用 sync 替代简单同步
```go
// Channel 方式（开销大）
done := make(chan struct{})
go func() {
    work()
    close(done)
}()
<-done

// WaitGroup 方式（更高效）
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    work()
}()
wg.Wait()
```

## 性能对比

| 操作 | 耗时 |
|------|------|
| 无缓冲 send/recv | ~200ns |
| 有缓冲 send/recv | ~100ns |
| atomic.AddInt64 | ~10ns |
| Mutex Lock/Unlock | ~20ns |