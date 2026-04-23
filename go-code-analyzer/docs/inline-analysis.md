# 内联失败分析指南

## 什么是内联

内联是编译器将函数调用替换为函数体，消除调用开销。

## 内联条件

Go 编译器自动内联满足以下条件的函数：
- 函数体足够小（< 80 nodes）
- 无复杂控制流
- 非递归
- 无 `go`/`defer` 语句

## 检测方法

```bash
# 查看内联决策
go build -gcflags="-m" ./...

# 详细原因
go build -gcflags="-m -m" ./...
```

## 输出解读

```
./main.go:10:6: can inline foo        # 可以内联
./main.go:20:6: cannot inline bar: function too complex  # 不能内联
./main.go:30:6: inlining call to foo  # 调用被内联
```

## 常见内联失败原因

| 原因 | 说明 |
|------|------|
| function too complex | 函数体过大 |
| unhandled op | 包含不支持的操作 |
| has defer | 包含 defer |
| recursive | 递归函数 |
| has go | 包含 go 语句 |

## 优化建议

### 拆分大函数
```go
// 内联失败
func bigFunc() {
    // 100 行代码
}

// 拆分后可内联
func smallFunc1() { ... }
func smallFunc2() { ... }
```

### 热点路径简化
```go
// 热点函数保持简单
func hotPath(x int) int {
    return x * 2
}
```

### 使用编译器指令
```go
//go:noinline  // 禁止内联
func mustNotInline() {}
```