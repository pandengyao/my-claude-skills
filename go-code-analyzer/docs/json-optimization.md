# JSON 序列化优化指南

## 标准库性能

`encoding/json` 使用反射，性能较低。

## 检测模式

### 1. 热点路径使用标准库
```go
// 高频调用场景
func handleRequest(w http.ResponseWriter, r *http.Request) {
    var req Request
    json.NewDecoder(r.Body).Decode(&req)  // 每次反射
    
    resp := process(req)
    json.NewEncoder(w).Encode(resp)  // 每次反射
}
```

### 2. 大对象序列化
```go
data, _ := json.Marshal(hugeStruct)  // 内存翻倍
```

## 搜索关键词

- `encoding/json`
- `json.Marshal`, `json.Unmarshal`
- `json.NewEncoder`, `json.NewDecoder`

## 优化方案

### 使用高性能库

| 库 | 性能提升 | 特点 |
|---|---------|------|
| json-iterator | 2-3x | 兼容标准库 |
| easyjson | 4-5x | 需代码生成 |
| sonic | 5-10x | 需 amd64 |
| go-json | 2-3x | 兼容标准库 |

### json-iterator 替换
```go
import jsoniter "github.com/json-iterator/go"

var json = jsoniter.ConfigCompatibleWithStandardLibrary

// 用法完全相同
json.Marshal(v)
json.Unmarshal(data, &v)
```

### 流式处理大文件
```go
// 避免一次性加载
decoder := json.NewDecoder(file)
for decoder.More() {
    var item Item
    decoder.Decode(&item)
    process(item)
}
```

## 其他优化

- 使用 `json.RawMessage` 延迟解析
- 使用 `omitempty` 减少输出
- 预分配缓冲区