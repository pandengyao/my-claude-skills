# 接口装箱分析指南

## 什么是接口装箱

当值类型赋给接口类型时，Go 会进行"装箱"操作，涉及内存分配和复制。

## 装箱开销

```go
var x interface{} = 42  // 装箱：分配内存 + 复制值
```

每次装箱：
- 堆内存分配（16-24 bytes）
- 值复制
- GC 压力增加

## 检测模式

### 1. 函数参数为 interface{}
```go
func process(v interface{}) {  // 每次调用都装箱
    // ...
}
```

### 2. 切片/Map 存储 interface{}
```go
items := []interface{}{}
items = append(items, 42)  // 装箱
```

### 3. 循环中的装箱
```go
for i := 0; i < 1000; i++ {
    fmt.Println(i)  // 每次都装箱 i
}
```

## 搜索关键词

- `interface{}` 参数
- `[]interface{}`
- `map[string]interface{}`
- `any` (Go 1.18+)

## 优化建议

### 使用泛型（Go 1.18+）
```go
// 优化前
func Sum(items []interface{}) float64

// 优化后
func Sum[T Number](items []T) T
```

### 使用具体类型
```go
// 优化前
func process(v interface{})

// 优化后
func processInt(v int)
func processString(v string)
```

### 使用类型断言池
```go
// 高频场景使用 sync.Pool
var intPool = sync.Pool{
    New: func() interface{} { return new(int) },
}
```

## 可接受场景

- 日志函数参数
- JSON 解析结果
- 通用容器（无泛型替代时）