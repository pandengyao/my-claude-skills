---
name: prd-to-tech-design
description: 将 PRD 转换为技术设计文档。触发场景：(1) 用户提供知识库链接(ku.baidu-int.com)要求技术设计 (2) 用户提供 PRD 文档并要求技术设计/架构设计/实现方案 (3) 用户说"编写技术设计"、"生成技术规格"、"PRD转设计"、"设计接口"等。重要：检测到 ku.baidu-int.com 链接时必须使用 query_ku_doc.py 获取内容，禁止用 WebFetch 或 playwright。
---

# PRD 转技术设计文档

将 PRD 转换为完整的技术设计文档。

**交流语言: 必须使用中文与用户交流。**

## 技能触发后的第一步操作

**立即判断 PRD 来源类型并执行对应操作：**

### 类型 A: 知识库链接 (ku.baidu-int.com)

**立即执行以下脚本获取文档：**

```bash
~/py312/bin/python3 ~/.claude/skills/prd-to-tech-design/scripts/query_ku_doc.py \
  --url "https://ku.baidu-int.com/knowledge/xxx/DOC_ID" \
  --output tech_design/{需求名称}/source_prd/PRD-原始.md
```

**⚠️ 禁止使用 WebFetch 或 playwright 访问知识库链接，必须使用上述脚本**

获取成功后，继续执行"标准工作流程"。

### 类型 B: 本地文档路径

直接使用 Read 工具读取文档内容，然后继续执行"标准工作流程"。

### 类型 C: 用户直接提供内容

直接继续执行"标准工作流程"。

---

## 标准工作流程

| 步骤 | 关键操作 | 输出 |
|------|----------|------|
| 1. 理解 PRD | 读取文档、下载图片、生成优化版 PRD | `tech_design/{需求名称}/PRD-优化版.md` |
| 2. 证据扫描 | 扫描现有实现,识别可复用能力与冲突 | 现状证据清单 |
| 3. 技术分析 | 分析架构、数据、接口、安全、性能 | 技术要点清单 |
| 4. 识别不确定性 | 向用户澄清技术未知点(每次 1-2 个问题) | 参考资料 |
| 5. 编写设计 | 按模板填充,严格遵循 PRD | 技术设计文档各章节 |
| 6. 自主完善 | 补充标准设计元素 | 完整设计文档 |
| 7. 添加参考信息 | 记录所有参考资料链接和路径 | 可追溯文档 |
| 8. PRD 对照 Review | 检查是否覆盖所有需求 | 最终文档 |

### 第一步: 理解 PRD

**详细指南**: 参考 `references/prd-processing-guide.md`

1. **读取 PRD 内容**: 知识库链接已在触发后处理，本地文档直接读取
2. **下载图片**: 使用内置脚本下载内网图片
   ```bash
   ~/py312/bin/python3 ~/.claude/skills/prd-to-tech-design/scripts/download_images.py \
     --json tech_design/{需求名称}/source_prd/ku-content.json \
     --output tech_design/{需求名称}/prd_assets/
   ```
3. **生成优化版 PRD**: 保留原文信息,优化格式,图片本地化

### 第二步: 证据扫描

**目标**: 了解现有实现,避免重复设计或冲突。

**扫描范围**: 仅扫描 PRD 相关模块,包括前端组件、后端 API、数据库表、第三方集成。

**证据清单格式:**
| 能力点 | 证据路径 | 当前实现 | 缺口/冲突 | 影响范围 |
|--------|----------|----------|-----------|----------|

**关键原则:**
- 证据不清晰时立即停止,向用户澄清(每次 1-2 个问题)
- 禁止基于局部代码片段推断完整机制

### 第三步: 技术方案分析

**详细指南**: 参考 `references/technical-analysis-guide.md`

基于 PRD 和证据扫描结果,分析:架构设计、数据设计、接口设计、安全性、性能、可观测性。

### 第四步: 识别技术不确定性

**关键原则**: 不要盲目假设,向用户请求明确的参考信息。

**必须询问用户的情况:**
- 现有系统的具体实现机制
- 技术选型的可行性
- 业务规则的具体定义
- 架构决策、性能指标、安全规范

**应该自主补充的内容:**
- 标准错误处理、日志设计、监控指标
- 数据校验规则、接口标准参数
- 数据库标准字段、安全防护措施
- 性能优化方案、测试方案

**沟通原则:**
- 每次只问 1-2 个清晰问题
- 问题要具体明确,易于回答
- 用户提到的文档直接读取,无需再次确认

### 第五步: 编写技术设计文档

**模板**: `references/tech-design-template.md`

**章节结构:**
1. 概要 - 背景、功能目标、非功能目标、方案要点
2. 意义 - 业务/技术/用户价值
3. 竞品对照 - 无则写"暂无"
4. 设计思路与实现方案 - 架构、关键点设计、API 文档、数据库设计
5. 影响和风险总结
6. 规划排期 - 按模块拆分,估算工作量
7. 待确认问题
8. 评审意见

**接口设计要求**: 参考 `references/api-protocol-guide.md`,必须包含业务上下文、依赖关系、测试要点。

### 第六步: 自主完善设计文档

**检查清单**: 参考 `references/standard-design-elements.md`

系统性地补充:错误处理、日志记录、监控指标、数据校验、安全防护、性能优化、测试方案、运维部署。

### 第七步: 添加参考信息

在文档末尾记录所有参考资料:
- PRD 文档:原始路径、知识库链接、优化版路径
- 技术文档:官方文档、第三方服务文档
- 代码参考:关键文件路径
- 用户提供的资料

### 第八步: PRD 对照 Review

**检查项:**
- [ ] PRD 每个功能点是否都在设计中体现?
- [ ] 业务规则理解是否正确?
- [ ] 非功能需求(性能/安全/可用性)是否覆盖?

**发现问题:** 遗漏则补充,偏离则在"待确认问题"说明。

## 输出文件

```
tech_design/
└── {需求名称}/
    ├── PRD-优化版.md          # 优化版 PRD
    ├── 技术设计-{功能名称}.md  # 技术设计文档
    └── prd_assets/            # PRD 图片资源
```

## 参考资料

- PRD 处理指南: `references/prd-processing-guide.md`
- 技术设计模板: `references/tech-design-template.md`
- 接口协议指南: `references/api-protocol-guide.md`
- 标准设计元素: `references/standard-design-elements.md`
- 技术分析指南: `references/technical-analysis-guide.md`
- 沟通指南: `references/communication-guidelines.md`
- 项目安全规范: 项目根目录 `CLAUDE.md`

## 内置脚本

| 脚本 | 用途 |
|------|------|
| `scripts/query_ku_doc.py` | 获取知识库文档内容 |
| `scripts/download_images.py` | 下载 PRD 中的内网图片 |