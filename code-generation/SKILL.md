---
name: code-generation
description: 通过结构化工作流生成高质量、生产就绪的代码 - 需求澄清、技术设计、迭代确认、测试和交付。适用于代码开发、功能实现、算法解决方案或系统设计需求。支持 Web 应用、API、数据处理和算法实现,覆盖常见技术栈包括百度 GDP 框架。
---

# 代码生成技能

一个系统化的代码生成方法,通过结构化工作流确保清晰的需求、稳固的架构和经过验证的实现,生成高质量、生产就绪的代码。

## 何时使用本技能

当用户请求以下内容时触发本技能:
- "构建/创建/开发 [功能/组件/系统]"
- "为 [需求] 创建代码"
- "实现 [算法/数据结构]"
- "开发 [应用/服务]"
- 任何受益于结构化规划的代码生成任务

## 核心工作流

```
需求澄清 → 技术设计 → 确认 → 实现 → 测试 → 交付
```

每个阶段都有具体的目标和输出,为下一阶段提供输入。

---

## 阶段 1: 需求澄清

**目标**: 在编写任何代码之前,提取完整、明确的需求。

### 关键问题框架

根据项目类型系统地提问:

#### 1. 核心功能
- **功能**: 主要目的和预期行为是什么?
- **输入**: 接受什么数据/参数? (类型、格式、约束)
- **输出**: 应该返回/产生什么? (格式、结构、交付方式)
- **范围**: 包含什么 vs 明确排除什么?

#### 2. 技术上下文
- **技术栈**: 需要/首选哪些语言、框架、库?
  - 前端: React、Vue、Angular、原生 JS?
  - 后端: Node.js、Python (Flask/Django)、Java (Spring)、Go (GDP 框架)?
  - 数据库: SQL (PostgreSQL、MySQL)、NoSQL (MongoDB、Redis)?
  - 其他: 测试框架、构建工具、部署目标?
- **环境**: 在哪里运行? (浏览器、Node.js、无服务器、容器等)
- **依赖**: 需要的包或外部服务?
- **版本要求**: 特定版本约束?

#### 3. 约束和要求
- **性能**: 响应时间、吞吐量、可扩展性需求?
- **安全**: 认证、授权、数据验证、加密?
- **错误处理**: 如何管理和报告错误?
- **数据验证**: 输入验证规则、清理需求?
- **兼容性**: 浏览器支持、向后兼容、API 版本控制?

#### 4. 非功能性要求
- **代码风格**: 特定约定、lint 规则、格式标准?
- **文档**: 内联注释、README、API 文档、JSDoc/docstrings?
- **测试**: 单元测试、集成测试、测试覆盖期望?
- **日志**: 需要什么级别的日志/监控?
- **部署**: 如何部署和配置?

#### 5. 上下文和集成
- **现有代码库**: 是否与现有代码集成? (如有,提供示例)
- **API/服务**: 需要哪些外部集成?
- **数据模型**: 要匹配的现有架构或数据结构?
- **业务逻辑**: 任何领域特定的规则或工作流?

### 澄清策略

**应该做的**:
- 对模糊需求提出开放式问题
- 当有合理替代方案时提供多项选择
- 如果用户不确定,建议最佳实践
- 尽早澄清边缘情况(空输入、空值、错误状态)
- 在继续之前明确确认假设

**不应该做的**:
- 如果需求从上下文中清晰,不要问每个问题
- 如果用户似乎不懂技术,不要用技术术语压倒他们
- 不要在未说明的情况下进行重大假设
- 不要跳过关键未知事项的澄清

### 输出: 需求文档

以结构化格式总结收集的需求:

```markdown
## 需求总结

**目的**: [一句话描述]

**核心功能**:
- [关键功能 1]
- [关键功能 2]

**输入**: 
- [带类型的输入规范]

**输出**: 
- [带格式的输出规范]

**技术栈**:
- 语言: [X]
- 框架: [Y]
- 关键依赖: [Z]

**约束**:
- [性能/安全/兼容性要求]

**需要处理的边缘情况**:
- [识别的边缘情况]
```

**确认检查点**: 提交此总结并要求用户在继续设计之前确认。

---

## 阶段 2: 技术设计

**目标**: 在编写代码之前创建清晰、架构良好的解决方案。

### 设计原则

遵循这些适应项目规模的原则:

#### 1. SOLID 原则 (对于 OOP)
- **单一职责**: 每个模块/类都有一个明确的目的
- **开闭原则**: 可扩展而无需修改
- **里氏替换**: 子类型可替换
- **接口隔离**: 特定接口优于通用接口
- **依赖倒置**: 依赖抽象,而非具体实现

#### 2. 通用设计原则
- **DRY** (不要重复自己): 提取可重用逻辑
- **KISS** (保持简单): 能工作的最简单解决方案
- **YAGNI** (你不会需要它): 不要过度设计
- **关注点分离**: 层之间的清晰边界
- **组合优于继承**: 倾向于灵活的组合

#### 3. 代码质量标准
- **可读性**: 具有有意义名称的自文档化代码
- **模块化**: 小型、专注的函数/模块
- **可测试性**: 为易于测试而设计
- **可维护性**: 易于理解和修改
- **防御性编程**: 验证输入,优雅地处理错误

### 架构设计

根据项目类型创建适当的架构:

#### Web 应用

```
前端架构:
├── 组件
│   ├── 展示型 (仅 UI)
│   └── 容器型 (逻辑 + 数据)
├── 状态管理
│   ├── 本地状态
│   ├── 全局状态 (Context/Redux/Zustand)
│   └── 服务器状态 (React Query/SWR)
├── 路由
├── API 层
└── 工具/辅助函数

后端架构:
├── 路由/控制器 (HTTP 层)
├── 服务 (业务逻辑)
├── 数据访问层 (数据库/ORM)
├── 中间件 (认证、验证、日志)
├── 模型/模式
└── 工具/辅助函数
```

#### API/微服务

```
API 结构:
├── API 网关/路由器
├── 控制器 (请求处理)
├── 服务 (业务逻辑)
├── 仓储 (数据访问)
├── 模型/DTO (数据传输对象)
├── 中间件
│   ├── 认证
│   ├── 验证
│   ├── 限流
│   └── 错误处理
└── 工具/辅助函数
```

#### 数据处理脚本

```
脚本结构:
├── 主入口点
├── 数据摄取
│   ├── 读取器 (CSV、JSON、API、DB)
│   └── 验证器
├── 处理管道
│   ├── 转换器
│   ├── 过滤器
│   └── 聚合器
├── 输出层
│   ├── 写入器 (文件、DB、API)
│   └── 格式化器
└── 错误处理和日志
```

#### 算法/数据结构

```
算法结构:
├── 核心算法实现
├── 辅助函数
├── 输入验证
├── 边缘情况处理
├── 复杂度分析 (文档化)
└── 使用示例
```

### 技术栈最佳实践

根据识别的技术栈提供具体指导:

#### JavaScript/TypeScript
- 使用 TypeScript 在大型项目中确保类型安全
- 对异步操作使用 async/await
- 使用 ES6+ 特性 (解构、展开、箭头函数)
- 在 React 中实现适当的错误边界
- 适当时使用函数式编程模式

#### Python
- 遵循 PEP 8 风格指南
- 为函数签名使用类型提示 (Python 3.5+)
- 利用列表推导和生成器
- 为资源管理使用上下文管理器 (with 语句)
- 选择适当的数据结构 (dict vs list vs set)

#### Node.js 后端
- 使用 Express.js 中间件模式
- 实现异步错误处理
- 使用环境变量进行配置
- 对大数据处理利用流
- 为数据库实现适当的连接池

#### React
- 使用带 hooks 的函数组件
- 保持组件小而专注
- 在需要时提升状态
- 使用自定义 hooks 提取可重用逻辑
- 在列表中实现适当的 key props
- 在需要时使用 useMemo、useCallback、React.memo 进行优化

#### Go 语言 (百度 GDP 框架)

**命名规范** (强制 - 必须遵守):
- 变量、常量、函数使用驼峰命名法
- 缩写词全大写: `HTTP`、`ID`、`URL`、`JSON`、`API`、`SQL`、`DB` 等
  - 正确: `ServeHTTP`、`UserID`、`ParseJSON`
  - 错误: `ServeHttp`、`UserId`、`ParseJson`
- Error 变量添加 `err` 或 `Err` 前缀
  - 导出: `ErrNotFound`、`ErrTimeout`
  - 非导出: `errInternal`、`errInvalidInput`
- Receiver 使用简短名称 (不用 `self`、`this`)
  - 正确: `func (u *User) Name() string`
  - 错误: `func (this *User) Name() string`
- 包名简短、小写、无下划线
  - 正确: `http`、`strconv`
  - 错误: `httpClient`、`string_converter`

**语言规则** (强制):
- Bool 判断不与 `true`/`false` 比较
  - 正确: `if !ok { }`
  - 错误: `if ok == false { }`
- 删除多余的 `else`
  ```go
  // 正确
  func check(id int) error {
      if id > 0 {
          return nil
      }
      return errors.New("invalid")
  }
  ```
- 错误处理:
  - Error 总是最后一个返回值
  - 所有错误必须处理
  - 使用 `fmt.Errorf` 和 `%w` 包装错误
    ```go
    return fmt.Errorf("连接失败: %w", err)
    ```
- Context 总是第一个参数
  ```go
  func Process(ctx context.Context, data string) error
  ```
- **禁止在循环中使用 defer** (会导致内存泄漏)
  ```go
  // 错误
  for _, file := range files {
      f, _ := os.Open(file)
      defer f.Close() // 错误!
  }
  
  // 正确
  for _, file := range files {
      func() {
          f, _ := os.Open(file)
          defer f.Close() // 正确
      }()
  }
  ```
- Struct 字面量必须指定字段名
  ```go
  user := User{ID: 1, Name: "Alice"} // 正确
  ```

**GDP 框架核心模块**:

1. **基础设施 (Foundation)**
   - `gdp/env`: 应用环境信息 (AppName、IDC、RunMode、配置目录等)
   - `gdp/conf`: 配置文件解析 (支持 .toml、.json、.yml)
   - `gdp/logit`: 结构化日志库 (支持 KV 文本、JSON、b2log)
   - `gdp/metrics/gmetrics`: 标准化指标采集
   - `gdp/metrics/gtrace`: 链路追踪 (OTEL 方案)

2. **RPC 能力**
   - `gdp/ral`: 多协议 RPC Client (HTTP、NSHead、PBRPC)
   - `gdp/servicer`: 下游服务抽象和管理
   - `gdp/ghttp`: HTTP Client 和 Server
   - `gdp/nshead`: NSHead 协议 Client 和 Server
   - `gdp/pbrpc`: ProtoBuf RPC Client 和 Server
   - `gdp/mysql`: MySQL Client (适配 GORM)
   - `gdp/redis`: Redis Client

3. **服务治理**
   - `gdp/net/discoverer`: 服务发现 (BNS、Manual、DNS、Mesh)
   - `gdp/net/addressPicker`: 负载均衡策略
   - `gdp/net/connpool`: 连接池
   - `gdp/extension/limit`: 限流器 (令牌桶、并发度限制等)

4. **AI 能力** (GDP3 新增)
   - `gdp/aic`: 大模型交互核心 (LLM、Prompt、Embedding、Memory)
   - `gdp/aichain`: 基于大模型的 Chain (LLMChain、LLMMath等)
   - `gdp/aiagent`: 智能体实现 (ReAct)
   - `gdp/milvus`: 向量数据库 SDK
   - `gdp/aie/vectorstore`: 抽象向量存储 (BES、Milvus)
   - `gdp/aie/rag`: RAG (检索增强生成)

**GDP 项目结构**:
```
myapp/
├── main.go              # 主入口
├── go.mod               # 依赖管理
├── conf/                # 配置文件目录
│   └── app.toml
├── handler/             # HTTP/RPC 处理器层
│   └── user.go
├── service/             # 业务逻辑层
│   └── user.go
├── repository/          # 数据访问层
│   └── user.go
├── model/               # 数据模型
│   └── user.go
└── tests/               # 测试
    └── user_test.go
```

**GDP HTTP Server 示例**:
```go
package main

import (
    "context"
    
    "baidu/gdp/env"
    "baidu/gdp/ghttp"
    "baidu/gdp/logit"
)

func main() {
    // 初始化环境
    env.Init("myapp")
    
    // 初始化日志
    logit.Init()
    defer logit.Close()
    
    // 创建 HTTP Server
    server := ghttp.NewServer(
        ghttp.WithAddr(":8080"),
    )
    
    // 注册路由
    server.GET("/api/users/:id", GetUser)
    server.POST("/api/users", CreateUser)
    
    // 启动服务
    server.Run()
}

// GetUser 处理获取用户请求
func GetUser(c *ghttp.Context) {
    ctx := c.Request.Context()
    userID := c.Param("id")
    
    // 调用服务层
    user, err := service.GetUser(ctx, userID)
    if err != nil {
        c.JSON(500, ghttp.H{
            "success": false,
            "error": err.Error(),
        })
        return
    }
    
    c.JSON(200, ghttp.H{
        "success": true,
        "data": user,
    })
}
```

**GDP RAL Client 示例**:
```go
package main

import (
    "context"
    
    "baidu/gdp/ral"
)

func callDownstream(ctx context.Context) error {
    // 创建 RAL Client
    client := ral.NewHTTPClient("downstream_service")
    
    req := ral.NewHTTPRequest()
    req.SetURI("/api/data")
    req.SetMethod("GET")
    
    resp := ral.NewHTTPResponse()
    
    // 发起请求
    err := client.Do(ctx, req, resp)
    if err != nil {
        return fmt.Errorf("调用下游失败: %w", err)
    }
    
    // 处理响应
    // ...
    
    return nil
}
```

**错误处理模式**:
```go
func DoSomething(ctx context.Context, id int) (*Result, error) {
    if id <= 0 {
        return nil, fmt.Errorf("无效的 ID: %d", id)
    }
    
    result, err := repository.Find(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("查找失败: %w", err)
    }
    
    return result, nil
}
```

**并发安全**:
```go
// 正确的循环闭包
for _, item := range items {
    item := item  // 创建新变量!
    go func() {
        process(item)
    }()
}

// Worker Pool 模式
func processItems(items []Item) error {
    var wg sync.WaitGroup
    errCh := make(chan error, len(items))
    
    for _, item := range items {
        wg.Add(1)
        go func(i Item) {
            defer wg.Done()
            if err := process(i); err != nil {
                errCh <- err
            }
        }(item)
    }
    
    wg.Wait()
    close(errCh)
    
    for err := range errCh {
        if err != nil {
            return err
        }
    }
    return nil
}
```

**注释规范**:
```go
// MinAge 是注册的最小年龄
const MinAge = 3

// ServeHTTP 处理 HTTP 请求
func ServeHTTP(w http.ResponseWriter, r *http.Request) {}

// User 代表系统用户
type User struct {
    ID   int64
    Name string
}
```

**Import 分组**:
```go
import (
    // 标准库
    "context"
    "fmt"
    
    // 百度 GDP
    "baidu/gdp/ghttp"
    "baidu/gdp/logit"
    
    // 第三方库
    "github.com/go-sql-driver/mysql"
    
    // 项目内部
    "myapp/internal/model"
    "myapp/internal/service"
)
```

**测试规范**:
```bash
# 必须使用 -race 检测竞态条件
go test -race ./...
```

**常用工具**:
- 格式化: `gofmt`、`goimports`
- 检查: `go vet`、`golangci-lint`、`staticcheck`

---

## 阶段 3: 迭代确认

**目标**: 在全面实现之前确保一致性,特别是对于复杂项目。

### 确认策略

根据项目复杂度选择方法:

#### 小型项目 (<100 行)
- 在一个总结中显示完整的需求 + 设计
- 获得一次确认即可继续

#### 中型项目 (100-500 行)
- 首先确认需求
- 展示高级架构
- 可选: 在实现之前分享关键函数签名
- 获得确认继续

#### 大型项目 (>500 行)
- 分解为模块/阶段
- 分别确认每个模块的设计
- 通过检查点增量实现
- 分享进度更新

### 要确认的内容

向用户展示以明确批准:

1. **需求理解**: "根据我们的讨论,这是我的理解..."
2. **技术方法**: "我将使用 [技术栈] 和 [架构] 因为..."
3. **关键权衡**: "这种方法优先考虑 [X] 而非 [Y] 因为..."
4. **实现计划**: "我将在 [N] 个主要组件中构建..."
5. **交付物**: "你将收到 [文件/文档/测试]..."

### 确认模板

```markdown
## 实现计划确认

**我要构建的**: [一句话总结]

**如何构建**:
- 架构: [模式/方法]
- 技术栈: [确认的技术栈]
- 主要组件: [列出 3-5 个关键组件]

**关键决策**:
- [决策 1 + 理由]
- [决策 2 + 理由]

**你将收到什么**:
- [交付文件列表]
- [包含的文档]
- [包含的测试(如适用)]

**估计复杂度**: [简单/中等/复杂]

**准备好继续了吗?** 如果需要任何调整,请告诉我。
```

---

## 阶段 4: 实现

**目标**: 按照确认的设计编写干净、经过测试、生产就绪的代码。

### 实现标准

#### 代码组织

**文件结构**:
- 按功能或层进行逻辑分组
- 清晰的命名约定
- 将配置与逻辑分离
- 提取常量和配置

**命名约定**:
- 函数/方法: 基于动词 (`getUserData`、`calculateTotal`)
- 类: 基于名词,PascalCase (`UserService`、`DataProcessor`)
- 变量: 描述性,camelCase (`userData`、`totalAmount`)
- 常量: UPPER_SNAKE_CASE (`MAX_RETRIES`、`API_BASE_URL`)
- 文件: 匹配主要导出或目的 (`userService.js`、`auth-middleware.js`)

#### 代码质量检查清单

**✓ 可读性**:
- [ ] 有意义的变量和函数名称
- [ ] 一致的代码风格
- [ ] 复杂逻辑的适当注释
- [ ] 清晰的函数签名
- [ ] 合理的函数长度 (<50 行理想)

**✓ 健壮性**:
- [ ] 所有公共接口的输入验证
- [ ] 具有特定错误类型的适当错误处理
- [ ] 边缘情况处理 (null、undefined、空、边界值)
- [ ] 资源清理 (关闭连接、清除计时器)
- [ ] 可能时优雅降级

**✓ 性能**:
- [ ] 高效的算法 (记录复杂度)
- [ ] 避免不必要的计算
- [ ] 适当时使用缓存
- [ ] I/O 的异步操作
- [ ] 内存泄漏预防

**✓ 安全性**:
- [ ] 针对注入攻击的输入清理
- [ ] 日志或错误消息中没有敏感数据
- [ ] 数据库使用参数化查询
- [ ] 适当的认证/授权检查
- [ ] 安全的依赖项 (无已知漏洞)

**✓ 可维护性**:
- [ ] 应用 DRY 原则
- [ ] 单一职责原则
- [ ] 可测试的代码结构
- [ ] 清晰的关注点分离
- [ ] 最小耦合、高内聚

### 文档标准

#### 内联注释

**何时注释**:
- 复杂的算法或业务逻辑
- 非显而易见的解决方案或变通方法
- 重要的假设或约束
- 正则表达式或隐晦的表达式
- 性能优化

**何时不注释**:
- 自解释的代码
- 代码做什么 (让代码说话)
- 冗余信息

**好的注释示例**:
```javascript
// 不好: 增加计数器
counter++;

// 好: 跟踪失败尝试以进行指数退避计算
failedAttempts++;

// 好: 使用 Set 进行 O(1) 查找而不是 Array.includes() 的 O(n)
const uniqueIds = new Set(userIds);
```

```go
// 不好: 循环处理
for _, item := range items {
    process(item)
}

// 好: 使用 goroutine 并发处理以提升性能
for _, item := range items {
    item := item
    go func() {
        process(item)
    }()
}
```

#### 函数/方法文档

为语言使用适当的文档格式:

**JavaScript/TypeScript (JSDoc)**:
```javascript
/**
 * 使用重试逻辑从 API 获取用户数据
 * @param {string} userId - 唯一用户标识符
 * @param {Object} options - 配置选项
 * @param {number} options.maxRetries - 最大重试次数 (默认: 3)
 * @param {number} options.timeout - 请求超时(毫秒) (默认: 5000)
 * @returns {Promise<User>} 用户对象
 * @throws {UserNotFoundError} 当用户不存在时
 * @throws {NetworkError} 当重试后网络请求失败时
 */
async function fetchUserData(userId, options = {}) {
  // 实现
}
```

**Python (Docstrings)**:
```python
def process_data(data: List[Dict], threshold: float = 0.5) -> pd.DataFrame:
    """
    处理原始数据并按置信度阈值过滤。
    
    Args:
        data: 包含原始数据条目的字典列表
        threshold: 包含的最小置信度分数 (0.0 到 1.0)
    
    Returns:
        包含已处理和过滤数据的 DataFrame
    
    Raises:
        ValueError: 如果阈值超出有效范围
        DataProcessingError: 如果数据格式无效
    
    Example:
        >>> raw_data = [{"value": 10, "confidence": 0.8}]
        >>> result = process_data(raw_data, threshold=0.7)
    """
    # 实现
```

**Go**:
```go
// ProcessData 处理原始数据并按阈值过滤
//
// 参数:
//   - data: 原始数据条目列表
//   - threshold: 包含的最小置信度分数 (0.0 到 1.0)
//
// 返回:
//   - *Result: 处理后的结果
//   - error: 处理错误
//
// 示例:
//   result, err := ProcessData(rawData, 0.7)
//   if err != nil {
//       return err
//   }
func ProcessData(data []RawData, threshold float64) (*Result, error) {
    if threshold < 0 || threshold > 1 {
        return nil, errors.New("阈值必须在 0 到 1 之间")
    }
    // 实现
}
```

### 错误处理模式

#### JavaScript/TypeScript

```javascript
// 自定义错误类
class ValidationError extends Error {
  constructor(message, field) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

// Try-Catch 与特定处理
try {
  const result = await riskyOperation();
  return result;
} catch (error) {
  if (error instanceof ValidationError) {
    logger.warn(`验证失败: ${error.message}`, { field: error.field });
    return { success: false, error: error.message };
  } else if (error.code === 'ECONNREFUSED') {
    logger.error('数据库连接失败');
    throw new ServiceUnavailableError('数据库不可用');
  } else {
    logger.error('意外错误:', error);
    throw error;
  }
}
```

#### Python

```python
# 自定义异常
class DataValidationError(Exception):
    """当输入数据验证失败时引发"""
    def __init__(self, message, field=None):
        self.field = field
        super().__init__(message)

# Try-Except 与特定处理
try:
    result = risky_operation()
    return result
except DataValidationError as e:
    logger.warning(f"验证失败: {e}", extra={"field": e.field})
    return {"success": False, "error": str(e)}
except ConnectionError as e:
    logger.error("数据库连接失败")
    raise ServiceUnavailableError("数据库不可用") from e
except Exception as e:
    logger.error(f"意外错误: {e}", exc_info=True)
    raise
finally:
    cleanup()
```

#### Go

```go
// 自定义错误
var (
    ErrNotFound = errors.New("未找到")
    ErrInvalid  = errors.New("无效输入")
)

// 自定义错误类型
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("字段 %s 验证失败: %s", e.Field, e.Message)
}

// 错误处理
func ProcessRequest(ctx context.Context, req *Request) (*Response, error) {
    if req.ID <= 0 {
        return nil, &ValidationError{
            Field:   "id",
            Message: "ID 必须大于 0",
        }
    }
    
    data, err := fetchData(ctx, req.ID)
    if err != nil {
        return nil, fmt.Errorf("获取数据失败: %w", err)
    }
    
    return &Response{Data: data}, nil
}

// 错误检查
if errors.Is(err, ErrNotFound) {
    // 处理未找到
}

var validErr *ValidationError
if errors.As(err, &validErr) {
    fmt.Printf("字段: %s, 消息: %s\n", validErr.Field, validErr.Message)
}
```

---

## 阶段 5: 测试和验证

**目标**: 在交付前验证实现正确工作。

### 测试策略

#### 1. 自测检查清单

在提交代码前验证:

**✓ 语法和编译**:
- [ ] 没有语法错误
- [ ] 代码可以解析/编译
- [ ] 所有导入/依赖正确

**✓ 逻辑正确性**:
- [ ] 主要功能按指定工作
- [ ] 边缘情况得到处理
- [ ] 错误条件产生适当的错误
- [ ] 输入验证捕获无效数据

**✓ 代码质量**:
- [ ] 遵循编码标准
- [ ] 没有明显的 bug 或反模式
- [ ] 使用高效的算法
- [ ] 适当的资源管理

**✓ 文档**:
- [ ] 关键函数有文档
- [ ] 复杂逻辑有注释
- [ ] 包含使用示例
- [ ] README 完整 (如适用)

#### 2. 测试覆盖

确保测试覆盖:

**正常路径**:
- 正常输入产生预期输出
- 标准用例正常工作

**边缘情况**:
- 空输入 ([], {}, "", null, undefined)
- 边界值 (0, -1, MAX_INT, min/max 日期)
- 大数据集 (如适用)
- 字符串中的特殊字符

**错误情况**:
- 无效输入触发适当的错误
- 网络故障得到处理
- 资源耗尽得到管理
- 避免竞态条件

**集成点**:
- 外部 API 调用正常工作
- 数据库操作成功
- 文件 I/O 处理错误
- 认证/授权工作

#### 3. 手动测试建议

向用户提供测试指导:

```markdown
## 测试建议

**测试此代码**:

1. **设置**:
   ```bash
   [安装/设置命令]
   ```

2. **基本测试**:
   ```javascript
   [应该工作的简单使用示例]
   ```
   预期输出: [应该发生什么]

3. **边缘情况测试**:
   ```javascript
   [使用边缘情况输入测试]
   ```
   预期: [应该优雅地处理]

4. **错误测试**:
   ```javascript
   [使用无效输入测试]
   ```
   预期: [应该抛出特定错误]

**常见问题**:
- [潜在问题 1]: [如何解决]
- [潜在问题 2]: [如何解决]
```

---

## 阶段 6: 交付

**目标**: 提供完整、随时可用的代码以及所有必要的文档。

### 交付检查清单

**✓ 代码文件**:
- [ ] 所有实现文件
- [ ] 测试文件 (如适用)
- [ ] 配置文件 (如需要)
- [ ] 构建/部署脚本 (如需要)

**✓ 文档**:
- [ ] 带设置和使用的 README
- [ ] 内联代码文档
- [ ] API 参考 (如适用)
- [ ] 示例和用例

**✓ 依赖**:
- [ ] package.json / requirements.txt / go.mod 等
- [ ] 安装说明
- [ ] 指定版本要求

**✓ 设置说明**:
- [ ] 环境设置步骤
- [ ] 需要的配置
- [ ] 如何运行测试
- [ ] 如何部署 (如适用)

### 交付格式

以清晰的结构呈现代码:

```markdown
## 交付总结

**我构建的内容**: [简要描述]

**包含的文件**:
1. `[文件名]` - [目的]
2. `[文件名]` - [目的]

**实现的关键功能**:
- [功能 1]
- [功能 2]

**如何使用**:
[快速入门说明]

**测试**:
[如何验证其工作]

**后续步骤** (可选):
- [潜在增强]
- [要自定义的区域]
```

### 代码展示

**使用适当的文件创建**:
- 对于单个文件 <100 行: 内联呈现或直接创建文件
- 对于多个文件: 以有组织的结构创建所有文件
- 对于复杂项目: 使用文件树结构,系统地创建

**文件组织示例**:
```
project/
├── src/
│   ├── index.js          # 主入口点
│   ├── services/
│   │   └── userService.js
│   └── utils/
│       └── validation.js
├── tests/
│   └── userService.test.js
├── README.md
└── package.json
```

### 交付后支持

交付后提供:

1. **澄清**: "如果任何部分需要解释,请告诉我"
2. **自定义**: "如果需要,我可以调整 X 或 Y"
3. **扩展**: "你想让我添加 [相关功能] 吗?"
4. **调试**: "如果遇到问题,分享错误,我会帮助调试"

---

## 领域特定模式

### Web 应用开发

**前端 (React) 模式**:
```javascript
// 组件结构
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

/**
 * [组件描述]
 */
const ComponentName = ({ prop1, prop2 }) => {
  // 状态管理
  const [state, setState] = useState(initialValue);

  // 副作用
  useEffect(() => {
    // 副作用
    return () => {
      // 清理
    };
  }, [dependencies]);

  // 事件处理器
  const handleEvent = (event) => {
    // 处理事件
  };

  // 渲染
  return (
    <div>
      {/* JSX */}
    </div>
  );
};

ComponentName.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};

export default ComponentName;
```

**后端 (Express) 模式**:
```javascript
// Route → Controller → Service → Repository 模式

// routes/userRoutes.js
const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');
const { authenticate } = require('../middleware/auth');

router.get('/:id', authenticate, userController.getUser);
router.post('/', userController.createUser);

// controllers/userController.js
const userService = require('../services/userService');

exports.getUser = async (req, res, next) => {
  try {
    const user = await userService.getUserById(req.params.id);
    res.json({ success: true, data: user });
  } catch (error) {
    next(error);
  }
};

// services/userService.js
const userRepository = require('../repositories/userRepository');

exports.getUserById = async (userId) => {
  if (!userId) throw new ValidationError('需要用户 ID');
  
  const user = await userRepository.findById(userId);
  if (!user) throw new NotFoundError('未找到用户');
  
  return user;
};

// repositories/userRepository.js
const db = require('../database');

exports.findById = async (userId) => {
  return db.query('SELECT * FROM users WHERE id = $1', [userId]);
};
```

### API 开发

**RESTful API 模式**:
```javascript
// 清晰的端点结构
const api = {
  // 资源
  users: {
    getAll: 'GET /api/v1/users',
    getById: 'GET /api/v1/users/:id',
    create: 'POST /api/v1/users',
    update: 'PUT /api/v1/users/:id',
    delete: 'DELETE /api/v1/users/:id',
  },
  
  // 响应格式
  successResponse: {
    success: true,
    data: {},
    metadata: {
      timestamp: 'ISO-8601',
      version: 'v1',
    },
  },
  
  errorResponse: {
    success: false,
    error: {
      code: 'ERROR_CODE',
      message: '人类可读的消息',
      details: {},
    },
  },
};

// 中间件栈
app.use(cors());
app.use(helmet());
app.use(express.json());
app.use(requestLogger);
app.use(authenticate);
app.use('/api/v1', apiRoutes);
app.use(errorHandler);
```

**Go (GDP 框架) API 模式**:
```go
package main

import (
    "context"
    
    "baidu/gdp/env"
    "baidu/gdp/ghttp"
    "baidu/gdp/logit"
)

func main() {
    // 初始化环境
    env.Init("myapp")
    logit.Init()
    defer logit.Close()
    
    // 创建 HTTP Server
    server := ghttp.NewServer(
        ghttp.WithAddr(":8080"),
    )
    
    // 注册中间件
    server.Use(LoggerMiddleware())
    server.Use(RecoverMiddleware())
    
    // 注册路由
    v1 := server.Group("/api/v1")
    {
        v1.GET("/users/:id", GetUser)
        v1.POST("/users", CreateUser)
    }
    
    // 启动服务
    server.Run()
}

// GetUser 处理获取用户请求
func GetUser(c *ghttp.Context) {
    ctx := c.Request.Context()
    userID := c.Param("id")
    
    user, err := service.GetUser(ctx, userID)
    if err != nil {
        c.JSON(500, ghttp.H{
            "success": false,
            "error": err.Error(),
        })
        return
    }
    
    c.JSON(200, ghttp.H{
        "success": true,
        "data": user,
    })
}

// service/user.go
func GetUser(ctx context.Context, id string) (*User, error) {
    user, err := repository.FindByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("查找用户失败: %w", err)
    }
    return user, nil
}

// repository/user.go
func FindByID(ctx context.Context, id string) (*User, error) {
    // 使用 GDP MySQL Client
    var user User
    err := db.WithContext(ctx).
        Where("id = ?", id).
        First(&user).Error
    if err != nil {
        return nil, fmt.Errorf("查询失败: %w", err)
    }
    return &user, nil
}
```

### 数据处理

**ETL 管道模式**:
```python
# Extract → Transform → Load 模式

class DataPipeline:
    """用于数据处理的 ETL 管道"""
    
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.logger = setup_logger(__name__)
    
    def extract(self):
        """从源提取数据"""
        self.logger.info(f"从 {self.source} 提取")
        try:
            data = self._read_source()
            self.logger.info(f"提取了 {len(data)} 条记录")
            return data
        except Exception as e:
            self.logger.error(f"提取失败: {e}")
            raise DataExtractionError(f"提取失败: {e}")
    
    def transform(self, data):
        """转换和清理数据"""
        self.logger.info("转换数据")
        try:
            # 验证
            validated = self._validate_data(data)
            # 清理
            cleaned = self._clean_data(validated)
            # 转换
            transformed = self._apply_transformations(cleaned)
            self.logger.info(f"转换了 {len(transformed)} 条记录")
            return transformed
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            raise DataTransformationError(f"转换失败: {e}")
    
    def load(self, data):
        """加载数据到目标"""
        self.logger.info(f"加载到 {self.destination}")
        try:
            result = self._write_destination(data)
            self.logger.info(f"加载了 {result['count']} 条记录")
            return result
        except Exception as e:
            self.logger.error(f"加载失败: {e}")
            raise DataLoadError(f"加载失败: {e}")
    
    def run(self):
        """执行完整管道"""
        try:
            data = self.extract()
            transformed = self.transform(data)
            result = self.load(transformed)
            return {"success": True, "result": result}
        except Exception as e:
            self.logger.error(f"管道失败: {e}")
            return {"success": False, "error": str(e)}
```

### 算法实现

**算法模板**:
```python
def algorithm_name(input_data, **options):
    """
    [算法描述和目的]
    
    时间复杂度: O(n log n)
    空间复杂度: O(n)
    
    Args:
        input_data: [描述]
        **options: 可选参数
            - option1: [描述] (默认: value)
            - option2: [描述] (默认: value)
    
    Returns:
        [返回值描述]
    
    Raises:
        ValueError: [何时发生]
    
    Example:
        >>> algorithm_name([3, 1, 4, 1, 5])
        [1, 1, 3, 4, 5]
    """
    # 输入验证
    if not input_data:
        raise ValueError("输入数据不能为空")
    
    # 初始化变量
    result = []
    
    # 主要算法逻辑
    # [步骤 1: 描述]
    step1_result = perform_step1(input_data)
    
    # [步骤 2: 描述]
    step2_result = perform_step2(step1_result)
    
    # [步骤 3: 描述]
    result = perform_step3(step2_result)
    
    return result
```

**Go 算法模式**:
```go
// AlgorithmName 实现某某算法
//
// 时间复杂度: O(n log n)
// 空间复杂度: O(n)
//
// 参数:
//   - inputData: 输入数据
//   - options: 可选配置
//
// 返回:
//   - result: 处理结果
//   - error: 错误信息
//
// 示例:
//   result, err := AlgorithmName(data, options)
func AlgorithmName(inputData []int, options *Options) ([]int, error) {
    // 输入验证
    if len(inputData) == 0 {
        return nil, errors.New("输入数据不能为空")
    }
    
    // 初始化变量
    result := make([]int, 0, len(inputData))
    
    // 主要算法逻辑
    // 步骤 1: 描述
    step1Result := performStep1(inputData)
    
    // 步骤 2: 描述
    step2Result := performStep2(step1Result)
    
    // 步骤 3: 描述
    result = performStep3(step2Result)
    
    return result, nil
}
```

---

## 常见技术栈指南

### JavaScript/Node.js

**最佳实践**:
- 使用 `async/await` 而非回调
- 优先使用 `const` 而非 `let`,避免 `var`
- 使用模板字符串进行字符串插值
- 利用解构使代码更清晰
- 使用可选链 (`?.`) 和空值合并 (`??`)
- 使用 try-catch 处理 promise 拒绝
- 使用 `Array` 方法 (`map`、`filter`、`reduce`) 而非循环

**常用包**:
- Express.js: Web 框架
- Axios: HTTP 客户端
- Lodash: 实用函数
- Moment/date-fns: 日期操作
- Joi/Yup: 验证
- Winston: 日志
- Jest: 测试

### Python

**最佳实践**:
- 遵循 PEP 8 风格指南
- 使用虚拟环境
- 函数签名的类型提示
- 列表推导提高可读性
- 上下文管理器用于资源处理
- 生成器表达式提高内存效率
- 使用 `pathlib` 而非 `os.path`
- 优先使用标准库

**常用包**:
- Flask/FastAPI: Web 框架
- Requests: HTTP 客户端
- Pandas: 数据操作
- NumPy: 数值计算
- SQLAlchemy: ORM
- Pydantic: 数据验证
- Pytest: 测试

### React

**最佳实践**:
- 使用带 hooks 的函数组件
- 保持组件小而专注
- 需要时提升状态
- 使用自定义 hooks 实现可重用逻辑
- 在列表中实现适当的 key props
- 记忆化昂贵的计算
- 使用 React.lazy 进行代码分割
- 处理加载和错误状态

**常用库**:
- React Router: 导航
- React Query/SWR: 数据获取
- Zustand/Redux: 状态管理
- Axios: API 调用
- React Hook Form: 表单处理
- Tailwind/MUI: 样式

### TypeScript

**最佳实践**:
- 为对象定义接口
- 使用类型联合和交叉
- 避免 `any`,如需要使用 `unknown`
- 利用泛型实现可重用性
- 使用实用类型 (Partial、Pick、Omit)
- 启用严格模式
- 明确声明返回类型

### Go (百度 GDP 框架)

**框架特性**:
- 对厂内基础设施支持完善 (BNS、SSM、DataHub 等)
- 可扩展性好、易配置、易组装
- 对测试友好 (易 mock,多种 testServer、testClient)
- 组件内部状态易观察 (管理面板)
- 全链路超时和流程控制机制
- 厂内大规模应用,稳定可靠

**核心能力汇总**:

1. **基础能力**: 环境管理、配置解析、结构化日志、指标采集、链路追踪
2. **RPC 能力**: 多协议 Client/Server (HTTP、NSHead、PBRPC)、服务发现、负载均衡
3. **数据存储**: MySQL、Redis、BNS、DataHub
4. **服务治理**: 连接池、限流器、熔断器、超时控制
5. **AI 能力**: LLM 交互、向量检索、RAG、智能体
6. **可观测性**: 日志、指标、追踪、管理面板

**推荐使用场景**:
- API 服务开发
- 微服务架构
- 数据处理服务
- AI 应用开发
- 后端系统开发

---

## 错误处理参考

### 常见错误类型

**JavaScript**:
```javascript
// 内置错误
TypeError          // 错误的类型
ReferenceError     // 未定义的变量
SyntaxError        // 无效的语法
RangeError         // 数字超出范围

// 自定义错误
ValidationError    // 无效输入
AuthenticationError // 认证失败
NotFoundError      // 资源未找到
ServiceUnavailableError // 外部服务不可用
TimeoutError       // 操作超时
```

**Python**:
```python
# 内置异常
ValueError         # 无效值
TypeError          # 错误的类型
KeyError           # 缺少键
IndexError         # 索引超出范围
FileNotFoundError  # 文件不存在

# 自定义异常
ValidationError    # 无效输入
AuthenticationError # 认证失败
NotFoundError      # 资源未找到
ServiceUnavailableError # 外部服务不可用
TimeoutError       # 操作超时
```

**Go**:
```go
// 标准库错误
import (
    "errors"
    "fmt"
    "io"
    "os"
)

// 常见标准错误
io.EOF                // 文件结束
os.ErrNotExist       // 文件不存在
os.ErrPermission     // 权限被拒绝
context.Canceled     // 上下文被取消
context.DeadlineExceeded // 上下文超时

// 自定义错误
var (
    ErrValidation    = errors.New("验证失败")
    ErrNotFound      = errors.New("资源未找到")
    ErrUnauthorized  = errors.New("未授权")
    ErrInternal      = errors.New("内部服务器错误")
)

// 错误包装 (Go 1.13+)
func ProcessData(id int) error {
    data, err := fetchData(id)
    if err != nil {
        return fmt.Errorf("获取数据失败: %w", err)
    }
    return nil
}

// 带字段的自定义错误
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("字段 %s 验证失败: %s", e.Field, e.Message)
}

// 使用 errors.Is 和 errors.As 检查错误
func HandleError(err error) {
    if errors.Is(err, os.ErrNotExist) {
        // 处理不存在错误
    }
    
    var validationErr *ValidationError
    if errors.As(err, &validationErr) {
        // 处理验证错误
        fmt.Printf("字段: %s, 消息: %s\n", validationErr.Field, validationErr.Message)
    }
}
```

### 错误响应格式

**API 错误响应**:
```javascript
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "邮箱格式无效",
    "details": {
      "field": "email",
      "value": "invalid-email",
      "constraint": "必须是有效的邮箱地址"
    },
    "timestamp": "2026-02-10T10:30:00Z",
    "requestId": "req_12345"
  }
}
```

---

## 工作流执行指南

### 简单请求
1. 简要澄清 (如需要 1-2 个问题)
2. 用 2-3 句话确认方法
3. 直接实现
4. 提供使用示例

### 中等请求
1. 澄清需求 (3-5 个问题)
2. 提交设计摘要
3. 获得确认
4. 实现并测试
5. 交付并提供文档

### 复杂请求
1. 深入需求收集
2. 详细技术设计
3. 逐模块确认
4. 迭代实现
5. 全面测试
6. 完整文档包

### 灵活性原则

**适应用户风格**:
- 如果用户懂技术: 使用适当的术语,更深入的架构
- 如果用户不懂技术: 解释概念,使用更简单的语言
- 如果用户赶时间: 跳过确认,快速交付
- 如果用户要求彻底: 完整工作流和所有检查点

**根据项目规模扩展**:
- 快速脚本: 最小流程,快速交付
- 生产系统: 完整工作流,全面测试
- 原型: 专注功能,减少优化
- 企业级: 强调安全性、可扩展性、文档

**听取反馈**:
- 用户想要更少流程: 简化,减少确认
- 用户想要更多细节: 扩展文档,更多示例
- 用户不同意方法: 讨论替代方案,调整
- 用户发现 bug: 快速调试,解释修复

---

## 质量门槛

交付代码前,确保通过这些门槛:

**门槛 1: 满足需求**
- ✓ 所有指定功能已实现
- ✓ 输入/输出格式匹配需求
- ✓ 边缘情况已处理

**门槛 2: 代码质量**
- ✓ 遵循语言最佳实践
- ✓ 干净、可读、可维护
- ✓ 适当的错误处理
- ✓ 没有明显的 bug 或反模式

**门槛 3: 文档**
- ✓ 关键函数已文档化
- ✓ 提供使用示例
- ✓ 设置说明清晰
- ✓ 复杂逻辑已解释

**门槛 4: 测试**
- ✓ 主要功能已验证
- ✓ 边缘情况已处理
- ✓ 错误情况产生适当的错误
- ✓ 包含测试 (如范围需要)

**门槛 5: 交付物**
- ✓ 所有文件已创建
- ✓ 依赖已指定
- ✓ 随时可用
- ✓ 后续步骤清晰

---

## 反模式避免

**❌ 不要**:
- 在未询问的情况下假设需求
- 过度设计简单请求
- 交付没有解释的代码
- 跳过错误处理
- 忽略边缘情况
- 编写代码而不进行思维测试
- 使用过时的模式或语法
- 创建上帝函数 (>100 行)
- 硬编码配置值
- 默默吞下错误

**✓ 要**:
- 提出澄清问题
- 将复杂性扩展到需求
- 解释关键决策
- 优雅地处理错误
- 考虑边缘情况
- 走查逻辑路径
- 使用现代、惯用的代码
- 保持函数专注
- 外部化配置
- 快速失败并显示清晰错误

---

## 成功标准

成功的代码生成会话产生:

1. **清晰理解**: 用户和 Claude 对需求达成一致
2. **稳固设计**: 架构良好、可维护的解决方案
3. **质量代码**: 干净、经过测试、生产就绪的实现
4. **完整交付**: 提供所有文件、文档和说明
5. **用户信心**: 用户理解并可以使用/修改代码
6. **可扩展性**: 代码可以轻松增强或调整

---

## 结论

本技能通过以下方式提供生成高质量代码的系统化框架:
- 彻底的需求澄清
- 稳健的技术设计
- 迭代确认
- 质量实现
- 适当的测试
- 完整交付

根据项目复杂性和用户需求调整工作流,同时保持核心原则:**先理解后构建,先设计后编码,先验证后交付**。

对于百度 Go 项目,优先使用 GDP 框架,它提供了完善的基础设施支持、丰富的 RPC 能力和强大的 AI 功能,可以显著提升开发效率。
