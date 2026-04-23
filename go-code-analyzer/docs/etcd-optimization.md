# etcd 优化分析指南

## 常见问题

### 1. 客户端配置不当

```go
// 问题模式 - 默认配置
client, _ := clientv3.New(clientv3.Config{
    Endpoints: []string{"localhost:2379"},
    // 缺少关键配置
})
```

**推荐配置**：
```go
client, _ := clientv3.New(clientv3.Config{
    Endpoints:            []string{"localhost:2379"},
    DialTimeout:          5 * time.Second,
    DialKeepAliveTime:    10 * time.Second,
    DialKeepAliveTimeout: 3 * time.Second,
    MaxCallSendMsgSize:   2 * 1024 * 1024,  // 2MB
    MaxCallRecvMsgSize:   2 * 1024 * 1024,
    AutoSyncInterval:     time.Minute,       // 自动同步端点
    RejectOldCluster:     true,
})
```

### 2. Watch 泄漏

```go
// 问题模式 - Watch 未关闭
func watchKey(client *clientv3.Client, key string) {
    watchChan := client.Watch(context.Background(), key)
    for resp := range watchChan {
        // 处理事件
    }
    // context.Background() 永不取消，Watch 泄漏
}

// 正确模式
func watchKey(ctx context.Context, client *clientv3.Client, key string) {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()  // 确保取消
    
    watchChan := client.Watch(ctx, key)
    for resp := range watchChan {
        // 处理事件
    }
}
```

### 3. 租约续期问题

```go
// 问题模式 - 手动续期
lease, _ := client.Grant(ctx, 10)
go func() {
    for {
        client.KeepAliveOnce(ctx, lease.ID)  // 可能漏续
        time.Sleep(3 * time.Second)
    }
}()

// 正确模式 - 自动续期
lease, _ := client.Grant(ctx, 10)
keepAliveChan, _ := client.KeepAlive(ctx, lease.ID)
go func() {
    for range keepAliveChan {
        // 自动续期响应
    }
}()
```

### 4. 事务使用不当

```go
// 低效模式 - 多次独立操作
client.Put(ctx, "key1", "val1")
client.Put(ctx, "key2", "val2")
client.Put(ctx, "key3", "val3")

// 高效模式 - 事务批量
client.Txn(ctx).
    Then(
        clientv3.OpPut("key1", "val1"),
        clientv3.OpPut("key2", "val2"),
        clientv3.OpPut("key3", "val3"),
    ).Commit()
```

### 5. 前缀查询未优化

```go
// 问题模式 - 获取大量数据
resp, _ := client.Get(ctx, "/prefix/", clientv3.WithPrefix())
// 可能返回大量数据

// 优化模式 - 分页查询
opts := []clientv3.OpOption{
    clientv3.WithPrefix(),
    clientv3.WithLimit(100),
    clientv3.WithSort(clientv3.SortByKey, clientv3.SortAscend),
}
resp, _ := client.Get(ctx, "/prefix/", opts...)
```

### 6. 连接未复用

```go
// 问题模式 - 每次创建新连接
func getValue(key string) string {
    client, _ := clientv3.New(config)  // 每次创建
    defer client.Close()
    resp, _ := client.Get(ctx, key)
    return string(resp.Kvs[0].Value)
}

// 正确模式 - 复用连接
var etcdClient *clientv3.Client

func init() {
    etcdClient, _ = clientv3.New(config)
}

func getValue(key string) string {
    resp, _ := etcdClient.Get(ctx, key)
    return string(resp.Kvs[0].Value)
}
```

### 7. 未处理 Watch 事件压缩

```go
// 问题模式 - 忽略压缩错误
for resp := range watchChan {
    if resp.Err() != nil {
        continue  // 可能是压缩错误
    }
}

// 正确模式 - 处理压缩
for resp := range watchChan {
    if resp.CompactRevision > 0 {
        // 需要从新版本重新 Watch
        newWatchChan := client.Watch(ctx, key, 
            clientv3.WithRev(resp.CompactRevision))
    }
}
```

## 搜索关键词

- `clientv3.New`
- `client.Watch(`
- `client.Grant(`, `client.KeepAlive(`
- `client.Txn(`
- `clientv3.WithPrefix(`

## 检测维度

| 检查项 | 严重程度 | 说明 |
|--------|----------|------|
| 超时未配置 | 🔴 高 | 可能永久阻塞 |
| Watch 泄漏 | 🔴 高 | 资源耗尽 |
| 连接未复用 | 🟡 中 | 性能损耗 |
| 未使用事务 | 🟡 中 | 一致性问题 |
| 大数据查询无分页 | 🟡 中 | 内存压力 |

## 性能建议

| 配置项 | 建议值 |
|--------|--------|
| DialTimeout | 5s |
| 租约 TTL | 10-30s |
| 事务操作数 | < 128 |
| 单 Value 大小 | < 1.5MB |