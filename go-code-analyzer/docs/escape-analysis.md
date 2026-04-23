# 内存逃逸分析指南

## 什么是内存逃逸

当 Go 编译器无法证明变量在函数返回后不再被使用时，该变量会从栈"逃逸"到堆上分配，增加 GC 压力。

## 常见逃逸场景

### 1. 返回局部变量指针

```go
// 会逃逸
func createUser() *User {
    u := User{Name: "test"}  // u 逃逸到堆
    return &u
}
```

### 2. 发送指针到 channel

```go
// 会逃逸
func send(ch chan *Data) {
    d := Data{}  // d 逃逸到堆
    ch <- &d
}
```

### 3. 在闭包中引用局部变量

```go
// 会逃逸
func closure() func() int {
    x := 10  // x 逃逸到堆
    return func() int {
        return x
    }
}
```

### 4. 存储到接口类型

```go
// 可能逃逸
func toInterface(x int) interface{} {
    return x  // x 可能逃逸
}
```

### 5. 切片/Map 存储指针

```go
// 会逃逸
func storePointer() {
    slice := make([]*int, 10)
    x := 42  // x 逃逸到堆
    slice[0] = &x
}
```

### 6. 切片容量超过栈限制

```go
// 大切片会逃逸
func bigSlice() {
    s := make([]byte, 64*1024)  // 超过栈大小，逃逸到堆
}
```

### 7. 变量大小在编译时未知

```go
// 动态大小会逃逸
func dynamicSize(n int) {
    s := make([]byte, n)  // n 不确定，逃逸到堆
}
```

## 分析方法

### 使用编译器逃逸分析

```bash
# 基础逃逸分析
go build -gcflags="-m" ./...

# 详细逃逸分析（显示逃逸原因）
go build -gcflags="-m -m" ./...

# 分析单个文件
go build -gcflags="-m" path/to/file.go
```

### 输出解读

```
./main.go:10:2: moved to heap: x          # 变量 x 逃逸到堆
./main.go:15:9: &y escapes to heap        # y 的地址逃逸
./main.go:20:6: can inline foo            # 函数可内联（好）
./main.go:25:3: leaking param: p          # 参数泄漏
```

## 检测关键词

代码审查时关注：

1. **返回指针的函数**：`return &`
2. **闭包捕获变量**：函数内定义函数并引用外部变量
3. **接口转换**：`interface{}` 参数或返回值
4. **大对象创建**：`make([]T, n)` 其中 n > 10000 或动态
5. **切片/Map 存储指针**：`[]*T` 或 `map[K]*V`

## 执行步骤

1. 对目标包运行 `go build -gcflags="-m -m" ./... 2>&1`
2. 解析输出，识别逃逸变量
3. 使用 `extract_content_blocks` 读取逃逸位置的代码
4. 分析逃逸原因，评估影响
5. 提供优化建议（如使用 sync.Pool、避免不必要的指针等）

## 优化建议模板

| 逃逸原因 | 优化建议 |
|----------|----------|
| 返回局部变量指针 | 考虑返回值而非指针，或使用对象池 |
| 闭包捕获 | 将变量作为参数传递 |
| 接口转换 | 使用泛型或具体类型 |
| 动态切片大小 | 预估合理容量，使用固定大小 |
| 大对象 | 使用 sync.Pool 复用 |
