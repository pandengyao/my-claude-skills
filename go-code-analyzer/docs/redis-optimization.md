# Redis 优化分析指南

## 常见问题

### 1. 连接池配置不当

```go
// 问题模式 - 默认配置
client := redis.NewClient(&redis.Options{
    Addr: "localhost:6379",
    // 未设置连接池参数
})
```

**推荐配置**：
```go
client := redis.NewClient(&redis.Options{
    Addr:         "localhost:6379",
    PoolSize:     100,              // 连接池大小
    MinIdleConns: 10,               // 最小空闲连接
    MaxRetries:   3,                // 最大重试次数
    DialTimeout:  5 * time.Second,  // 连接超时
    ReadTimeout:  3 * time.Second,  // 读超时
    WriteTimeout: 3 * time.Second,  // 写超时
    PoolTimeout:  4 * time.Second,  // 获取连接超时
    IdleTimeout:  5 * time.Minute,  // 空闲超时
})
```

### 2. 未使用 Pipeline 批量操作

```go
// 低效模式 - 多次网络往返
for _, key := range keys {
    client.Get(ctx, key)  // 每次一个 RTT
}

// 高效模式 - Pipeline
pipe := client.Pipeline()
for _, key := range keys {
    pipe.Get(ctx, key)
}
results, _ := pipe.Exec(ctx)
```

### 3. 大 Key 问题

```go
// 问题模式 - 存储大对象
client.Set(ctx, "big_key", hugeData, 0)  // 可能阻塞

// 优化 - 分片存储
for i, chunk := range splitData(hugeData) {
    client.Set(ctx, fmt.Sprintf("key:%d", i), chunk, 0)
}
```

### 4. 热点 Key 问题

```go
// 问题模式 - 单点热点
client.Get(ctx, "hot_key")  // 高并发访问

// 优化 - 本地缓存 + 分布式
var localCache sync.Map
func GetWithLocalCache(key string) string {
    if v, ok := localCache.Load(key); ok {
        return v.(string)
    }
    v, _ := client.Get(ctx, key).Result()
    localCache.Store(key, v)
    return v
}
```

### 5. 未使用连接池状态监控

```go
// 推荐 - 监控连接池
stats := client.PoolStats()
log.Printf("Hits=%d Misses=%d Timeouts=%d TotalConns=%d IdleConns=%d",
    stats.Hits, stats.Misses, stats.Timeouts,
    stats.TotalConns, stats.IdleConns)
```

### 6. Lua 脚本未缓存

```go
// 低效模式 - 每次发送完整脚本
client.Eval(ctx, script, keys, args)

// 高效模式 - 预加载脚本
scriptSHA := client.ScriptLoad(ctx, script).Val()
client.EvalSha(ctx, scriptSHA, keys, args)
```

### 7. 未使用 Cluster 模式的正确方式

```go
// 问题模式 - 跨 slot 操作
client.MGet(ctx, "key1", "key2", "key3")  // 可能跨多个 slot

// 正确模式 - 使用 Hash Tag
client.MGet(ctx, "{user}:key1", "{user}:key2")  // 同一 slot
```

## 搜索关键词

- `redis.NewClient`
- `redis.NewClusterClient`
- `client.Get(`, `client.Set(`
- `client.Pipeline(`
- `PoolSize`, `MinIdleConns`

## 检测维度

| 检查项 | 严重程度 | 说明 |
|--------|----------|------|
| 连接池未配置 | 🔴 高 | 影响并发性能 |
| 未使用 Pipeline | 🟡 中 | 批量操作效率低 |
| 大 Key | 🔴 高 | 可能阻塞服务 |
| 热点 Key | 🟡 中 | 需要本地缓存 |
| 无超时配置 | 🔴 高 | 可能永久阻塞 |

## 性能建议

| 操作 | 建议 |
|------|------|
| 单次操作 | < 1ms |
| Pipeline 100 条 | < 10ms |
| 大 Key 阈值 | < 10KB |
| 连接池大小 | CPU * 10 |