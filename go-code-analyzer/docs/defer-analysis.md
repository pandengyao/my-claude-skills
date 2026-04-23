# defer 开销分析指南

## defer 的开销

每个 defer 调用约 **50-100ns** 开销（Go 1.14+ 已优化，但仍有成本）。

## 检测模式

### 1. 循环内 defer（严重）
```go
// 危险模式
for _, file := range files {
    f, _ := os.Open(file)
    defer f.Close()  // defer 堆积！
}
```

**问题**：所有 defer 在函数结束时才执行，可能导致资源耗尽。

**优化**：
```go
for _, file := range files {
    func() {
        f, _ := os.Open(file)
        defer f.Close()
        // 处理文件
    }()
}
```

### 2. 热点函数中的 defer
```go
// 高频调用函数
func hotPath() {
    mu.Lock()
    defer mu.Unlock()  // 每次调用都有 defer 开销
    // 简单操作
}
```

**优化**：
```go
func hotPath() {
    mu.Lock()
    // 简单操作
    mu.Unlock()  // 直接调用
}
```

### 3. 不必要的 defer
```go
func simple() error {
    f, err := os.Open("file")
    if err != nil {
        return err
    }
    defer f.Close()
    
    data, err := io.ReadAll(f)
    if err != nil {
        return err  // defer 仍会执行
    }
    return nil
}
```

## 搜索关键词

- `for` + `defer`（循环内 defer）
- 高频调用函数中的 `defer`
- 基准测试标记的函数

## 何时使用 defer

✅ **推荐使用**：
- 资源清理（文件、连接）
- Panic 恢复
- 解锁操作（复杂函数）

❌ **避免使用**：
- 循环内
- 极简函数
- 性能关键路径

## 优化效果

| 场景 | 使用 defer | 不使用 defer | 提升 |
|------|-----------|-------------|------|
| 简单锁 | 150ns | 50ns | 3x |
| 文件关闭 | 200ns | 150ns | 1.3x |