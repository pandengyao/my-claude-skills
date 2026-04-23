# 百度 Go 编码规范 v1.3

本文档为百度内部Go语言编码规范，包含代码规范检查的详细规则。

## 规范级别

- **Rule**：要求所有程序必须遵守，不得违反
- **Advice**：建议遵守，除非确有特殊情况

## 适用范围

1. 不适用于头部带有 `DO NOT EDIT`注释的生成类文件
2. 不适用于第三方依赖库
3. 不适用于主动使用 `//nolint` 注释跳过的代码段

---

# 2. 命名规范

### [Rule001] 变量、常量、函数名使用驼峰法进行命名

驼峰法是Go中常用的命名方法。特别注意缩写词如HTTP、ID、URL应该大写。

常用缩写名单：
"ACL", "API", "ASCII", "CPU", "CSS", "DNS", "EOF", "GUID", "HTML", "HTTP", "HTTPS", "ID", "IP", "JSON", "QPS", "RAM", "RPC", "SLA", "SMTP", "SQL", "SSH", "TCP", "TLS", "TTL", "UDP", "UI", "GID", "UID", "UUID", "URI", "URL", "UTF8", "VM", "XML", "XMPP", "XSRF", "XSS", "SIP", "RTP", "AMQP", "DB", "TS"

**Good:**
```go
const FileNotExistsCode = 404
const DialTimeout = 1
func ServeHTTP(rw ResponseWriter, req *Request) {}
```

**Bad:**
```go
const FILE_NOT_FOUND_CODE = 404
const Dial_Timeout = 1
func ServeHttp(rw ResponseWriter, req *Request) {}
```

### [Rule002] error 类型的顶级变量请添加 err 或 Err 前缀

按照变量是否需要导出，对错误类型的变量添加`err/Err`前缀。

**Good:**
```go
var (
    ErrDial      = errors.New("dial")
    errNotFound  = errors.New("not found")
)
```

### [Rule003] 禁止 receiver 使用 self、this 等其他语言惯用名

**Good:**
```go
type User struct{ id int64 }
func (u *User) ID() int64 { return u.id }
```

**Bad:**
```go
func (this *User) ID() int64 { return this.id }
```

### [Rule004] receiver 的名称应该简短且保持一致

**Good:**
```go
type User struct{ id int64; name string }
func (u *User) ID() int64 { return u.id }
func (u *User) Name() string { return u.name }
```

### [Rule005] 包名应该简短、全小写、并且不要使用下划线

**Good:** `time`, `strconv`, `http`
**Bad:** `computeServiceClient`, `priority_queue`

### [Rule006] 包内类型不应以包名为前缀

**Good:**
```go
package net
func Dial(network, address string) (Conn, error) {}
```

**Bad:**
```go
package net
func NetDial(network, address string) (Conn, error) {}
```

---

# 3. 文件规范

### [Rule101] 文件名应使用小写字母，并以.go为后缀，满足规则 [a-z0-9_]+.go

### [Rule102] 所有源文件编码必须是 UTF-8

### [Rule103] 每行代码不超过160个字符

### [Rule104] 测试数据文件应放在单测文件同级目录下的 testdata 目录里

### [Rule105] 应使用 go mod 管理依赖，并将 go.mod 和 go.sum 文件提交到代码库

### [Advice101] 单个文件不超过2000行

### [Advice102] 同一个 struct 的方法应在同一个文件里

### [Advice103] pkg 的功能描述建议写到单独的 doc.go 文件

---

# 4. 语言规范

### [Rule201] 文件应通过 go vet 的检查

### [Rule202] 禁止在 if、for 中对 bool 类型进行等值判断

**Good:**
```go
if !ok { println("false") }
```

**Bad:**
```go
if ok == false { println("false") }
```

### [Rule203] 当函数以 else 结尾时，应删除 else 语句直接 return

**Good:**
```go
func checkID(id int) error {
    if id > 0 {
        return nil
    }
    return errors.New("i'm failed")
}
```

**Bad:**
```go
func checkID(id int) error {
    if id > 0 {
        return nil
    } else {
        return errors.New("i'm failed")
    }
}
```

### [Rule204] error 类型始终放在返回参数末尾

### [Rule205] 函数返回值中的 error 必须处理，defer 调用除外

### [Rule206] 包装 error 时，应使用 fmt.Errorf 并配合 %w

**Good:**
```go
fmt.Errorf("%w, id=%d", err, 1)
```

**Bad:**
```go
fmt.Errorf("%s, id=%d", err.Error(), 1)
```

### [Rule207] 当入参包含 context.Context 时，总是作为第一个参数

### [Rule208] 如果 receiver 是 struct，且包含 sync.Mutex 类型字段，则必须使用指针避免拷贝

### [Rule209] 如果 receiver 是 map、函数或者 chan 类型，类型不可以是指针

### [Rule210] 如果 receiver 是 slice，并且方法不会进行 reslice 或者重新分配 slice，类型不可以是指针

### [Rule211] 禁止直接在 for 循环中使用 defer

### [Rule212] 函数的圈复杂度不得高于30

### [Rule213] 给 struct 赋值时，不可以省略字段名

### [Advice201] 如果 receiver 是比较大的 struct/array，建议使用指针

### [Advice202] 如果 receiver 是比较小的 struct/array，建议使用 value 类型

### [Advice203] 申明 slice 时，建议使用 var 方式申明；若能预估大小，建议预分配大小

### [Advice204] 一个 struct 定义内，最多 embedding 1 个 struct

### [Advice205] 函数参数不建议超过 5 个

### [Advice206] 函数返回值小于等于 3 个

---

# 5. 风格规范

### [Rule301] 使用 tab 进行缩进，并统一格式化

### [Rule302] 所有导出的类型都需要被注释, 并以该类型名为注释的开头

```go
// MinAge 允许报名的最小年龄
const MinAge = 3

// SayHello 在终端输出 "Hello World"
func SayHello() {
    println("Hello World")
}
```

### [Rule303] 全局的同一类型的常量和变量，应定义在同一个分组里

### [Rule304] 包的注释应以 "Package " 为前缀

### [Rule305] 函数之间应有1个空行

### [Rule306] 类型定义之间应有1个空行

### [Rule307] import 需要按照标准库、第三方库、项目自身库的顺序分组排列，每组之间一个空行

### [Rule308] 禁止使用点号格式 import

### [Rule309] 使用"_" import 的包，需要予以注释说明原因

### [Rule310] error string不得以大写字母开头，结尾不带标点符号

**Good:** `errors.New("something bad")`
**Bad:** `fmt.Errorf("Something bad.")`

### [Advice301] 函数内不同的业务逻辑处理建议采用单个空行分割

### [Advice302] 尽量不要在程序中直接写数字，特殊字符串，而是用常量替代

### [Advice303] 推荐使用单行注释 "//"，而不是 "/* */"

### [Advice304] Copyright 应放在文件的头部

### [Advice305] 在函数内部不使用分组方式定义常量和变量

---

# 6. 编程实践

### [001] 变量、常量的分组

同类型的、有关联的可以定义到一组。

### [002] iota 的使用

0 值一般当做缺省值，是默认值。

### [003] switch 的使用

类型断言时可以直接赋值：
```go
switch v := val.(type) {
    case int:
        return v, true
    case string:
        num, err := strconv.Atoi(v)
        return num, err==nil
}
```

### [004] 函数参数和返回值

对于"逻辑判断型"的函数，返回值类型定义为bool。
对于"操作型"的函数，返回值类型定义为error。

### [005] Don't panic

除非出现不可恢复的程序错误，不要使用panic。

### [006] 关于 Lock 的使用

同一个变量会在不同协程里同时读和写时，需要使用锁来保护。

### [007] 日志的处理

建议使用 GDP 的 logit。

### [008] 稳定性指标监控

应对 goroutine 数添加监控报警。

### [009] unsafe package

除非特殊原因，不建议使用 unsafe package。

### [010] 单元测试

1. 单测文件和代码文件放在同一个目录下
2. 单测所需数据文件放在 testdata 目录
3. 执行单测时应添加 -race 参数

### [011] 正则表达式

使用前应对正则预编译。

### [012] 注意循环闭包问题

### [013] nil 值的使用

interface 类型只有当其 iface 和 eface 同时为nil 时才是真的 nil。

### [014] 安全

1. 日志、接口输出不要触犯《百度安全红线》
2. 调试接口、metrics Exporter 接口、pprof 接口等不可在外网访问
3. 查询数据库时建议使用 SQLBuilder 或 ORM
4. 数据库应配置 IP 白名单和密码
5. 密码/秘钥使用 SSM 系统托管

### [015] 字符串

不区分大小写的比较使用 strings.EqualFold。

### [016] JSON 编解码

遇到不确定结构和类型的字段可以定义为 json.RawMessage 类型。

### [017] 注意隐匿的map、slice 的并发读写问题

---

# 7. 相关工具

## 代码格式化工具

- **gorgeous** (推荐)：能自动识别修改的文件并格式化
- **gofumpt**：更严格的 gofmt
- **gofmt**：Go SDK 内置
- **goimports**：格式化 import

## 代码检查工具

- **go vet** (推荐)：Go SDK 内置的静态代码分析工具
- **golangci-lint** (推荐)：快速的 Go linters runner
- **revive**：可配置的 linter
- **staticcheck** (推荐)：静态分析工具
