# 结构体字段对齐指南

## 内存对齐原理

CPU 按字长访问内存，未对齐的字段需要填充（padding），导致内存浪费。

## 对齐规则

| 类型 | 大小 | 对齐边界 |
|------|------|----------|
| bool | 1 | 1 |
| int8/uint8 | 1 | 1 |
| int16/uint16 | 2 | 2 |
| int32/uint32/float32 | 4 | 4 |
| int64/uint64/float64 | 8 | 8 |
| pointer/string/slice | 8/16/24 | 8 |

## 检测模式

### 未优化的结构体
```go
// 浪费内存
type Bad struct {
    a bool    // 1 byte + 7 padding
    b int64   // 8 bytes
    c bool    // 1 byte + 7 padding
    d int64   // 8 bytes
}  // 总计: 32 bytes

// 优化后
type Good struct {
    b int64   // 8 bytes
    d int64   // 8 bytes
    a bool    // 1 byte
    c bool    // 1 byte + 6 padding
}  // 总计: 24 bytes（节省 25%）
```

## 分析命令

```bash
# 查看结构体大小
go run -gcflags="-m" main.go

# 使用工具分析
go install golang.org/x/tools/go/analysis/passes/fieldalignment/cmd/fieldalignment@latest
fieldalignment ./...
```

## 优化原则

1. **大字段在前**：int64, float64, pointer
2. **小字段在后**：bool, int8
3. **相同大小字段相邻**
4. **考虑缓存行（64 bytes）**

## 搜索方法

1. 查找所有 `type ... struct`
2. 分析字段类型和顺序
3. 计算理论最优排列
4. 比较节省空间

## 注意事项

- 字段顺序可能影响代码可读性
- 某些情况下对齐是刻意的（如 atomic 操作）
- 小结构体优化收益有限
