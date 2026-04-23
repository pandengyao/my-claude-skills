# range 复制分析指南

## range 的复制行为

`for _, v := range slice` 中，`v` 是元素的**复制**，大结构体会有性能开销。

## 检测模式

### 大结构体复制
```go
type BigStruct struct {
    Data [1024]byte
    // 更多字段...
}

// 问题模式 - 每次迭代复制整个结构体
for _, item := range bigSlice {
    process(item)  // item 是复制
}
```

### Map 迭代复制
```go
for k, v := range bigMap {
    // k 和 v 都是复制
}
```

## 优化方案

### 使用索引
```go
for i := range bigSlice {
    process(&bigSlice[i])  // 无复制
}
```

### 使用指针切片
```go
slice := []*BigStruct{...}
for _, item := range slice {
    process(item)  // 只复制指针
}
```

### 只取需要的字段
```go
for i := range slice {
    processName(slice[i].Name)  // 只访问需要的字段
}
```

## 搜索方法

1. 查找 `for _, v := range`
2. 检查被迭代的类型
3. 评估元素大小（>64 bytes 需关注）

## 阈值建议

| 元素大小 | 建议 |
|----------|------|
| < 64 B | range 复制可接受 |
| 64-256 B | 考虑使用索引 |
| > 256 B | 必须优化 |