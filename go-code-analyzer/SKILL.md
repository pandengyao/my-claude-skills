--- 
name: go-code-analyzer
description: |
  Go 代码深度分析工具，提供 41 项检查能力，涵盖安全漏洞、内存管理、并发性能、
  I/O优化（含Redis/etcd/ClickHouse）、数据结构、编译器优化等领域。
  适用于 Go 项目的代码审查、性能调优和上线前检查。
---

# Go 代码深度分析器 v2.1

## 功能概述

本 Skill 提供 Go 代码的全面分析能力，涵盖 **8 大领域、41 项检查**。**所有分析仅提供诊断报告和优化建议，不会自动修改代码**。

---

## 一、安全检测（3 项）

### 1. 安全漏洞检测
- SQL 注入、命令注入、路径遍历
- 不安全的随机数、硬编码敏感信息
- 不安全的 HTTP/TLS 配置

### 2. unsafe 使用分析
- `unsafe.Pointer` 使用场景评估
- 是否有更安全的替代方案

### 3. CGO 安全分析
- CGO 调用的安全风险
- 内存管理问题

---

## 二、内存管理（6 项）

### 4. 内存逃逸分析
- 识别逃逸到堆的变量
- 分析逃逸原因和影响

### 5. 内存泄漏检测
- 未关闭的资源（文件、连接、通道）
- goroutine 泄漏、Timer/Ticker 泄漏

### 6. 大内存消耗分析
- 大对象分配、切片预分配
- 字符串拼接优化

### 7. 内存分配评估
- 循环内分配、对象池建议
- 值类型 vs 指针选择

### 8. 结构体字段对齐
- 字段顺序导致的内存浪费（padding）
- 最优字段排列建议

### 9. GC 压力分析
- 对象分配速率评估
- 短生命周期对象识别
- Finalizer 使用风险

---

## 三、并发性能（6 项）

### 10. 原子操作分析
- 锁粒度、Mutex/RWMutex 选择
- 锁竞争检测

### 11. Goroutine 管理
- 无限制创建 goroutine 检测
- Worker Pool 使用建议

### 12. Channel 分析
- 缓冲区大小合理性
- 无缓冲 vs 有缓冲选择

### 13. Context 使用分析
- `context.Value` 性能问题
- Context 传递完整性

### 14. 调度延迟分析
- 长时间占用 P 的 goroutine
- `runtime.Gosched()` 使用

### 15. 竞态检测
- 数据竞争风险识别
- `go build -race` 结果分析

---

## 四、I/O 与网络（7 项）

### 16. HTTP 客户端优化
- `http.Client` 复用检查
- 连接池配置、超时设置

### 17. 数据库优化
- 连接池配置
- N+1 查询问题
- 预编译语句使用

### 18. 文件 I/O 优化
- `bufio` 使用建议
- 批量读写优化

### 19. JSON 序列化优化
- 标准库 vs 高性能库对比
- 流式处理建议

### 20. Redis 优化分析
- 连接池配置
- Pipeline 批量操作
- 大 Key / 热点 Key 检测
- Lua 脚本缓存

### 21. etcd 优化分析
- 客户端配置检查
- Watch 泄漏检测
- 租约续期管理
- 事务批量操作

### 22. ClickVisual/ClickHouse 优化
- 连接池配置
- 批量写入优化
- 查询索引使用
- 日志采集缓冲

---

## 五、数据结构优化（4 项）

### 23. 切片优化
- 预分配容量
- 切片 vs 数组选择

### 24. Map 优化
- 预分配大小
- 大 Map 迭代优化

### 25. 字符串优化
- `string ↔ []byte` 转换开销
- `strings.Builder` 使用

### 26. range 复制分析
- 大结构体复制检测
- 指针遍历建议

---

## 六、代码模式优化（6 项）

### 27. 反射使用检测
- `reflect` 包使用场景
- 性能影响评估

### 28. 接口装箱分析
- `interface{}` 装箱开销
- 泛型替代建议

### 29. defer 开销分析
- 循环内 defer
- 热点函数 defer 累积

### 30. 内联失败分析
- 函数无法内联的原因
- 优化建议

### 31. 正则表达式检测
- 循环内编译检测
- 预编译建议

### 32. 错误处理优化
- `fmt.Errorf` vs `errors.New`
- 错误包装层数

---

## 七、编译器优化（4 项）

### 33. 边界检查消除
- BCE 分析
- 手动消除建议

### 34. 编译器指令分析
- `//go:noinline` 等指令使用
- 适用场景评估

### 35. 栈增长分析
- 大栈帧函数识别
- 栈分裂风险

### 36. 汇编函数分析
- 手写汇编评估
- 可移植性影响

---

## 八、测试与监控（5 项）

### 37. Benchmark 完整性
- 关键函数覆盖率
- 测试准确性检查

### 38. pprof 配置检查
- HTTP 端点配置
- 自定义 metric 覆盖

### 39. 热点路径识别
- 高频调用路径分析
- 优化优先级建议

### 40. 日志性能分析
- 日志级别检查
- 结构化日志建议

### 41. 零值初始化检测
- 冗余零值初始化
- 代码简化建议

## 使用方式

### 完整分析
```
请使用 go-code-analyzer 对整个项目进行完整的代码分析
```

### 按领域分析

#### 一、安全检测
```
请使用 go-code-analyzer 检查项目中的安全漏洞
请使用 go-code-analyzer 分析 unsafe 包的使用情况
请使用 go-code-analyzer 检查 CGO 调用的安全性
```

#### 二、内存管理
```
请使用 go-code-analyzer 分析代码的内存逃逸问题
请使用 go-code-analyzer 检测可能的内存泄漏
请使用 go-code-analyzer 分析大内存消耗问题
请使用 go-code-analyzer 评估内存分配合理性
请使用 go-code-analyzer 检查结构体字段对齐
请使用 go-code-analyzer 分析 GC 压力
```

#### 三、并发性能
```
请使用 go-code-analyzer 分析原子操作和锁的使用
请使用 go-code-analyzer 检查 Goroutine 管理问题
请使用 go-code-analyzer 分析 Channel 使用情况
请使用 go-code-analyzer 检查 Context 使用是否正确
请使用 go-code-analyzer 分析调度延迟问题
请使用 go-code-analyzer 进行竞态检测
```

#### 四、I/O 与网络
```
请使用 go-code-analyzer 检查 HTTP 客户端配置
请使用 go-code-analyzer 分析数据库连接池配置
请使用 go-code-analyzer 检查文件 I/O 优化机会
请使用 go-code-analyzer 分析 JSON 序列化性能
请使用 go-code-analyzer 分析 Redis 使用优化
请使用 go-code-analyzer 分析 etcd 使用优化
请使用 go-code-analyzer 分析 ClickVisual/ClickHouse 优化
```

#### 五、数据结构优化
```
请使用 go-code-analyzer 检查切片预分配
请使用 go-code-analyzer 分析 Map 使用优化
请使用 go-code-analyzer 检查字符串处理性能
请使用 go-code-analyzer 分析 range 复制问题
```

#### 六、代码模式优化
```
请使用 go-code-analyzer 检测反射使用情况
请使用 go-code-analyzer 分析接口装箱开销
请使用 go-code-analyzer 检查 defer 使用开销
请使用 go-code-analyzer 分析内联失败情况
请使用 go-code-analyzer 检查正则表达式预编译
请使用 go-code-analyzer 分析错误处理性能
```

#### 七、编译器优化
```
请使用 go-code-analyzer 分析边界检查消除
请使用 go-code-analyzer 检查编译器指令使用
请使用 go-code-analyzer 分析栈增长问题
请使用 go-code-analyzer 检查汇编函数使用
```

#### 八、测试与监控
```
请使用 go-code-analyzer 检查 Benchmark 覆盖率
请使用 go-code-analyzer 检查 pprof 配置
请使用 go-code-analyzer 识别热点路径
请使用 go-code-analyzer 分析日志性能
请使用 go-code-analyzer 检查零值初始化
```

### 指定文件/目录分析
```
请使用 go-code-analyzer 分析 vendor_local/gatus/storage/store/sql/sql.go 文件的内存问题
请使用 go-code-analyzer 分析 vendor_local/gatus/watchdog/ 目录的并发问题
请使用 go-code-analyzer 检查 api/yaml.go 的性能问题
```

## 分析流程

详细的分析方法请参考以下文档：

### 安全检测
- 安全漏洞检测：`docs/security-check.md`

### 内存管理
- 内存逃逸分析：`docs/escape-analysis.md`
- 内存泄漏检测：`docs/memory-leak.md`
- 大内存消耗：`docs/memory-consumption.md`
- 内存分配评估：`docs/allocation-analysis.md`
- 结构体对齐：`docs/struct-alignment.md`
- GC 压力分析：`docs/gc-pressure.md`

### 并发性能
- 原子操作分析：`docs/atomic-analysis.md`
- Goroutine 管理：`docs/goroutine-management.md`
- Channel 分析：`docs/channel-analysis.md`
- Context 分析：`docs/context-analysis.md`

### I/O 与网络
- HTTP 优化：`docs/http-optimization.md`
- 数据库优化：`docs/database-optimization.md`
- JSON 优化：`docs/json-optimization.md`
- Redis 优化：`docs/redis-optimization.md`
- etcd 优化：`docs/etcd-optimization.md`
- ClickVisual/ClickHouse 优化：`docs/clickvisual-optimization.md`

### 代码模式
- 反射检测：`docs/reflect-analysis.md`
- 接口装箱：`docs/interface-boxing.md`
- defer 分析：`docs/defer-analysis.md`
- 内联分析：`docs/inline-analysis.md`
- 正则检测：`docs/regex-analysis.md`
- range 复制：`docs/range-copy-analysis.md`

### 测试监控
- Benchmark 检查：`docs/benchmark-analysis.md`

## 输出报告格式

每项分析将输出以下内容：

```
## [分析类型] 分析报告

### 问题汇总
| 严重程度 | 数量 |
|----------|------|
| 🔴 高    | N    |
| 🟡 中    | N    |
| 🟢 低    | N    |

### 详细问题列表

#### 问题 1：[问题标题]
- **文件位置**：path/to/file.go:行号
- **严重程度**：🔴 高 / ?? 中 / 🟢 低
- **问题描述**：具体问题说明
- **相关代码**：
  ```go
  // 问题代码片段
  ```
- **优化建议**：具体的改进方案
- **参考资料**：相关文档链接

### 总结与建议
整体评估和优先处理建议
```

## 重要说明

⚠️ **本 Skill 仅进行分析和提供建议，不会自动修改任何代码**

所有优化建议需要开发者审核后手动实施，这样做的原因：
1. 优化方案可能需要结合业务逻辑判断
2. 某些优化可能涉及架构调整
3. 保证代码变更的可控性和可追溯性

## 依赖工具

分析过程中可能使用以下 Go 工具：
- `go build -gcflags="-m"` - 逃逸分析
- `go vet` - 静态检查
- `staticcheck` - 高级静态分析（如已安装）
- `golangci-lint` - 综合检查（如已安装）

## 适用场景

- 代码审查（Code Review）
- 性能优化前的诊断
- 上线前的安全检查
- 定期代码质量评估
- 新成员代码学习