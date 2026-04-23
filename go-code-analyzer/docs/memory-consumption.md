# 大内存消耗分析指南

## 常见大内存消耗模式

### 1. 大切片创建

```go
// 潜在问题 - 预分配过大
data := make([]byte, 10*1024*1024)  // 10MB

// 潜在问题 - 一次性读取大文件
content, _ := ioutil.ReadFile(largefile)  // 整个文件加载到内存
```

**检测关键词**：
- `make([]` 后跟大数字或 `*1024*1024`
- `ioutil.ReadFile`, `io.ReadAll`

**优化建议**：
- 使用流式处理代替一次性加载
- 使用 `bufio.Scanner` 或 `io.Reader` 分块读取

### 2. 字符串拼接

```go
// 低效模式 - 循环中字符串拼接
var result string
for _, s := range items {
    result += s  // 每次创建新字符串
}
```

**检测关键词**：
- 循环内 `+=` 字符串操作
- `fmt.Sprintf` 在循环中高频调用

**优化建议**：
```go
// 使用 strings.Builder
var builder strings.Builder
for _, s := range items {
    builder.WriteString(s)
}
result := builder.String()
```

### 3. 切片未预分配

```go
// 低效模式 - 动态扩容
var results []Item
for _, raw := range data {
    results = append(results, process(raw))  // 多次扩容
}
```

**检测关键词**：
- `var slice []T` 后跟循环 `append`
- `make([]T, 0)` 未指定容量

**优化建议**：
```go
// 预分配容量
results := make([]Item, 0, len(data))
for _, raw := range data {
    results = append(results, process(raw))
}
```

### 4. Map 未预分配

```go
// 低效模式 - 动态扩容
m := make(map[string]int)  // 未指定大小
for _, item := range largeData {
    m[item.Key] = item.Value  // 多次 rehash
}
```

**检测关键词**：
- `make(map[` 未指定大小，后跟大量写入

**优化建议**：
```go
m := make(map[string]int, len(largeData))
```

### 5. JSON 序列化大对象

```go
// 潜在问题 - 大对象 JSON 操作
data, _ := json.Marshal(hugeStruct)  // 内存翻倍
json.Unmarshal(largeJSON, &obj)
```

**检测关键词**：
- `json.Marshal`, `json.Unmarshal` 处理大数据
- `encoding/json` 用于大文件

**优化建议**：
- 使用 `json.Encoder`/`json.Decoder` 流式处理
- 考虑使用 `json-iterator` 或 `easyjson`

### 6. 不必要的数据复制

```go
// 潜在问题 - 值传递大结构体
type BigStruct struct {
    Data [1024]byte
    // ... 更多字段
}

func process(b BigStruct) {  // 每次调用复制整个结构体
    // ...
}
```

**检测关键词**：
- 函数参数为大结构体值类型
- 结构体包含大数组或多字段

**优化建议**：
- 大结构体使用指针传递
- 考虑只传递必要字段

### 7. 缓存无限增长

```go
// 危险模式 - 无限制缓存
var cache = make(map[string][]byte)

func Get(key string) []byte {
    if v, ok := cache[key]; ok {
        return v
    }
    v := loadFromDB(key)
    cache[key] = v  // 无限增长
    return v
}
```

**检测关键词**：
- 全局 map 变量
- 只有写入没有删除/清理逻辑

**优化建议**：
- 使用 LRU 缓存限制大小
- 添加 TTL 过期机制
- 使用 `sync.Map` 并定期清理

## 执行步骤

1. 搜索大内存分配模式（`make([]`, `ReadFile`, `ReadAll`）
2. 搜索循环中的字符串拼接
3. 搜索未预分配的切片和 Map
4. 搜索大结构体的值传递
5. 检查全局缓存的大小限制
6. 评估内存消耗并提供优化建议

## 内存消耗评估标准

| 级别 | 内存大小 | 建议 |
|------|----------|------|
| 🟢 低 | < 1 MB | 可接受 |
| 🟡 中 | 1-10 MB | 检查是否必要 |
| 🔴 高 | > 10 MB | 需要优化 |