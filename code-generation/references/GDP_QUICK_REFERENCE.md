# GDP 框架快速参考

百度 Go Development Platform (GDP) - 企业级 Go 开发框架

## 框架概述

GDP 是百度内部的 Go 开发框架,具备:
- ✅ 完善的基础设施支持 (BNS、SSM、DataHub)
- ✅ 强大的 RPC Client/Server 能力
- ✅ 丰富的服务治理功能
- ✅ AI 能力集成 (GDP3)
- ✅ 易测试、易扩展、易配置

## 核心模块速查

### 基础设施 (Foundation)

**环境管理** (`gdp/env`)
```go
import "baidu/gdp/env"

// 初始化应用环境
env.Init("myapp")

// 获取环境信息
appName := env.AppName()      // 应用名称
idc := env.IDC()              // 当前机房
runMode := env.RunMode()      // 运行模式
confDir := env.ConfDir()      // 配置目录
```

**配置解析** (`gdp/conf`)
```go
import "baidu/gdp/conf"

// 解析配置文件 (支持 .toml、.json、.yml)
var config AppConfig
err := conf.Parse("app.toml", &config)

// 读取环境变量
// 配置文件中: db_host = "${DB_HOST}"
// 会自动读取环境变量 DB_HOST 的值
```

**结构化日志** (`gdp/logit`)
```go
import "baidu/gdp/logit"

// 初始化日志
logit.Init()
defer logit.Close()

// 记录日志
logit.Info("用户登录", logit.KV("user_id", 123), logit.KV("ip", "1.2.3.4"))
logit.Error("数据库连接失败", logit.KV("error", err))

// 支持格式: KV 文本、JSON、b2log
```

**指标采集** (`gdp/metrics/gmetrics`)
```go
import "baidu/gdp/metrics/gmetrics"

// 记录请求
gmetrics.EmitCounter("request_count", 1, "api", "/users")
gmetrics.EmitTimer("request_duration", duration, "api", "/users")

// 记录成功/失败
gmetrics.EmitStore("api_success", 1)
gmetrics.EmitStore("api_failed", 1)
```

**链路追踪** (`gdp/metrics/gtrace`)
```go
import "baidu/gdp/metrics/gtrace"

// 创建 span
ctx, span := gtrace.StartSpan(ctx, "operation_name")
defer span.End()

// 添加属性
span.SetAttribute("user_id", 123)

// 记录事件
span.AddEvent("缓存命中")
```

---

### RPC 能力

**HTTP Server** (`gdp/ghttp`)
```go
import "baidu/gdp/ghttp"

func main() {
    // 创建 server
    server := ghttp.NewServer(
        ghttp.WithAddr(":8080"),
    )
    
    // 注册路由
    server.GET("/api/users/:id", GetUser)
    server.POST("/api/users", CreateUser)
    
    // 路由分组
    v1 := server.Group("/api/v1")
    {
        v1.GET("/users/:id", GetUser)
        v1.POST("/users", CreateUser)
    }
    
    // 中间件
    server.Use(LoggerMiddleware())
    server.Use(RecoverMiddleware())
    
    // 启动
    server.Run()
}

func GetUser(c *ghttp.Context) {
    userID := c.Param("id")
    
    // 响应 JSON
    c.JSON(200, ghttp.H{
        "success": true,
        "data": user,
    })
}
```

**RAL Client** (`gdp/ral`)
```go
import "baidu/gdp/ral"

// HTTP 请求
client := ral.NewHTTPClient("service_name")

req := ral.NewHTTPRequest()
req.SetURI("/api/data")
req.SetMethod("GET")
req.SetQueryParam("id", "123")

resp := ral.NewHTTPResponse()

err := client.Do(ctx, req, resp)
if err != nil {
    return err
}

// 解析响应
var data ResponseData
err = json.Unmarshal(resp.Body(), &data)
```

**MySQL Client** (`gdp/mysql`)
```go
import "baidu/gdp/mysql"

// 初始化
db := mysql.NewMySQL("db_service_name")

// 使用 GORM
var user User
err := db.WithContext(ctx).
    Where("id = ?", userID).
    First(&user).Error
if err != nil {
    return err
}

// 事务
err = db.Transaction(func(tx *gorm.DB) error {
    // 在事务中执行操作
    return nil
})
```

**Redis Client** (`gdp/redis`)
```go
import "baidu/gdp/redis"

// 初始化
client := redis.NewRedis("redis_service_name")

// 基本操作
err := client.Set(ctx, "key", "value", 0).Err()
val, err := client.Get(ctx, "key").Result()

// 哈希
client.HSet(ctx, "hash_key", "field", "value")
client.HGet(ctx, "hash_key", "field")

// 列表
client.LPush(ctx, "list_key", "value")
client.RPop(ctx, "list_key")
```

**NSHead Server** (`gdp/nshead`)
```go
import "baidu/gdp/nshead"

// 创建 NSHead server
server := nshead.NewNSHeadServer(
    nshead.WithAddr(":8081"),
)

// 注册处理器
server.RegisterHandler(handler)

// 启动
server.Run()
```

**PBRPC** (`gdp/pbrpc`)
```go
import "baidu/gdp/pbrpc"

// PBRPC Server
server := pbrpc.NewPBRPCServer(
    pbrpc.WithAddr(":8082"),
)

// 注册服务
pb.RegisterUserServiceServer(server, &userServiceImpl{})

// 启动
server.Run()
```

---

### 服务治理

**服务发现** (`gdp/net/discoverer`)
```go
import "baidu/gdp/net/discoverer"

// BNS 服务发现
disc := discoverer.NewBNS("group.bns-name")

// 手动配置
disc := discoverer.NewManual([]string{"127.0.0.1:8080", "127.0.0.1:8081"})

// DNS
disc := discoverer.NewDNS("example.com:8080")

// Mesh (Proxyless Servicemesh)
disc := discoverer.NewMesh("service_name")
```

**负载均衡** (`gdp/net/addressPicker`)
```go
// 支持的策略:
// - RoundRobin (默认)
// - Random
// - LocalityAware
// - ConsistentHash
// - LocalityAwarePlus
// - LeastConnection

picker := addressPicker.NewRoundRobin()
```

**连接池** (`gdp/net/connpool`)
```go
import "baidu/gdp/net/connpool"

pool := connpool.NewConnPool(
    connpool.WithMaxIdle(10),
    connpool.WithMaxActive(100),
)
```

**限流器** (`gdp/extension/limit`)
```go
import "baidu/gdp/extension/limit"

// 令牌桶限流 (限制 QPS)
limiter := limit.NewLimiter(100) // 每秒 100 个令牌
if limiter.Allow() {
    // 处理请求
}

// 并发度限制
concLimiter := limit.NewConcurrentLimiter(50) // 最多 50 并发
if concLimiter.Acquire() {
    defer concLimiter.Release()
    // 处理请求
}

// 对冲请求限流
hedgingLimiter := limit.NewHedgingLimiter(10) // 最多 10% 对冲
```

---

### AI 能力 (GDP3)

**LLM 交互** (`gdp/aic`)
```go
import "baidu/gdp/aic"

// 创建 LLM
llm := aic.NewWenxin(
    aic.WithModel("ERNIE-4.0-8K"),
)

// 创建 Runtime
runtime := aic.NewRuntime(llm)

// 调用
resp, err := runtime.Call(ctx, "你好,请介绍一下 GDP 框架")
if err != nil {
    return err
}

fmt.Println(resp.Content)
```

**Prompt 模板** (`gdp/aic`)
```go
// 定义模板
template := aic.NewPromptTemplate(
    "根据以下信息生成用户画像:\n姓名: {{.Name}}\n年龄: {{.Age}}",
)

// 填充变量
prompt, err := template.Format(map[string]interface{}{
    "Name": "张三",
    "Age":  25,
})
```

**Embedding** (`gdp/aic`)
```go
// 创建 Embedding
embedding := aic.NewWenxinEmbedding()

// 生成向量
vectors, err := embedding.Embed(ctx, []string{"文本1", "文本2"})
if err != nil {
    return err
}
```

**向量存储** (`gdp/aie/vectorstore`)
```go
import "baidu/gdp/aie/vectorstore"

// 使用 Milvus
store := vectorstore.NewMilvus(
    vectorstore.WithCollectionName("my_collection"),
)

// 存储向量
err := store.Add(ctx, documents, vectors)

// 相似度搜索
results, err := store.Search(ctx, queryVector, topK)
```

**RAG** (`gdp/aie/rag`)
```go
import "baidu/gdp/aie/rag"

// 创建 RAG
ragEngine := rag.New(
    rag.WithLLM(llm),
    rag.WithVectorStore(store),
    rag.WithEmbedding(embedding),
)

// 查询
answer, err := ragEngine.Query(ctx, "GDP 框架有哪些核心特性?")
```

**Chain** (`gdp/aichain`)
```go
import "baidu/gdp/aichain"

// LLM Chain
chain := aichain.NewLLMChain(runtime)
result, err := chain.Run(ctx, prompt)

// LLM Math (计算器)
mathChain := aichain.NewLLMMath(runtime)
result, err := mathChain.Run(ctx, "计算 25 * 36 + 18")

// LLM Router (意图识别)
router := aichain.NewLLMRouter(runtime, routes)
result, err := router.Run(ctx, userInput)
```

**Agent** (`gdp/aiagent`)
```go
import "baidu/gdp/aiagent"

// ReAct Agent
agent := aiagent.NewReAct(
    aiagent.WithRuntime(runtime),
    aiagent.WithTools(tools),
)

result, err := agent.Run(ctx, "帮我查询今天的天气并发送邮件通知")
```

---

## 项目结构

### 标准 GDP 项目
```
myapp/
├── main.go              # 主入口
├── go.mod               # 依赖管理
├── conf/                # 配置文件
│   ├── app.toml
│   └── ral.toml
├── handler/             # 处理器层
│   └── user.go
├── service/             # 服务层
│   └── user.go
├── repository/          # 数据层
│   └── user.go
├── model/               # 数据模型
│   └── user.go
├── middleware/          # 中间件
│   └── auth.go
├── tests/               # 测试
│   └── user_test.go
└── testdata/            # 测试数据
    └── sample.json
```

---

## 配置示例

### app.toml
```toml
[app]
name = "myapp"
port = 8080
debug = false

[database]
host = "${DB_HOST}"          # 读取环境变量
port = 3306
name = "mydb"
user = "root"
password = "${DB_PASSWORD}"  # 读取环境变量

[redis]
addr = "127.0.0.1:6379"
db = 0

[log]
level = "info"
format = "json"
output = "stdout"
```

### ral.toml
```toml
[[service]]
name = "user_service"
protocol = "http"
server = "group.user-service.bns"
timeout = 1000
retry = 2

[[service]]
name = "order_service"
protocol = "nshead"
server = "group.order-service.bns"
timeout = 2000
```

---

## 完整示例

### HTTP API Server
```go
package main

import (
    "context"
    "fmt"
    
    "baidu/gdp/env"
    "baidu/gdp/conf"
    "baidu/gdp/ghttp"
    "baidu/gdp/logit"
    "baidu/gdp/mysql"
    "baidu/gdp/redis"
)

type AppConfig struct {
    Port  int
    Debug bool
}

func main() {
    // 初始化环境
    env.Init("myapp")
    
    // 初始化日志
    logit.Init()
    defer logit.Close()
    
    // 解析配置
    var cfg AppConfig
    conf.Parse("app.toml", &cfg)
    
    // 初始化数据库
    db := mysql.NewMySQL("mydb")
    
    // 初始化 Redis
    rdb := redis.NewRedis("myredis")
    
    // 创建 HTTP Server
    server := ghttp.NewServer(
        ghttp.WithAddr(fmt.Sprintf(":%d", cfg.Port)),
    )
    
    // 注册中间件
    server.Use(LoggerMiddleware())
    server.Use(RecoverMiddleware())
    
    // 注册路由
    RegisterRoutes(server, db, rdb)
    
    // 启动服务
    logit.Info("服务启动", logit.KV("port", cfg.Port))
    server.Run()
}

func RegisterRoutes(server *ghttp.Server, db *gorm.DB, rdb *redis.Client) {
    v1 := server.Group("/api/v1")
    {
        // 用户相关
        users := v1.Group("/users")
        {
            users.GET("/:id", GetUser(db))
            users.POST("", CreateUser(db))
            users.PUT("/:id", UpdateUser(db))
            users.DELETE("/:id", DeleteUser(db))
        }
        
        // 其他资源...
    }
}

func GetUser(db *gorm.DB) ghttp.HandlerFunc {
    return func(c *ghttp.Context) {
        ctx := c.Request.Context()
        userID := c.Param("id")
        
        var user User
        err := db.WithContext(ctx).
            Where("id = ?", userID).
            First(&user).Error
        if err != nil {
            logit.Error("查询用户失败", 
                logit.KV("user_id", userID),
                logit.KV("error", err),
            )
            c.JSON(500, ghttp.H{
                "success": false,
                "error": "查询用户失败",
            })
            return
        }
        
        c.JSON(200, ghttp.H{
            "success": true,
            "data": user,
        })
    }
}

func LoggerMiddleware() ghttp.HandlerFunc {
    return func(c *ghttp.Context) {
        start := time.Now()
        
        c.Next()
        
        duration := time.Since(start)
        logit.Info("请求处理完成",
            logit.KV("method", c.Request.Method),
            logit.KV("path", c.Request.URL.Path),
            logit.KV("status", c.Writer.Status()),
            logit.KV("duration", duration.Milliseconds()),
        )
    }
}

func RecoverMiddleware() ghttp.HandlerFunc {
    return func(c *ghttp.Context) {
        defer func() {
            if err := recover(); err != nil {
                logit.Error("panic 恢复", logit.KV("error", err))
                c.JSON(500, ghttp.H{
                    "success": false,
                    "error": "内部服务器错误",
                })
            }
        }()
        c.Next()
    }
}
```

---

## 最佳实践

### 1. 分层架构
```
Handler  → Service  → Repository
(HTTP层)   (业务层)    (数据层)
```

### 2. 错误处理
```go
// 统一错误包装
func GetUser(ctx context.Context, id string) (*User, error) {
    user, err := repository.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("查找用户失败: %w", err)
    }
    return user, nil
}
```

### 3. Context 传递
```go
// Context 总是第一个参数
func ProcessData(ctx context.Context, data string) error {
    // 使用 context 进行超时控制、取消等
}
```

### 4. 并发安全
```go
// 正确的循环闭包
for _, item := range items {
    item := item  // 创建新变量
    go func() {
        process(item)
    }()
}
```

### 5. 资源清理
```go
func ProcessFile(filename string) error {
    f, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer f.Close()  // 确保文件关闭
    
    // 处理文件
    return nil
}
```

### 6. 日志规范
```go
// 使用结构化日志
logit.Info("用户登录",
    logit.KV("user_id", userID),
    logit.KV("ip", clientIP),
    logit.KV("device", device),
)

// 错误日志包含足够上下文
logit.Error("数据库操作失败",
    logit.KV("operation", "insert"),
    logit.KV("table", "users"),
    logit.KV("error", err),
)
```

### 7. 指标监控
```go
// 记录关键指标
start := time.Now()
err := doSomething()
duration := time.Since(start)

if err != nil {
    gmetrics.EmitCounter("operation_failed", 1, "op", "do_something")
} else {
    gmetrics.EmitCounter("operation_success", 1, "op", "do_something")
}
gmetrics.EmitTimer("operation_duration", duration, "op", "do_something")
```

---

## 测试

### 单元测试
```go
func TestGetUser(t *testing.T) {
    // 准备测试数据
    user := &User{ID: 1, Name: "张三"}
    
    // Mock repository
    mockRepo := &MockRepository{
        users: map[int64]*User{1: user},
    }
    
    // 测试
    result, err := service.GetUser(context.Background(), 1)
    assert.NoError(t, err)
    assert.Equal(t, user.Name, result.Name)
}
```

### 集成测试
```bash
# 使用 -race 检测竞态条件
go test -race ./...

# 指定测试
go test -race -run TestGetUser ./service
```

---

## 常用命令

```bash
# 初始化项目
gdp init myapp

# 生成代码
gdp gen proto user.proto

# 热编译运行
gdp run

# 请求抓包
gdp proxy

# 依赖升级
gdp upgrade

# 构建
go build -o myapp main.go

# 测试
go test -race ./...
```

---

## 相关资源

- GDP 文档: https://gdp.baidu-int.com/
- 问题反馈: https://gdp.baidu-int.com/issue
- Q&A: https://gdp.baidu-int.com/qa
- 如流用户群: 1612141

---

**注意**: GDP 框架为百度内部框架,需要在百度内网环境中使用。
