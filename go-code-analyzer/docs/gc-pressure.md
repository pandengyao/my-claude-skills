# GC 压力分析指南

## GC 基础知识

Go 使用三色标记清除 GC，STW（Stop The World）时间影响延迟。

## 检测模式

### 1. 高频分配短生命周期对象
```go
// 问题模式
func process(data []byte) string {
    buf := make([]byte, 1024)  // 每次调用分配
    // 处理后丢弃
    return string(buf)
}
```

### 2. Finalizer 滥用
```go
// 危险模式
func newResource() *Resource {
    r := &Resource{}
    runtime.SetFinalizer(r, func(r *Resource) {
        r.Close()
    })
    return r
}
```

**问题**：Finalizer 延迟执行，增加 GC 负担。

### 3. 大量小对象
```go
// 每个请求创建多个小对象
type Request struct {
    Headers map[string]string  // 小 map
    Params  []string           // 小 slice
}
```

## 搜索关键词

- `runtime.SetFinalizer`
- 循环内 `make(`, `new(`
- `runtime.GC()` 手动调用

## 优化方案

### 使用 sync.Pool
```go
var bufPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 1024)
    },
}

func process(data []byte) string {
    buf := bufPool.Get().([]byte)
    defer bufPool.Put(buf)
    // 使用 buf
}
```

### 预分配 + 复用
```go
type Processor struct {
    buf []byte  // 复用缓冲区
}

func (p *Processor) Process(data []byte) {
    if p.buf == nil {
        p.buf = make([]byte, 1024)
    }
    // 复用 p.buf
}
```

### 避免 Finalizer
```go
// 显式关闭资源
defer resource.Close()
```

## GC 调优参数

```bash
# 设置 GC 目标百分比（默认 100）
GOGC=200  # 减少 GC 频率，增加内存使用

# 设置内存限制（Go 1.19+）
GOMEMLIMIT=1GiB
```