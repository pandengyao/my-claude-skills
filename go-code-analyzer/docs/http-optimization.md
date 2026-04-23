# HTTP 客户端优化指南

## 常见问题

### 1. 未复用 http.Client
```go
// 危险模式 - 每次创建新 Client
func fetch(url string) {
    client := &http.Client{}  // 每次创建
    resp, _ := client.Get(url)
    // ...
}
```

**问题**：无法复用 TCP 连接，性能差。

**优化**：
```go
// 全局复用 Client
var httpClient = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}
```

### 2. 未设置超时
```go
// 危险模式
client := &http.Client{}  // 无超时，可能永久阻塞
```

### 3. 未关闭 Response Body
```go
// 危险模式
resp, _ := http.Get(url)
// 忘记 resp.Body.Close()，连接泄漏
```

### 4. 使用默认 Transport
```go
// 默认配置可能不够
http.DefaultTransport  // MaxIdleConnsPerHost = 2
```

## 搜索关键词

- `http.Client{}`
- `http.Get(`, `http.Post(`
- `&http.Transport{`
- `resp.Body`

## 最佳配置

```go
var client = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        Proxy:                 http.ProxyFromEnvironment,
        DialContext:          (&net.Dialer{
            Timeout:   30 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,
        MaxIdleConns:          100,
        MaxIdleConnsPerHost:   10,
        IdleConnTimeout:       90 * time.Second,
        TLSHandshakeTimeout:   10 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
        ForceAttemptHTTP2:     true,
    },
}
```

## 正确的请求模式

```go
func fetch(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    
    resp, err := httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()  // 必须关闭
    
    return io.ReadAll(resp.Body)
}
```