# 安全漏洞检测指南

## 检测范围

### 1. SQL 注入风险

**检测模式**：
```go
// 危险模式 - 字符串拼接 SQL
query := "SELECT * FROM users WHERE id = " + userInput
db.Query(query)

// 危险模式 - fmt.Sprintf 构建 SQL
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
```

**搜索关键词**：
- `db.Query(` 或 `db.Exec(` 结合字符串拼接
- `fmt.Sprintf` + SQL 关键词
- `"SELECT` 或 `"INSERT` 或 `"UPDATE` 或 `"DELETE` 结合 `+`

**安全建议**：使用参数化查询
```go
db.Query("SELECT * FROM users WHERE id = $1", userInput)
```

### 2. 命令注入风险

**检测模式**：
```go
// 危险模式
cmd := exec.Command("sh", "-c", userInput)
cmd := exec.Command(userInput)
os.system(userInput)
```

**搜索关键词**：
- `exec.Command` 参数包含变量
- `os/exec` 包的使用

**安全建议**：验证和白名单过滤输入

### 3. 路径遍历漏洞

**检测模式**：
```go
// 危险模式
filepath := "/data/" + userInput
os.Open(filepath)
ioutil.ReadFile(userInput)
```

**搜索关键词**：
- `os.Open` / `os.Create` / `ioutil.ReadFile` 参数包含变量
- 文件路径拼接

**安全建议**：使用 `filepath.Clean` 并验证路径前缀

### 4. 不安全的随机数

**检测模式**：
```go
// 危险模式 - 用于安全场景
import "math/rand"
token := rand.Int()
```

**搜索关键词**：
- `math/rand` 用于 token、密钥、session 等安全场景

**安全建议**：安全场景使用 `crypto/rand`

### 5. 硬编码敏感信息

**检测模式**：
```go
// 危险模式
password := "admin123"
apiKey := "sk-xxxxx"
secret := "hardcoded-secret"
```

**搜索关键词**：
- `password`, `passwd`, `pwd` 变量赋值字符串字面量
- `apiKey`, `api_key`, `secret`, `token` 赋值字符串字面量
- 常见密钥前缀如 `sk-`, `ak-`

**安全建议**：使用环境变量或配置文件

### 6. 不安全的 HTTP 配置

**检测模式**：
```go
// 危险模式
http.ListenAndServe(":80", handler)  // 非 HTTPS
&http.Client{Transport: &http.Transport{TLSClientConfig: &tls.Config{InsecureSkipVerify: true}}}
```

**搜索关键词**：
- `InsecureSkipVerify: true`
- `http.ListenAndServe` 非 TLS
- 无超时的 HTTP Client

**安全建议**：启用 TLS，设置合理超时

### 7. 不安全的反序列化

**检测模式**：
```go
// 潜在危险
json.Unmarshal(userInput, &obj)
gob.Decode(userInput)
```

**搜索关键词**：
- 反序列化用户可控输入

## 执行步骤

1. 使用 `search_files` 搜索上述危险模式
2. 使用 `extract_content_blocks` 读取匹配文件的上下文
3. 分析数据流，确认是否存在真实风险
4. 生成报告，按严重程度排序