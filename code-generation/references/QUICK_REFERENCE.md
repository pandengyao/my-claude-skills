# Code Generation Skill - Quick Reference

## 快速启动

### 触发技能
当用户说以下内容时自动触发:
- "创建/构建/开发 [功能]"
- "写一个 [组件/函数/API]"
- "实现 [算法/系统]"
- "帮我开发..."

### 基本流程
```
澄清 → 设计 → 确认 → 实现 → 测试 → 交付
```

---

## 场景速查表

### 场景 1: 工具函数
**示例**: "创建一个防抖函数"

**流程**:
1. 简短澄清(1-2问题)
2. 快速确认
3. 直接实现
4. 使用示例

**关键点**:
- 包含类型定义
- 处理边缘情况
- JSDoc/docstring
- 使用示例

---

### 场景 2: API 端点
**示例**: "创建用户登录 API"

**澄清要点**:
- [ ] 技术栈? (Node.js/Python/etc.)
- [ ] 数据库? (PostgreSQL/MongoDB/etc.)
- [ ] 认证方式? (JWT/Session/etc.)
- [ ] 验证规则?

**设计要点**:
- 分层架构(Route → Controller → Service → Repository)
- 中间件(认证、验证、日志)
- 错误处理策略
- 安全措施

**实现清单**:
- [ ] 路由定义
- [ ] 请求验证
- [ ] 业务逻辑
- [ ] 数据访问
- [ ] 错误处理
- [ ] 响应格式

---

### 场景 3: React 组件
**示例**: "创建一个搜索自动完成组件"

**澄清要点**:
- [ ] API 格式?
- [ ] 状态管理方式?
- [ ] 样式方案?
- [ ] 可访问性要求?

**设计要点**:
- 组件结构
- 状态管理
- 副作用处理
- 性能优化

**实现清单**:
- [ ] 函数组件 + Hooks
- [ ] 防抖搜索
- [ ] 加载/错误状态
- [ ] 键盘导航
- [ ] ARIA 属性
- [ ] PropTypes/TypeScript

---

### 场景 4: 数据处理脚本
**示例**: "处理 CSV 文件并生成报告"

**澄清要点**:
- [ ] CSV 格式和列?
- [ ] 数据验证规则?
- [ ] 输出格式?
- [ ] 错误处理策略?

**设计要点**:
- ETL 模式
- 数据验证
- 错误处理
- 日志记录

**实现清单**:
- [ ] 文件读取
- [ ] 数据验证
- [ ] 数据转换
- [ ] 报告生成
- [ ] 错误日志
- [ ] 使用示例

---

### 场景 5: 算法实现
**示例**: "实现 Dijkstra 最短路径算法"

**澄清要点**:
- [ ] 输入数据结构?
- [ ] 输出格式?
- [ ] 性能要求?

**实现清单**:
- [ ] 算法实现
- [ ] 复杂度分析
- [ ] 输入验证
- [ ] 边缘情况
- [ ] 详细注释
- [ ] 测试用例
- [ ] 使用示例

---

## 关键检查点

### 需求澄清阶段 ✓
```
- 明确输入/输出格式
- 确认技术栈
- 识别约束条件
- 讨论边缘场景
```

### 技术设计阶段 ✓
```
- 选择架构模式
- 定义组件职责
- 规划错误处理
- 考虑性能和安全
```

### 实现阶段 ✓
```
- 代码规范
- 错误处理
- 性能优化
- 安全措施
- 文档注释
```

### 测试阶段 ✓
```
- 正常流程
- 边缘场景
- 错误情况
- 集成点
```

### 交付阶段 ✓
```
- 所有源文件
- 配置文件
- 文档说明
- 使用示例
- 依赖列表
```

---

## 代码质量清单

### ✓ 可读性
- [ ] 有意义的命名
- [ ] 一致的风格
- [ ] 适当的注释
- [ ] 清晰的结构

### ✓ 健壮性
- [ ] 输入验证
- [ ] 错误处理
- [ ] 边缘场景
- [ ] 资源清理

### ✓ 性能
- [ ] 高效算法
- [ ] 避免不必要计算
- [ ] 适当缓存
- [ ] 异步 I/O

### ✓ 安全
- [ ] 输入清理
- [ ] 防注入攻击
- [ ] 不泄露敏感信息
- [ ] 安全依赖

### ✓ 可维护性
- [ ] DRY 原则
- [ ] 单一职责
- [ ] 可测试
- [ ] 低耦合

---

## 常用模式速查

### JavaScript/Node.js

#### Express API 模式
```javascript
// routes/resource.js
router.get('/:id', controller.get);
router.post('/', validate, controller.create);

// controllers/resource.js
exports.get = async (req, res, next) => {
  try {
    const data = await service.getById(req.params.id);
    res.json({ success: true, data });
  } catch (error) {
    next(error);
  }
};

// services/resource.js
exports.getById = async (id) => {
  const data = await repository.findById(id);
  if (!data) throw new NotFoundError();
  return data;
};
```

#### 错误处理
```javascript
class CustomError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

app.use((error, req, res, next) => {
  const statusCode = error.statusCode || 500;
  res.status(statusCode).json({
    success: false,
    error: {
      message: error.message,
      code: error.code
    }
  });
});
```

### React

#### 组件模式
```javascript
const Component = ({ prop1, prop2 }) => {
  const [state, setState] = useState(initial);
  
  useEffect(() => {
    // 副作用
    return () => {
      // 清理
    };
  }, [deps]);
  
  const handleEvent = useCallback(() => {
    // 处理
  }, [deps]);
  
  return <div>{/* JSX */}</div>;
};
```

#### 自定义 Hook
```javascript
const useCustomHook = (param) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    // 逻辑
  }, [param]);
  
  return { data, loading, error };
};
```

### Python

#### 类模式
```python
class Service:
    """服务类文档"""
    
    def __init__(self, dependency):
        self.dependency = dependency
        self.logger = setup_logger(__name__)
    
    def process(self, data: List[Dict]) -> pd.DataFrame:
        """
        处理数据
        
        Args:
            data: 输入数据
            
        Returns:
            处理后的数据
            
        Raises:
            ValueError: 无效输入
        """
        try:
            validated = self._validate(data)
            result = self._transform(validated)
            return result
        except Exception as e:
            self.logger.error(f"处理失败: {e}")
            raise
```

#### 上下文管理器
```python
with open(file_path, 'r') as f:
    data = f.read()

with database.connection() as conn:
    result = conn.execute(query)
```

### Go

#### 错误处理模式
```go
// 自定义错误
var (
    ErrNotFound = errors.New("not found")
    ErrInvalid  = errors.New("invalid input")
)

// 错误包装
func ProcessData(id int) error {
    data, err := fetch(id)
    if err != nil {
        return fmt.Errorf("process failed: %w", err)
    }
    return nil
}

// 错误检查
if errors.Is(err, ErrNotFound) {
    // 处理
}
```

#### Struct 方法模式
```go
// User 代表系统用户
type User struct {
    id   int64
    name string
}

// ID 返回用户ID
func (u *User) ID() int64 {
    return u.id
}

// SetName 设置用户名
func (u *User) SetName(name string) error {
    if name == "" {
        return errors.New("name cannot be empty")
    }
    u.name = name
    return nil
}
```

#### 并发模式
```go
// Worker Pool
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

---

## 文档模板

### JSDoc
```javascript
/**
 * 函数简短描述
 * 
 * 更详细的说明(如果需要)
 * 
 * @param {string} param1 - 参数说明
 * @param {Object} options - 配置选项
 * @param {number} options.timeout - 超时时间
 * @returns {Promise<Result>} 返回值说明
 * @throws {ErrorType} 何时抛出错误
 * 
 * @example
 * const result = await funcName('value', { timeout: 5000 });
 */
```

### Python Docstring
```python
def function_name(param1: str, param2: int = 10) -> Dict:
    """
    函数简短描述
    
    更详细的说明(如果需要)
    
    Args:
        param1: 参数说明
        param2: 参数说明,默认 10
    
    Returns:
        返回值说明
    
    Raises:
        ValueError: 何时抛出错误
    
    Example:
        >>> result = function_name('value', 20)
        {'key': 'value'}
    """
```

---

## 错误类型参考

### JavaScript
```javascript
TypeError          // 类型错误
ReferenceError     // 引用错误
SyntaxError        // 语法错误
RangeError         // 范围错误

// 自定义
ValidationError
AuthenticationError
NotFoundError
ServiceUnavailableError
```

### Python
```python
ValueError         # 值错误
TypeError          # 类型错误
KeyError           # 键错误
IndexError         # 索引错误
FileNotFoundError  # 文件不存在

# 自定义
ValidationError
AuthenticationError
NotFoundError
ServiceUnavailableError
```

---

## HTTP 状态码

```
200 OK                    - 成功
201 Created              - 创建成功
204 No Content           - 成功,无返回内容
400 Bad Request          - 客户端错误
401 Unauthorized         - 未认证
403 Forbidden            - 无权限
404 Not Found            - 资源不存在
409 Conflict             - 冲突
422 Unprocessable Entity - 验证失败
500 Internal Server Error - 服务器错误
503 Service Unavailable  - 服务不可用
```

---

## 性能优化提示

### JavaScript/React
- 使用 `useMemo` 缓存计算结果
- 使用 `useCallback` 缓存函数
- 使用 `React.memo` 避免重渲染
- 代码分割 `React.lazy`
- 虚拟化长列表

### Python
- 使用列表推导式而非循环
- 使用生成器处理大数据
- 选择正确的数据结构
- 使用 `lru_cache` 缓存
- 向量化操作 (NumPy)

### 数据库
- 添加适当索引
- 使用连接池
- 批量操作
- 避免 N+1 查询
- 使用预处理语句

---

## 安全检查清单

- [ ] 输入验证和清理
- [ ] 参数化查询(防 SQL 注入)
- [ ] XSS 防护
- [ ] CSRF 保护
- [ ] 密码哈希(bcrypt/argon2)
- [ ] 环境变量存储敏感数据
- [ ] HTTPS 通信
- [ ] 速率限制
- [ ] 日志不包含敏感信息
- [ ] 依赖项安全检查

---

## 常见反模式(避免)

❌ **不要**:
```javascript
// 全局变量污染
var globalVar = 'bad';

// 深层嵌套
if (a) {
  if (b) {
    if (c) {
      // 难以维护
    }
  }
}

// 忽略错误
try { riskyOp(); } catch (e) {}

// 硬编码配置
const API_KEY = 'abc123';
```

✅ **要**:
```javascript
// 模块作用域
const moduleVar = 'good';

// 提前返回
if (!a) return;
if (!b) return;
if (!c) return;
// 清晰逻辑

// 处理错误
try {
  riskyOp();
} catch (error) {
  logger.error(error);
  throw new CustomError();
}

// 环境变量
const API_KEY = process.env.API_KEY;
```

---

## 快速调试提示

### 常见问题

**"Cannot read property of undefined"**
→ 添加可选链 `obj?.prop?.nested`

**"CORS error"**
→ 配置 CORS 中间件

**"Module not found"**
→ 检查依赖安装和路径

**"Port already in use"**
→ 更改端口或终止进程

**"Connection refused"**
→ 检查服务是否运行

---

## 项目复杂度判断

### 简单 (<100 行)
- 单个函数/工具
- 最小流程
- 快速交付

### 中等 (100-500 行)
- 单个功能模块
- 标准流程
- 适度测试

### 复杂 (>500 行)
- 完整系统/多模块
- 完整流程
- 全面测试和文档

---

## 使用技巧

### 加速开发
说: "跳过确认,直接实现"

### 获得详细设计
说: "我需要详细的技术方案"

### 指定风格
说: "使用函数式编程风格"

### 添加测试
说: "包含完整的测试套件"

### 特定框架
说: "使用 TypeScript 和 Express"

---

**提示**: 这个快速参考是为了日常使用,完整文档请查看 SKILL.md
