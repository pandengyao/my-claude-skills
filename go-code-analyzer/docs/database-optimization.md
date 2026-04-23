# 数据库优化指南

## 常见问题

### 1. 连接池配置不当
```go
// 默认配置可能不足
db, _ := sql.Open("postgres", connStr)
// 默认无限制，可能耗尽连接
```

**优化**：
```go
db.SetMaxOpenConns(25)        // 最大打开连接
db.SetMaxIdleConns(10)        // 最大空闲连接
db.SetConnMaxLifetime(5*time.Minute)  // 连接最大生命周期
db.SetConnMaxIdleTime(1*time.Minute)  // 空闲超时
```

### 2. N+1 查询问题
```go
// 问题模式
users, _ := db.Query("SELECT * FROM users")
for users.Next() {
    var u User
    users.Scan(&u)
    // 每个用户单独查询订单
    orders, _ := db.Query("SELECT * FROM orders WHERE user_id = ?", u.ID)
}
```

### 3. 未使用预编译语句
```go
// 每次编译
db.Query("SELECT * FROM users WHERE id = ?", id)

// 预编译复用
stmt, _ := db.Prepare("SELECT * FROM users WHERE id = ?")
stmt.Query(id)
```

### 4. 未关闭 Rows
```go
rows, _ := db.Query(...)
// 忘记 defer rows.Close()
```

## 搜索关键词

- `sql.Open(`
- `db.Query(`, `db.Exec(`
- `SetMaxOpenConns`, `SetMaxIdleConns`
- `rows.Close()`

## 最佳实践

```go
// 连接池配置
func initDB() *sql.DB {
    db, _ := sql.Open("postgres", connStr)
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(10)
    db.SetConnMaxLifetime(5 * time.Minute)
    return db
}

// 正确关闭 Rows
rows, err := db.Query(query)
if err != nil {
    return err
}
defer rows.Close()
```