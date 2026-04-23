# ClickVisual 优化分析指南

## 概述

ClickVisual 是基于 ClickHouse 的日志可视化平台，优化重点在于 ClickHouse 查询、数据写入和日志采集。

## 常见问题

### 1. ClickHouse 连接池配置

```go
// 问题模式 - 默认配置
conn, _ := clickhouse.Open(&clickhouse.Options{
    Addr: []string{"localhost:9000"},
    // 缺少连接池配置
})
```

**推荐配置**：
```go
conn, _ := clickhouse.Open(&clickhouse.Options{
    Addr: []string{"localhost:9000"},
    Auth: clickhouse.Auth{
        Database: "logs",
        Username: "default",
        Password: "",
    },
    DialTimeout:     5 * time.Second,
    MaxOpenConns:    10,
    MaxIdleConns:    5,
    ConnMaxLifetime: time.Hour,
    Compression: &clickhouse.Compression{
        Method: clickhouse.CompressionLZ4,
    },
    Settings: clickhouse.Settings{
        "max_execution_time": 60,
    },
})
```

### 2. 批量写入未优化

```go
// 低效模式 - 单条插入
for _, log := range logs {
    conn.Exec(ctx, "INSERT INTO logs VALUES (?)", log)
}

// 高效模式 - 批量插入
batch, _ := conn.PrepareBatch(ctx, "INSERT INTO logs")
for _, log := range logs {
    batch.Append(log.Time, log.Level, log.Message)
}
batch.Send()
```

### 3. 查询未使用索引

```go
// 低效查询 - 全表扫描
query := "SELECT * FROM logs WHERE message LIKE '%error%'"

// 高效查询 - 使用时间范围和索引
query := `
    SELECT * FROM logs 
    WHERE toDate(timestamp) = today() 
    AND level = 'error'
    LIMIT 1000
`
```

### 4. 大结果集未分页

```go
// 问题模式 - 返回大量数据
rows, _ := conn.Query(ctx, "SELECT * FROM logs")
var results []Log
for rows.Next() {
    var log Log
    rows.Scan(&log)
    results = append(results, log)  // 内存爆炸
}

// 优化模式 - 流式处理 + 分页
query := "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ? OFFSET ?"
rows, _ := conn.Query(ctx, query, pageSize, offset)
```

### 5. 日志采集缓冲区过小

```go
// 问题模式 - 频繁刷新
buffer := make([]Log, 0, 10)
for log := range logChan {
    buffer = append(buffer, log)
    if len(buffer) >= 10 {
        flush(buffer)  // 太频繁
        buffer = buffer[:0]
    }
}

// 优化模式 - 适当缓冲 + 定时刷新
buffer := make([]Log, 0, 10000)
ticker := time.NewTicker(5 * time.Second)
for {
    select {
    case log := <-logChan:
        buffer = append(buffer, log)
        if len(buffer) >= 10000 {
            flush(buffer)
            buffer = buffer[:0]
        }
    case <-ticker.C:
        if len(buffer) > 0 {
            flush(buffer)
            buffer = buffer[:0]
        }
    }
}
```

### 6. 查询超时未设置

```go
// 问题模式 - 无超时
rows, _ := conn.Query(context.Background(), slowQuery)

// 正确模式 - 设置超时
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
rows, _ := conn.Query(ctx, query)
```

### 7. 聚合查询未优化

```go
// 低效模式 - 客户端聚合
rows, _ := conn.Query(ctx, "SELECT * FROM logs WHERE level = 'error'")
count := 0
for rows.Next() {
    count++
}

// 高效模式 - 服务端聚合
var count uint64
conn.QueryRow(ctx, "SELECT count() FROM logs WHERE level = 'error'").Scan(&count)
```

### 8. 未使用物化视图

```go
// 每次查询都聚合
query := `
    SELECT toDate(timestamp) as day, count() as cnt 
    FROM logs 
    GROUP BY day
`

// 优化 - 创建物化视图
/*
CREATE MATERIALIZED VIEW logs_daily_mv
ENGINE = SummingMergeTree()
ORDER BY day
AS SELECT toDate(timestamp) as day, count() as cnt 
FROM logs GROUP BY day
*/
query := "SELECT * FROM logs_daily_mv"
```

### 9. 日志字段解析在查询时

```go
// 低效 - 查询时解析
query := `
    SELECT extractURLParameter(url, 'user_id') as user_id
    FROM logs
    WHERE ...
`

// 高效 - 写入时解析，存储到独立字段
// 建表时添加 user_id 字段，写入时提取
```

## 搜索关键词

- `clickhouse.Open`
- `conn.Query(`, `conn.Exec(`
- `PrepareBatch`, `batch.Send()`
- `clickhouse.Settings`
- `Compression`

## 检测维度

| 检查项 | 严重程度 | 说明 |
|--------|----------|------|
| 连接池未配置 | ?? 高 | 影响并发性能 |
| 单条插入 | 🔴 高 | 写入性能极差 |
| 全表扫描 | 🔴 高 | 查询超时 |
| 无超时设置 | 🟡 中 | 可能阻塞 |
| 缓冲区过小 | 🟡 中 | I/O 压力大 |
| 未压缩 | 🟡 中 | 网络带宽浪费 |

## 性能建议

| 配置项 | 建议值 |
|--------|--------|
| 批量写入大小 | 10000-50000 条 |
| 刷新间隔 | 5-10s |
| 查询超时 | 30-60s |
| 压缩方式 | LZ4 |
| 连接池大小 | 5-20 |
| 结果集分页 | 1000-10000 条 |

## ClickHouse 优化 SQL 示例

```sql
-- 创建带索引的表
CREATE TABLE logs (
    timestamp DateTime,
    level String,
    message String,
    INDEX idx_level level TYPE set(100) GRANULARITY 4
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, level);

-- 使用 PREWHERE 优化
SELECT * FROM logs 
PREWHERE level = 'error'  -- 先过滤再读取
WHERE message LIKE '%timeout%';

-- 使用 FINAL 代替 GROUP BY
SELECT * FROM logs FINAL;  -- 对 ReplacingMergeTree
```