# Benchmark 完整性检查指南

## 检查维度

### 1. 关键函数覆盖率
- 热点路径是否有基准测试
- 核心算法是否有性能基线

### 2. 测试准确性
```go
// 问题模式 - 编译器优化掉了
func BenchmarkBad(b *testing.B) {
    for i := 0; i < b.N; i++ {
        _ = compute(i)  // 结果未使用，可能被优化
    }
}

// 正确模式
var result int
func BenchmarkGood(b *testing.B) {
    var r int
    for i := 0; i < b.N; i++ {
        r = compute(i)
    }
    result = r  // 防止优化
}
```

### 3. 内存分配统计
```go
func BenchmarkWithAllocs(b *testing.B) {
    b.ReportAllocs()  // 报告内存分配
    for i := 0; i < b.N; i++ {
        process()
    }
}
```

## 搜索关键词

- `func Benchmark`
- `testing.B`
- `b.ReportAllocs()`
- `b.ResetTimer()`

## 推荐结构

```go
func BenchmarkProcess(b *testing.B) {
    // 初始化（不计入测试时间）
    data := setupTestData()
    
    b.ReportAllocs()
    b.ResetTimer()
    
    for i := 0; i < b.N; i++ {
        result = process(data)
    }
}
```

## 运行命令

```bash
# 运行基准测试
go test -bench=. -benchmem ./...

# 比较两次结果
go test -bench=. -count=5 > old.txt
# 修改代码后
go test -bench=. -count=5 > new.txt
benchstat old.txt new.txt
```