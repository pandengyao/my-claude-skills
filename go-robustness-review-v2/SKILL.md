---
name: go-robustness-review-v2
description: >
  对 Go 代码仓库进行全面的鲁棒性、稳定性和安全性审查。覆盖7大类42项检查：
  A-并发安全10项（数据竞争、死锁、goroutine泄漏、闭包循环变量、并发map的fatal不可recover、
  TOCTOU、sync值拷贝、atomic误用、channel误用含nil/closed/重复close、errgroup取消语义）、
  B-错误处理5项（忽略错误、包装丢失、panic含MustCompile、错误后缺return、sentinel用==而非errors.Is）、
  C-资源管理6项（资源泄漏含CancelFunc、defer循环、context未用含Background替换、连接池配置、临时文件、无界Map/缓存增长）、
  D-空值类型安全6项（nil指针含interface nil陷阱、类型断言含链式、nil map、切片越界含Split、
  interface滥用、slice引用语义含append共享底层数组）、
  E-数据安全6项（SQL注入含非值位置白名单、UTF-8截断、整数溢出含int平台差异、路径遍历、敏感信息泄露、不安全随机数）、
  F-HTTP/API 5项（Body未关闭、panic处理、不可信数据源无界读取含ReadAll、超时缺失含Slowloris、共享状态）、
  G-生命周期逻辑10项（优雅关闭、init副作用、边界条件、死循环与无界增长含树图遍历循环检测、time.After泄漏、
  json隐患含omitempty零值、time.Time比较含单调时钟、select公平性、log.Fatal在库代码中、大对象循环分配）。
  当用户提到"代码审查"、"code review"、"鲁棒性"、"稳定性"、"高可用"、"安全审计"、
  "bug扫描"、"风险排查"、"生产就绪检查"、"代码质量"、"OOM"、"内存溢出"、"内存泄漏"、
  "memory leak"等关键词且代码为Go语言时使用此技能。
  即使用户只说"帮我看看代码有没有问题"这样模糊的请求，只要项目是Go语言，也应触发此技能。
---
# Go 代码库全面安全与鲁棒性审查

## 任务目标

对当前 Go 代码仓库进行**全面的代码审查**，识别所有影响**高可用性、稳定性和安全性**的逻辑风险，并输出结构化的审查报告。

---

## 执行流程

### 阶段一：仓库全景扫描

1. 执行 `find . -name "*.go" -not -path "./vendor/*" -not -path "./.git/*" | head -500` 获取文件清单
2. 执行 `wc -l $(find . -name "*.go" -not -path "./vendor/*" -not -path "./.git/*")` 了解代码规模
3. 执行 `go list ./...` 了解包结构
4. 查看 `go.mod` 了解依赖和 Go 版本（**Go 版本直接影响多项检查的适用性，必须记录**）
5. 如果存在 `Makefile`、`Dockerfile`、`.goreleaser.yml` 等，也一并查看
6. 执行 `grep -rn "go func" --include="*.go" -l` 快速定位并发热点文件
7. 执行 `grep -rn "chan " --include="*.go" -l` 定位 channel 使用文件
8. 执行 `grep -rn "\.Query\|\.Exec\|\.QueryRow" --include="*.go" -l` 定位数据库操作文件
9. 检查是否存在 `http.ListenAndServe` 或 HTTP 框架引入（决定 F 类检查是否适用）
10. 执行 `grep -rn "io.ReadAll\|ioutil.ReadAll" --include="*.go" -l` 定位无界读取热点
11. **死循环与无界遍历热点扫描**（使用 5 种结构模式，不依赖变量命名）：
    ```bash
    # 模式A — 链式字段遍历: x = x.Field（变量赋值为自身字段）
    grep -Pn '(\b\w+)\s*=\s*\1\.\w+' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

    # 模式B — 映射自查遍历: x = map[x]（变量用自身做 key 查 map 再赋值给自身）
    grep -Pn '(\b\w+)\s*=\s*\w+\[\1\]' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

    # 模式C — BFS 队列自馈: for len(q) > 0 + append(q, ...)
    grep -Pn 'for\s+len\(\w+\)\s*>\s*0' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

    # 模式D — 无限循环 + DB 反馈: for { / for true { 内含 DB 查询且参数来自上轮结果
    grep -n 'for true\|for {' --include="*.go" -r . | grep -v _test.go | grep -v vendor

    # 模式E — 递归自调用: 函数体内调用同名函数
    # （对模式D的每个命中文件，检查 for 块内是否有 .Where/.Find 且循环变量被结果字段赋值）
    ```
    > **为什么用结构模式而非语义关键词**：搜索 `Parent`/`Children` 等关键词会遗漏使用 `upstream`/`downstream`、`prev`/`next`、`manager`/`subordinate`、`source`/`target` 等命名的遍历。以上 5 种模式从**代码数据流结构**（变量的"下一步"值来自"当前步"的派生）入手，覆盖所有自引用迭代，不受命名影响。

### 阶段二：静态分析辅助（如可用）

尝试运行以下工具收集线索（如果仓库已安装或可安装）：

```bash
# go vet 基础检查（几乎一定可用）
go vet ./... 2>&1

# 数据竞争检测（需要能编译通过）
go build -race ./... 2>&1 | head -100

# 如果安装了 staticcheck
staticcheck ./... 2>&1 | head -200

# 如果安装了 golangci-lint（覆盖更全面）
golangci-lint run --enable-all --timeout 5m 2>&1 | head -300
```

> 注意：静态工具的结果仅作为辅助参考，核心审查依赖逐文件人工分析。工具无法检出的**逻辑风险和跨文件交互问题**才是本次审查的核心价值。

### 阶段三：逐文件深度审查

按照下方「审查清单」中的 **7 大类 42 项检查点**，对每个 `.go` 文件进行审查。

**审查策略：**
- 优先审查：`main.go`、包含 `go func` 的文件、`handler/`、`service/`、`middleware/`、`pkg/` 目录
- 重点关注：并发相关代码、数据库操作、HTTP 处理、资源管理
- 对于每个文件，系统性地逐项检查，不要遗漏
- **每检查完一个文件，用一句话记录该文件的主要职责和发现的问题数**

### 阶段四：交叉分析

在完成单文件审查后，进行**跨文件的系统性分析**（这是单文件审查无法覆盖的关键步骤）：

1. **共享状态一致性**：同一个共享变量/结构体在不同文件中的所有读写点是否都正确同步？
2. **锁顺序一致性**：追踪所有获取多把锁的调用路径，是否存在 A->B 和 B->A 的顺序不一致？
3. **context 传递完整性**：context 是否在整个调用链中正确传递？是否有中间层丢弃了 context 用 `context.Background()` 替代？
4. **错误传播完整性**：error 是否在整个调用链中正确传播？是否有中间层吞掉了错误？
5. **优雅关闭完整性**：程序收到 SIGTERM/SIGINT 后，所有 goroutine、连接、资源是否都能正确清理？
6. **初始化顺序依赖**：`init()` 函数之间、全局变量初始化之间是否存在隐含的顺序依赖？
7. **接口契约一致性**：interface 的实现者是否都满足了调用方的隐含假设（如线程安全性、nil 安全性）？

---

## 审查清单（7 大类 42 项）

> **通用说明**：每条检查项包含「问题描述」「危害代码模式」「正确代码模式」「排除误判条件」四个维度。审查时请逐一对照，减少遗漏和误报。

---

### A类：并发安全（最高优先级，共10项）

#### A1 数据竞争

- **问题**：多个 goroutine 同时读写同一变量，且未使用同步原语保护
- **危害模式**：
  ```go
  // 模式1：结构体字段被多个 goroutine 并发访问
  type Server struct { count int }
  func (s *Server) Handle() { s.count++ }  // 在 HTTP handler 中被并发调用
  
  // 模式2：全局包级变量被并发读写
  var cache = map[string]string{}
  func Set(k, v string) { cache[k] = v }
  
  // 模式3：闭包共享外部变量
  func newCounter() func() int {
      n := 0
      return func() int { n++; return n }  // 多 goroutine 调用此闭包时竞争
  }
  ```
- **正确模式**：`sync.Mutex` / `sync.RWMutex` / `atomic.AddInt64` / `sync.Map`
- **排除误判**：单 goroutine 访问的局部变量；`init()` 中的一次性赋值；只读的全局常量；被 `sync.Once` 保护的初始化
- **审查方法**：重点关注结构体中没有 `mu sync.Mutex` 但有 `map` 或计数器字段的类型

#### A2 死锁

- **问题**：程序永久阻塞，不再响应
- **危害模式**：
  ```go
  // 模式1：嵌套锁顺序不一致
  func f1() { mu1.Lock(); mu2.Lock() }  // A->B
  func f2() { mu2.Lock(); mu1.Lock() }  // B->A -> 死锁
  
  // 模式2：无缓冲 channel 在同一 goroutine 收发
  ch := make(chan int)
  ch <- 1   // 阻塞，没有接收者
  v := <-ch
  
  // 模式3：锁内发送 channel，接收方也需要同一把锁
  mu.Lock()
  ch <- data  // 接收方也会 mu.Lock() -> 死锁
  mu.Unlock()
  
  // 模式4：WaitGroup.Add 在 goroutine 内部调用
  var wg sync.WaitGroup
  for i := 0; i < n; i++ {
      go func() {
          wg.Add(1)  // 应在 go 之前 Add
          defer wg.Done()
      }()
  }
  wg.Wait()  // 可能在 Add 之前就 Wait 了
  
  // 模式5：RWMutex 读锁内再获取写锁
  mu.RLock()
  mu.Lock()  // 死锁
  ```
- **正确模式**：统一锁顺序；带缓冲 channel 或 select+timeout；WaitGroup.Add 在 goroutine 启动前调用
- **排除误判**：已确认不会交叉调用的独立锁

#### A3 goroutine 泄漏

- **问题**：goroutine 永久阻塞无法退出，持续消耗内存，最终 OOM
- **危害模式**：
  ```go
  // 模式1：channel 无人消费
  go func() {
      result := <-ch  // ch 永远没写入者
  }()
  
  // 模式2：缺少退出信号
  go func() {
      for {
          doWork()  // 没有 select ctx.Done()
      }
  }()
  
  // 模式3：消费者退出后生产者阻塞
  ch := make(chan int, 10)
  go func() {
      for { ch <- produce() }  // 缓冲满后永久阻塞
  }()
  
  // 模式4：HTTP handler 中启动无管理的后台 goroutine
  func handler(w http.ResponseWriter, r *http.Request) {
      go func() { processAsync(data) }()  // 无生命周期管理
  }
  
  // 模式5：错误路径忘记通知 goroutine 退出
  ctx, cancel := context.WithCancel(context.Background())
  go worker(ctx)
  if err := setup(); err != nil {
      return err  // 忘记 cancel()，worker 永远不退出
  }
  ```
- **正确模式**：所有长期 goroutine 必须有 `context.Context` 或 `done channel` 退出机制；退出路径覆盖所有错误分支
- **排除误判**：main 中有意的永久运行 goroutine

#### A4 闭包捕获循环变量

- **问题**：goroutine 闭包捕获循环变量，所有 goroutine 共享最终值
- **危害模式**：
  ```go
  for _, item := range items {
      go func() {
          process(item)  // 都拿到最后一个元素
      }()
  }
  // 也包括 errgroup、defer 中的闭包
  for _, item := range items {
      g.Go(func() error { return process(item) })
  }
  ```
- **正确模式**：`go func(it Item) { process(it) }(item)` 通过参数传递
- **排除误判**：**Go 1.22+ (go.mod 中 `go 1.22` 及以上) 已修复此问题**。审查时必须先检查 go.mod 版本。

#### A5 并发读写 map

- **问题**：Go 原生 map 不是并发安全的，并发读写触发 fatal error
- **危害模式**：
  ```go
  m := make(map[string]int)
  go func() { m["a"] = 1 }()
  go func() { _ = m["a"] }()  // fatal: concurrent map read and map write
  ```
- **正确模式**：`sync.Map`（读多写少）；`sync.RWMutex` + map（写多或需遍历）
- **排除误判**：只在单 goroutine 中使用的 map；init() 中初始化后只读的 map
- **特别强调**：此类 fatal **无法被 recover 捕获**，属于进程级崩溃，是最严重的并发 bug 之一

#### A6 竞态条件（TOCTOU）

- **问题**：检查和执行之间状态可能被其他 goroutine 改变
- **危害模式**：
  ```go
  // check-then-act 非原子
  if _, ok := cache[key]; !ok {
      cache[key] = expensiveCompute()
  }
  
  // 文件操作 TOCTOU
  if _, err := os.Stat(path); os.IsNotExist(err) {
      os.Create(path)  // 可能已被其他进程创建
  }
  
  // 并发环境先查长度再访问
  if len(queue) > 0 {
      item := queue[0]  // 另一个 goroutine 可能已取走
  }
  ```
- **正确模式**：`sync.Once`；`sync.Map.LoadOrStore`；`os.OpenFile` + `O_CREATE|O_EXCL`；锁保护原子性

#### A7 sync 原语值拷贝

- **问题**：`sync.Mutex`、`sync.WaitGroup`、`sync.Once`、`sync.Cond` 被值拷贝后失去同步语义
- **危害模式**：
  ```go
  type Service struct { mu sync.Mutex }
  func process(s Service) {  // 值传递，mu 被拷贝，锁失效
      s.mu.Lock()
  }
  s2 := s1  // s1.mu 和 s2.mu 是两把独立的锁
  ```
- **正确模式**：使用指针接收者 `func process(s *Service)`
- **审查方法**：搜索包含 `sync.Mutex`/`sync.WaitGroup` 的结构体，检查值传递

#### A8 atomic 使用错误

- **问题**：对需要原子操作的变量混用 atomic 和普通读写
- **危害模式**：
  ```go
  var counter int64
  atomic.AddInt64(&counter, 1)  // 原子写
  fmt.Println(counter)           // 非原子读 -> 数据竞争
  
  // 32位平台对齐问题
  type Stats struct {
      name  string
      count int64  // 32位平台上可能未8字节对齐，atomic 操作 panic
  }
  ```
- **正确模式**：所有读写都通过 atomic 函数；Go 1.19+ 用 `atomic.Int64` 类型
- **注意**：32 位平台上 int64/uint64 的 atomic 操作要求 8 字节对齐

#### A9 channel 误用

- **问题**：channel 使用不当导致 panic 或永久阻塞
- **危害模式**：
  ```go
  // 向已关闭的 channel 发送 (panic: send on closed channel)
  close(ch); ch <- data
  
  // 重复关闭 (panic: close of closed channel)
  close(ch); close(ch)
  
  // nil channel 操作 (永久阻塞，不是 panic)
  var ch chan int
  ch <- 1   // 永久阻塞
  <-ch      // 永久阻塞
  close(ch) // panic: close of nil channel
  
  // 关闭信号 channel 但未排空数据 channel
  close(done)  // dataCh 中还有数据，发送方阻塞
  ```
- **正确模式**：只由发送方关闭；`sync.Once` 保证只关闭一次；初始化后再使用

#### A10 errgroup 并发错误处理

- **问题**：使用 errgroup 时不理解其取消语义
- **危害模式**：
  ```go
  g, ctx := errgroup.WithContext(parentCtx)
  for _, url := range urls {
      url := url
      g.Go(func() error {
          return fetch(url)  // 未用 ctx，某个报错后其他继续跑
      })
  }
  return g.Wait()  // 只返回第一个 error
  ```
- **正确模式**：goroutine 内应使用返回的 ctx 并响应取消
- **排除误判**：明确只关心第一个错误的场景

---

### B类：错误处理（共5项）

#### B1 忽略错误返回值

- **问题**：函数返回 error 但被显式丢弃或完全不接收
- **危害模式**：
  ```go
  _ = db.Close()
  json.Unmarshal(data, &v)  // 完全不接收 error
  f.Write(data)             // io.Writer error 被忽略
  ```
- **排除误判**：`fmt.Println` 日志 error 可忽略；`defer xxx.Close()` 通常可忽略（但写操作后的 Close 不应忽略，可能意味着数据未刷盘）
- **审查方法**：`grep -rn "_ =" --include="*.go"` 逐条确认

#### B2 错误包装丢失上下文

- **问题**：直接 `return err` 导致上层无法判断错误来源
- **危害模式**：
  ```go
  func GetUser(id int) (*User, error) {
      err := row.Scan(&user)
      return nil, err  // 丢失上下文
  }
  ```
- **正确模式**：`return nil, fmt.Errorf("GetUser(id=%d): %w", id, err)` 使用 `%w`

#### B3 panic 风险未防护

- **问题**：未预期 panic 导致进程崩溃
- **危害模式**：
  ```go
  val := m["key"].(string)            // 类型断言 panic
  go func() { riskyOperation() }()   // goroutine 无 recover
  return results[0]                   // 空切片 panic
  re := regexp.MustCompile(userInput) // 非法正则 panic
  ```
- **正确模式**：类型断言用 `v, ok :=`；关键 goroutine 加 `defer recover()`；用户输入用 `regexp.Compile`
- **注意**：HTTP handler 的 panic 被 net/http 默认 recover 但会断连且泄露堆栈

#### B4 错误处理后继续执行

- **问题**：检查了错误但没有 return/continue/break
- **危害模式**：
  ```go
  result, err := doSomething()
  if err != nil {
      log.Error("failed:", err)
      // 忘记 return！
  }
  useResult(result)  // result 可能是零值
  
  // 循环中忘记 continue
  for _, item := range items {
      val, err := transform(item)
      if err != nil { log.Warn("skip:", err) }
      results = append(results, val)  // 零值也加进去了
  }
  ```
- **正确模式**：`if err != nil` 块内必须有流程控制语句

#### B5 error sentinel 比较方式错误

- **问题**：用 `==` 比较被 `%w` 包装过的 error
- **危害模式**：
  ```go
  if err == sql.ErrNoRows { ... }       // 包装后永远 false
  if _, ok := err.(*MyError); ok { ... } // 包装后匹配不到
  ```
- **正确模式**：`errors.Is(err, sql.ErrNoRows)`；`errors.As(err, &target)`

---

### C类：资源管理（共6项）

#### C1 资源未关闭导致泄漏

- **问题**：文件、连接、Body 等未关闭，文件描述符/连接池耗尽
- **危害模式**：
  ```go
  // HTTP Response Body 未关闭（最常见）
  resp, err := http.Get(url)
  if err != nil { return err }
  data, _ := io.ReadAll(resp.Body)  // 忘记 defer resp.Body.Close()
  
  // sql.Rows 未关闭（循环中途 return 更会泄漏）
  rows, _ := db.Query("SELECT ...")
  for rows.Next() { ... }
  
  // context cancel 未调用（泄漏 goroutine 和 timer）
  ctx, cancel := context.WithTimeout(parent, 5*time.Second)
  // 忘记 defer cancel()
  ```
- **正确模式**：获得资源后立即 `defer xxx.Close()`
- **重点关注**：`http.Response.Body`、`os.File`、`sql.Rows`、`sql.DB`/`sql.Conn`、`net.Conn`、`net.Listener`、`context.CancelFunc`、`*exec.Cmd` 的 Pipe

#### C2 defer 在循环内导致资源堆积

- **问题**：defer 在 for 循环内，资源到函数返回时才释放
- **危害模式**：
  ```go
  for _, path := range paths {
      f, _ := os.Open(path)
      defer f.Close()  // 循环1000次就打开1000个fd
  }
  ```
- **正确模式**：提取为子函数（子函数 return 时 defer 执行）；或手动 Close

#### C3 context 未正确使用

- **问题**：接收了 context 但未用它控制生命周期
- **危害模式**：
  ```go
  // 接收 ctx 但不用
  func Process(ctx context.Context, data []byte) error {
      time.Sleep(10 * time.Second)  // 不响应取消
      return nil
  }
  
  // Background() 替代传入的 ctx
  func Query(ctx context.Context) error {
      return db.QueryRowContext(context.Background(), "SELECT ...")
  }
  ```
- **正确模式**：`select { case <-ctx.Done(): return ctx.Err() }`；透传 ctx 给下游

#### C4 连接池/客户端配置不当

- **问题**：连接池参数未设置
- **危害模式**：
  ```go
  db, _ := sql.Open("mysql", dsn)
  // 缺 SetMaxOpenConns/SetMaxIdleConns/SetConnMaxLifetime
  // 默认 MaxOpenConns=0(无限) -> 连接数暴涨
  
  client := &http.Client{}  // 无 Timeout -> 请求可能永久阻塞
  ```
- **正确模式**：sql.DB 必设连接池参数；http.Client 必设 Timeout

#### C5 临时文件/目录未清理

- **问题**：`os.CreateTemp`/`os.MkdirTemp` 创建的资源未删除
- **正确模式**：`defer os.Remove(tmpFile.Name())`

#### C6 无界 Map/缓存增长

- **问题**：全局 map 或缓存只增不删，无大小限制和过期机制，内存持续增长直至 OOM
- **危害模式**：
  ```go
  // 模式1：全局缓存只写不删
  var cache = make(map[string]Data)
  func GetData(key string) Data {
      if v, ok := cache[key]; ok { return v }
      v := fetchFromDB(key)
      cache[key] = v  // 缓存会无限增长
      return v
  }

  // 模式2：map 在循环中持续添加 key
  for _, event := range events {
      stats[event.Type]++  // 如果 event.Type 基数极大，map 无限增长
  }

  // 模式3：用 map 做去重但不清理
  var seen = make(map[string]bool)
  func Process(id string) {
      if seen[id] { return }
      seen[id] = true  // 永远不删除
  }
  ```
- **正确模式**：
  ```go
  // 方案1：使用 LRU 缓存（如 groupcache/lru、hashicorp/golang-lru）
  cache, _ := lru.New(maxEntries)

  // 方案2：设置 TTL 过期
  // 方案3：定期清理 + 大小限制
  if len(cache) > maxSize {
      // 清理最旧条目
  }
  ```
- **审查方法**：搜索全局 `map` 变量，检查是否有对应的 `delete` 或大小限制逻辑

---

### D类：空值与类型安全（共6项）

#### D1 nil 指针解引用

- **问题**：对可能为 nil 的指针直接调用方法
- **危害模式**：
  ```go
  user := getUser(id)    // 可能返回 nil
  fmt.Println(user.Name) // panic
  ```
- **正确模式**：`if user == nil { return ... }`
- **interface nil 陷阱**（Go 最著名的陷阱之一）：
  ```go
  var p *MyStruct = nil
  var i interface{} = p
  if i != nil {  // true！interface 有类型信息所以不为 nil
      i.(*MyStruct).Method()  // panic: nil pointer
  }
  // 返回 error 时尤其危险：
  func getError() error {
      var p *MyError = nil
      return p  // 返回的 error != nil
  }
  ```

#### D2 类型断言未检查

- **问题**：单返回值类型断言失败会 panic
- **危害模式**：
  ```go
  val := data.(map[string]interface{})  // panic
  // 链式断言更危险
  port := data.(map[string]interface{})["server"].(map[string]interface{})["port"].(float64)
  ```
- **正确模式**：`val, ok := data.(Type); if !ok { ... }`
- **排除误判**：type switch 中的断言是安全的

#### D3 nil map 写入

- **问题**：未初始化的 map 写入 panic
- **危害模式**：
  ```go
  var m map[string]int
  m["key"] = 1  // panic: assignment to entry in nil map
  
  type Config struct { Tags map[string]string }
  c := Config{}
  c.Tags["env"] = "prod"  // panic
  ```
- **正确模式**：`m := make(map[string]int)`
- **注意**：nil map 读取不会 panic（返回零值），只有写入才会

#### D4 切片越界访问

- **问题**：索引超出切片长度
- **危害模式**：
  ```go
  first := results[0]  // 空切片 panic
  
  parts := strings.Split(s, ":")
  port := parts[1]  // s 不含 ":" -> parts 只有1个元素 -> panic
  ```
- **正确模式**：`if len(results) > 0 { first = results[0] }`

#### D5 interface{}/any 滥用

- **问题**：大量空接口导致编译期类型检查失效
- **正确模式**：Go 1.18+ 用泛型；定义具体接口
- **注意**：搭配 D2 时风险升级

#### D6 slice/map 引用语义误解

- **问题**：slice 和 map 是引用类型，浅拷贝修改影响原始数据
- **危害模式**：
  ```go
  func process(items []int) { items[0] = 999 }  // 修改了原始 slice
  
  // append 共享底层数组
  a := make([]int, 3, 10)
  b := append(a, 1, 2, 3)
  c := append(a, 4, 5, 6)  // 覆盖 b 的数据
  
  // 暴露内部状态
  func (s *Store) GetItems() []Item { return s.items }  // 外部可修改
  ```
- **正确模式**：`copy` 或 `slices.Clone`(Go 1.21+)；返回内部 slice/map 时返回副本

---

### E类：数据安全与输入验证（共6项）

#### E1 SQL 注入

- **问题**：字符串拼接构造 SQL
- **危害模式**：
  ```go
  query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", userName)
  query := "SELECT * FROM users ORDER BY " + sortField
  query := "SELECT * FROM " + tableName + " WHERE id = ?"
  ```
- **正确模式**：参数化查询 `db.Query("SELECT ... WHERE name = ?", userName)`
- **注意**：参数化只保护值位置，表名/列名/ORDER BY 必须白名单校验

#### E2 字符串截断（UTF-8 破坏）

- **问题**：按字节索引截取 UTF-8 字符串
- **危害模式**：`truncated := s[:6]` 对中文等多字节字符产生非法 UTF-8
- **正确模式**：转 `[]rune` 再截取；`utf8.RuneCountInString` 获取字符数

#### E3 整数溢出与类型转换

- **问题**：类型转换静默截断
- **危害模式**：
  ```go
  small := int32(math.MaxInt64)  // 静默截断为 -1
  size, _ := strconv.Atoi(userInput)
  buf := make([]byte, size)  // 极大值 OOM；负数 panic
  ```
- **正确模式**：转换前范围检查；用户输入校验

#### E4 路径遍历

- **问题**：用户输入路径未清洗
- **危害模式**：
  ```go
  filePath := filepath.Join(baseDir, userInput)  // "../../etc/passwd"
  ```
- **正确模式**：Clean + HasPrefix 验证结果路径在 baseDir 下
- **注意**：`filepath.Join` 和 `filepath.Clean` 不做安全检查

#### E5 敏感信息泄露

- **问题**：密码/密钥/token 出现在日志、错误信息或 HTTP 响应中
- **危害模式**：
  ```go
  log.Printf("connecting to db: %s", dsn)  // DSN 含密码
  http.Error(w, err.Error(), 500)           // 内部错误暴露给客户端
  ```
- **正确模式**：日志脱敏；HTTP 返回通用错误消息

#### E6 不安全的随机数

- **问题**：安全场景用 `math/rand`
- **危害模式**：`token := fmt.Sprintf("%d", rand.Int63())`
- **正确模式**：`crypto/rand.Read`
- **排除误判**：非安全用途可用 math/rand
- **注意**：Go 1.20+ math/rand 自动种子但仍不适合安全场景

---

### F类：HTTP/API 特定问题（共5项）

> **适用条件**：仓库包含 HTTP 服务端/客户端代码时审查。纯 CLI 或库可跳过。

#### F1 HTTP Response Body 未关闭

- **问题**：Response Body 未关闭导致连接池泄漏
- **正确模式**：`defer resp.Body.Close()` 紧跟错误检查
- **注意**：即使不读 Body 也必须关闭

#### F2 HTTP handler panic 处理

- **问题**：handler panic 导致连接断开、堆栈泄露
- **正确模式**：recovery middleware，返回 500 并记录日志

#### F3 不可信数据源无界读取

- **问题**：从不可信数据源读取全部内容到内存，数据大小不可控导致 OOM
- **危害模式**：
  ```go
  // HTTP 请求体未限制大小
  data, _ := io.ReadAll(r.Body)

  // HTTP 响应体未限制大小
  resp, _ := http.Get(url)
  body, _ := io.ReadAll(resp.Body)  // 响应可能是 GB 级别

  // 网络连接数据未限制
  content, _ := io.ReadAll(conn)

  // 用户上传文件未限制
  data, _ := io.ReadAll(file)       // ioutil.ReadAll 同理

  // bytes.Buffer 从不可信源无限写入
  var buf bytes.Buffer
  io.Copy(&buf, r.Body)  // 无大小限制
  ```
- **正确模式**：
  ```go
  // HTTP 请求体：使用 MaxBytesReader
  r.Body = http.MaxBytesReader(w, r.Body, maxBytes)

  // 通用场景：使用 io.LimitReader
  limited := io.LimitReader(source, maxSize)
  data, _ := io.ReadAll(limited)
  ```
- **排除误判**：读取本地配置文件、已知大小的小文件通常安全
- **审查方法**：`grep -rn "io.ReadAll\|ioutil.ReadAll\|ReadAll" --include="*.go"` 逐条检查数据源

#### F4 超时配置缺失

- **问题**：Server/Client 未设超时
- **危害模式**：
  ```go
  http.ListenAndServe(":8080", handler)  // Slowloris 攻击
  client := &http.Client{}               // 永久阻塞
  ```
- **正确模式**：Server 设 ReadTimeout/WriteTimeout/IdleTimeout；Client 设 Timeout

#### F5 并发请求中的共享状态

- **问题**：包级变量在 handler 中被并发访问
- **危害模式**：
  ```go
  var buf bytes.Buffer
  func handler(w http.ResponseWriter, r *http.Request) {
      buf.Reset(); buf.WriteString(r.URL.Path)  // 并发不安全
  }
  ```
- **正确模式**：handler 内声明局部变量；`sync.Pool` 复用

---

### G类：程序生命周期与逻辑健壮性（共10项）

#### G1 优雅关闭缺失

- **问题**：进程收到 SIGTERM 后直接退出，未完成处理中的请求
- **危害模式**：`log.Fatal(http.ListenAndServe(":8080", handler))`
- **正确模式**：`signal.Notify` + `srv.Shutdown(ctx)`
- **适用范围**：所有长期运行的服务

#### G2 init() 函数副作用

- **问题**：init() 中执行重量级操作
- **危害模式**：
  ```go
  func init() {
      db, _ = sql.Open("mysql", os.Getenv("DSN"))
      db.Ping()  // DB 不可用时 panic
  }
  ```
- **正确模式**：init() 只做轻量级操作；重初始化放 Setup() 函数
- **注意**：多文件 init() 按文件名字母序执行，跨包按导入序，隐式依赖极难调试

#### G3 边界条件未处理

- **问题**：未考虑空值、零值、最大值等边界
- **危害模式**：
  ```go
  func Average(nums []int) int {
      sum := 0
      for _, n := range nums { sum += n }
      return sum / len(nums)  // 空切片除零 panic
  }
  ```
- **正确模式**：函数入口校验参数

#### G4 死循环与无界增长风险

##### G4a 死循环/重试无退出

- **问题**：循环退出条件依赖外部状态且无超时，或死循环中持续向切片 append 导致内存无界增长
- **危害模式**：
  ```go
  // 模式1：退出条件不可靠
  for {
      if getStatus() == "done" { break }
      time.Sleep(time.Second)  // 永远不 done -> 死循环
  }

  // 模式2：死循环 + append -> OOM
  for {
      data := fetchData()
      results = append(results, data)  // 内存无限增长直至 OOM
  }

  // 模式3：退出条件依赖外部输入 + append
  for !done {
      items = append(items, processItem())  // done 可能永远不为 true
  }
  ```
- **正确模式**：最大重试次数或 `context.WithTimeout`；循环内 append 必须有容量上限检查或改为流式处理
- **检测要点**：
  - `for { ... }` 或 `for true { ... }` 内包含 `append` 且缺乏退出条件
  - 退出条件依赖外部变量且循环体内有 `append`
  - 递归函数中不断向切片追加元素

##### G4b 树/图遍历无循环检测

- **问题**：遍历关系型数据结构时，如果数据中存在循环引用（如 A→B→C→A），且代码没有终止保护，会导致死循环或栈溢出/OOM
- **风险判定原则**：**无论数据来源如何（即使是内部数据库、可信 API），只要遍历关系数据结构且无终止保护，一律判定为高风险。** 数据库数据可能因业务操作错误、数据迁移、并发问题产生循环引用，一旦触发服务直接崩溃。
- **四种核心危险模式**：
  ```go
  // 模式A：递归函数无保护
  func traverse(node *Node) {
      if node == nil { return }
      for _, child := range node.Children {
          traverse(child)  // 子节点指回祖先 -> 栈溢出
      }
  }

  // 模式B：链式指针遍历无保护
  func findRoot(node *Node) *Node {
      for node.Parent != nil {
          node = node.Parent  // 循环引用 -> 永不退出
      }
      return node
  }

  // 模式C：映射遍历无保护
  func getAncestors(id int64, parentMap map[int64]int64) []int64 {
      var result []int64
      for parentMap[id] != 0 {
          id = parentMap[id]
          result = append(result, id)  // 循环引用 -> 死循环 + OOM
      }
      return result
  }

  // 模式D：BFS 队列遍历无保护
  queue := []*Node{root}
  for len(queue) > 0 {
      node := queue[0]
      queue = queue[1:]
      for _, child := range node.Children {
          queue = append(queue, child)  // 循环引用 -> queue 无限增长 -> OOM
      }
  }
  ```
- **正确模式**：添加 `visited`/`seen` map 检测循环；或设置 `maxDepth` 深度限制
  ```go
  // visited 检测示例
  func traverse(node *Node, visited map[*Node]bool) {
      if node == nil || visited[node] { return }
      visited[node] = true
      for _, child := range node.Children {
          traverse(child, visited)
      }
  }
  ```
- **检测方法（5 种结构模式，不依赖变量命名）**：

  > **核心思路**：检测**数据流自引用结构**（变量的"下一步"值来自"当前步"的派生），而非搜索 `Parent`/`Children` 等语义关键词。这样无论代码使用 `upstream`/`downstream`、`prev`/`next`、`manager`/`subordinate` 还是任何自定义命名，都能覆盖。

  | 模式 | 代码结构特征 | grep 检测命令 | 说明 |
  |------|-------------|-------------|------|
  | A-链式字段遍历 | `x = x.Field` | `grep -Pn '(\b\w+)\s*=\s*\1\.\w+' --include="*.go" -rn .` | 变量赋值为自身字段，如 `node = node.Parent`。注意：GORM 链式调用 `db = db.Where(...)` 会误命中，需人工排除 |
  | B-映射自查遍历 | `x = map[x]` | `grep -Pn '(\b\w+)\s*=\s*\w+\[\1\]' --include="*.go" -rn .` | 变量用自身做 key 查 map 再赋值给自身，如 `id = parentMap[id]` |
  | C-BFS 队列自馈 | `for len(q)>0` + `append(q,...)` | `grep -Pn 'for\s+len\(\w+\)\s*>\s*0' --include="*.go" -rn .` | 循环条件依赖队列长度且循环体向同一队列 append |
  | D-DB 反馈循环 | `for {` 内含 DB 查询且参数来自上轮结果 | `grep -n 'for true\|for {' --include="*.go" -r .` | 无限循环 + DB 查询 + 循环变量被结果字段赋值，常见于树/链式数据的逐级查询 |
  | E-递归自调用 | 函数体内调用同名函数 | 人工审查或 AST 工具 | 函数内直接或间接调用自身，需检查是否有终止条件和 visited 保护 |

  所有 grep 结果需排除 `_test.go` 和 `vendor/` 目录。

- **常见业务场景**：组织架构树、权限/菜单树、分类/目录树、评论回复链、流程审批链、上下游关系链
- **排除误判**：函数内已有 `visited`/`seen`/`depth`/`maxDepth` 等终止保护变量；GORM/builder 模式的链式调用（`db = db.Where(...)`）
- **辅助搜索命令**：
  ```bash
  # 模式A — 链式字段遍历: x = x.Field
  grep -Pn '(\b\w+)\s*=\s*\1\.\w+' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

  # 模式B — 映射自查遍历: x = map[x]
  grep -Pn '(\b\w+)\s*=\s*\w+\[\1\]' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

  # 模式C — BFS 队列自馈: for len(q) > 0
  grep -Pn 'for\s+len\(\w+\)\s*>\s*0' --include="*.go" -rn . | grep -v _test.go | grep -v vendor

  # 模式D — 无限循环 + DB 反馈
  grep -n 'for true\|for {' --include="*.go" -r . | grep -v _test.go | grep -v vendor

  # 模式E — 递归自调用（需人工或 AST 工具辅助识别）
  ```

#### G5 time.After 在循环中的内存泄漏

- **问题**：time.After 在 for-select 中每次创建新 timer，到期前无法 GC
- **危害模式**：
  ```go
  for {
      select {
      case msg := <-ch: process(msg)
      case <-time.After(5 * time.Second): return
      }
  }
  ```
- **正确模式**：循环外 `time.NewTimer`，循环内 `Stop` + `Reset`

#### G6 json 序列化/反序列化隐患

- **问题**：json tag 缺失或 omitempty 语义不符预期
- **危害模式**：
  ```go
  type User struct {
      Name string                        // 无 tag -> "Name"
      Age  int `json:"age,omitempty"`    // Age=0 也会省略
  }
  ```
- **正确模式**：对外 API 结构体显式标注 json tag；理解 omitempty 对零值影响

#### G7 time.Time 比较与时区

- **问题**：time.Time 用 == 比较因时区/单调时钟差异出错
- **危害模式**：
  ```go
  t1 := time.Now()
  t2, _ := time.Parse(time.RFC3339, t1.Format(time.RFC3339))
  t1 == t2  // false! Parse 丢弃了单调时钟
  ```
- **正确模式**：`t1.Equal(t2)`；统一 UTC

#### G8 select 语句公平性误解

- **问题**：多 case 同时就绪时 select 随机选择，非按顺序
- **危害模式**：
  ```go
  for {
      select {
      case <-ctx.Done(): return
      case data := <-dataCh: process(data)
      }
  }
  // ctx 取消后如果 dataCh 也有数据，可能不会立即退出
  ```
- **正确模式**：处理数据前再检查 `ctx.Err()`

#### G9 log.Fatal/os.Exit 在库代码中

- **问题**：库代码调用 log.Fatal 或 os.Exit 终止调用方进程，defer 不执行
- **危害模式**：
  ```go
  // 在非 main 包中
  func LoadConfig(path string) *Config {
      if err != nil { log.Fatalf("failed: %v", err) }
  }
  ```
- **正确模式**：库代码只返回 error
- **排除误判**：main.go 或 cmd/ 中的 log.Fatal 通常合理

#### G10 大对象循环内重复分配

- **问题**：循环内反复 `make` 大容量切片/map，产生大量临时内存分配，增加 GC 压力，极端情况下可能触发 OOM
- **危害模式**：
  ```go
  for i := 0; i < n; i++ {
      buf := make([]byte, 1024*1024)  // 每次分配 1MB
      process(buf)
  }
  ```
- **正确模式**：
  ```go
  // 方案1：预分配复用
  buf := make([]byte, 1024*1024)
  for i := 0; i < n; i++ {
      process(buf)
  }

  // 方案2：sync.Pool 复用
  var pool = sync.Pool{New: func() interface{} { return make([]byte, 1024*1024) }}
  for i := 0; i < n; i++ {
      buf := pool.Get().([]byte)
      process(buf)
      pool.Put(buf)
  }
  ```
- **排除误判**：循环次数有限且分配量不大时通常无风险

---

## 输出格式

审查完成后，生成 Markdown 报告，包含以下部分：

### 报告结构

1. **概览**：扫描文件数、代码行数、Go 版本、问题总数及风险分布
2. **风险统计表**：7 类别 x 3 风险等级的矩阵
3. **详细发现**：按风险等级分组，每个问题包含：
   - 编号和检查项名称
   - 文件路径和行号
   - 问题描述
   - 风险等级
   - 问题代码（含文件名行号）
   - 修复建议（可编译代码）
   - 关联问题（跨文件时标注所有位置）
4. **修复优先级**：P0 立即修复 | P1 本迭代 | P2 后续优化
5. **架构级建议**：系统性问题汇总
6. **审查排除项**：排除的文件清单和确认非问题的疑似发现

### 风险等级标准

| 等级 | 条件 | 示例 |
|------|------|------|
| 高 | 崩溃(panic/fatal)、数据丢失、安全漏洞 | 数据竞争、并发map(fatal)、SQL注入、goroutine泄漏、nil指针、channel panic |
| 中 | 非预期行为、资源耗尽、排查困难 | 错误丢失、资源未关闭、类型断言未检查、超时缺失、context未传递 |
| 低 | 代码质量、可维护性 | 边界未处理、interface{}使用、错误未包装、json tag缺失 |

---

## 重要约束

1. **不要遗漏文件** -- 每个 .go 文件都必须扫描，结束后列出文件清单
2. **不要误报** -- 不确定的标注 `[需人工确认]` 并说明原因
3. **给出具体行号** -- 每个发现定位到文件和行号
4. **给出可用的修复代码** -- 需能编译通过，可直接应用
5. **标注交叉关联** -- 涉及多文件的标注所有相关位置
6. **Go 版本感知** -- 先读 go.mod：A4(1.22+修复) | A8(1.19+atomic类型) | D5(1.18+泛型) | D6(1.21+slices) | E6(1.20+自动种子)
7. **跳过测试文件** -- _test.go 降低优先级，并发测试问题仍需标注
8. **跳过第三方代码** -- vendor/、*.pb.go、*_gen.go、*_mock.go 排除
9. **大仓库分批** -- 超过100个文件时分批输出，每批不超过15个发现
10. **区分 fatal 和 panic** -- 并发 map 的 fatal 无法 recover，报告中明确标注