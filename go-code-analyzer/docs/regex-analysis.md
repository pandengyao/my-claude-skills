# 正则表达式检测指南

## 正则编译开销

`regexp.Compile` 是**昂贵操作**，应在循环外执行。

## 检测模式

### 1. 循环内编译（严重）
```go
// 危险模式
for _, s := range strings {
    matched, _ := regexp.MatchString(`\d+`, s)  // 每次编译
}
```

### 2. 函数内重复编译
```go
func validate(s string) bool {
    re := regexp.MustCompile(`^[a-z]+$`)  // 每次调用都编译
    return re.MatchString(s)
}
```

## 搜索关键词

- `regexp.Compile(`
- `regexp.MustCompile(`
- `regexp.MatchString(`
- `regexp.Match(`

## 优化方案

### 包级别预编译
```go
var emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)

func validateEmail(email string) bool {
    return emailRegex.MatchString(email)
}
```

### init 函数编译
```go
var patterns map[string]*regexp.Regexp

func init() {
    patterns = map[string]*regexp.Regexp{
        "email": regexp.MustCompile(`...`),
        "phone": regexp.MustCompile(`...`),
    }
}
```

## 性能对比

| 操作 | 耗时 |
|------|------|
| regexp.Compile | ~10μs |
| 预编译正则匹配 | ~100ns |
| strings.Contains | ~10ns |

**提示**：简单匹配优先使用 `strings` 包。