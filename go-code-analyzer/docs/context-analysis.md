# Context 使用分析指南

## Context 的正确使用

### 1. context.Value 性能问题
```go
// 性能差 - 链式查找
ctx = context.WithValue(ctx, "key1", val1)
ctx = context.WithValue(ctx, "key2", val2)
v := ctx.Value("key1")  // O(n) 查找
```

**优化**：
```go
// 使用结构体包装多个值
type RequestContext struct {
    UserID   string
    TraceID  string
}
ctx = context.WithValue(ctx, requestCtxKey, &RequestContext{...})
```

### 2. Context 未传递
```go
// 问题模式
func process(ctx context.Context) {
    go func() {
        // 没有使用 ctx，无法响应取消
        doWork()
    }()
}
```

### 3. Context 泄漏
```go
// 问题模式
ctx, cancel := context.WithCancel(parent)
// 忘记调用 cancel()
```

## 搜索关键词

- `context.WithValue`
- `ctx.Value(`
- `context.WithCancel`
- `context.WithTimeout`

## 最佳实践

```go
func process(ctx context.Context) error {
    // 派生新 context 时记得 cancel
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()  // 必须调用
    
    // 传递给子 goroutine
    go func(ctx context.Context) {
        select {
        case <-ctx.Done():
            return
        default:
            doWork()
        }
    }(ctx)
    
    return nil
}
```