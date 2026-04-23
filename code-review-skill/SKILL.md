---
name: code-review-skill
description: |
  高效、建设性的代码评审技能，支持多种编程语言。
  触发场景：评审指定 commit、评审当前分支代码差异、建立评审标准、执行规范检查。
---

# 代码评审卓越指南

对代码进行系统化评审，发现 bug、提升质量、促进团队知识共享。

## ⚠️ 重要：技能启动第一步（必须遵守）

**当此技能被触发时，你必须立即执行以下操作，不得跳过或询问用户：**

**第 0 步：识别项目技术栈**

以下路径均相对于本 SKILL.md 所在目录，执行时请基于该目录解析路径。

检查项目配置文件，确认技术栈并记录主要框架及版本（详细规则见 [core/process.md](core/process.md) 阶段 1）：
- 前端项目 → 读取项目根目录的 `package.json`，记录主框架（san/vue/react）及版本、构建工具（webpack/vite）及版本、TypeScript 版本、CSS 方案（less/sass/tailwind 等）
- Go 项目 → 检查 `go.mod`，记录 Go 版本及主要依赖版本
- Java 项目 → 检查 `pom.xml` 或 `build.gradle`，记录 Java 版本及主要依赖版本

收集到的技术栈和版本信息作为后续评审的上下文，用于判断规则适用性（如框架版本是否支持某语法、是否使用了 Tailwind 等）。

**第 0.5 步：校验并安装语言专属 CR Tool 依赖（必须）**

根据第 0 步识别到的技术栈，执行对应语言目录下的 `pre-install.sh`：

```bash
# San.js 项目
bash languages/sanjs/pre-install.sh

# React 项目
bash languages/react/pre-install.sh

# 其他语言项目（暂无对应 pre-install，跳过此步）
```

- `pre-install.sh` 会先校验依赖，缺失时自动安装到项目本地包
- 统一 npm 源：`registry=http://registry.npm.baidu-int.com`
- 若当前技术栈无对应语言目录（如 Go、Java），跳过此步骤，继续后续流程

**第 1 步：判断用户是否指定了 commit：**
- 如果用户明确指定了 commit（如 `cr abc1234`、`评审 abc1234 def5678`），将 commit 作为参数传入脚本
- 如果用户未指定 commit，不传参数，让脚本自动从 `$AGILE_COMMENTS` 或 fallback 获取

```bash
# 场景 1: 用户指定了 commit（支持一个或多个）
bash core/scripts/collect-changes.sh <commit1> [commit2...]

# 场景 2: 用户未指定 commit（自动从环境变量或 fallback 获取）
bash core/scripts/collect-changes.sh
```

**禁止的行为：**
- ❌ 不要提前运行 `git status` 来判断是否有变更
- ❌ 不要检查环境变量 `$AGILE_COMMENTS` 是否存在
- ❌ 不要在用户已指定 commit 时仍询问"要评审什么代码"
- ❌ 不要因为工作目录干净就停止流程

**commit 获取优先级（脚本自动处理）：**
1. ✅ **命令行参数**：用户明确指定的 commit（最高优先级）
2. ✅ **环境变量 `$AGILE_COMMENTS`**：CI/PR 场景自动注入的 commit 列表
3. ✅ **兜底策略**：自动评审最新的 commit

**只有在脚本执行失败时才询问用户。**

## 支持的语言

- **San.js**: [查看详情](languages/sanjs/)
- **React**: [查看详情](languages/react/)

## 使用场景

- **手动指定 commit 评审**：用户直接告诉要评审哪些 commit（如 `cr abc1234`、`评审 abc1234 def5678`）
- **CI/PR 自动评审**：从环境变量 `$AGILE_COMMENTS` 获取 commit 列表，评审这些 commit 的代码变更
  - `$AGILE_COMMENTS` 格式: `[{"Commit":"e5ba5cb","author":"username","comment":"feat: xxx","committer":"username"}]`
- **兜底策略**：当未指定 commit 且 `$AGILE_COMMENTS` 未设置时，自动评审最新的一个 commit（不需要询问用户）
- 评审内容：指定 commits 的完整代码差异
- 建立团队代码评审标准
- 指导初级开发者进行评审
- 进行架构设计评审
- 提升代码质量和一致性

## 核心评审流程

详细的评审流程见：**[core/process.md](core/process.md)**

评审流程包含 5 个阶段：

1. **阶段 1: 收集上下文** - 获取变更信息，确认评审范围，通过 `metadata.inherits` 加载对应的 checklist 文件
2. **阶段 2: 高层设计评审** - 评估整体架构和设计
3. **阶段 3: 逐行代码评审** - 按 P0 → P1 → P2 → P3 顺序执行所有已加载 checklist 的检查项，**同一问题只记录最高优先级规则**。
4. **阶段 4: 总结与决策** - 提供清晰的评审结论
5. **阶段 5: 输出评审报告** - 生成中文评审报告文件，使用阶段3已记录的规则ID

**关键要点：**
- ✅ **支持用户直接指定 commit**：将 commit 作为命令行参数传入脚本
- ✅ 从环境变量 `$AGILE_COMMENTS` 获取 commit 列表；**若未设置，自动使用最新的 commit（不询问用户）**
- ✅ 使用 `git show` 或 `git diff` 获取指定 commits 的代码差异
- ✅ 支持单个或多个 commit 的评审
- ✅ **禁止在调用 `collect-changes.sh` 前询问用户**：直接运行脚本，让脚本的兜底逻辑自动生效

### ⚠️ 输出规则（必须严格遵守）

**评审完成后必须按顺序执行以下工具调用，不得跳过或自行拼接内容：**

1. **第一步：生成 HTML 报告**
   ```
   使用 Read 工具读取: core/templates/html-report.template.html
   → 替换所有 {{占位符}} 为实际内容（规则ID使用阶段3已记录的值）
   → 使用 Write 工具输出: code-review-result.html（项目根目录）
   ```

2. **第二步：输出控制台摘要**
   ```
   使用 Read 工具读取: core/templates/console-output.template.sh
   → 替换所有 {{占位符}} 为实际内容
   → 使用 Shell 工具执行替换后的 bash 脚本
   ```

**🚫 严禁：** ❌ 不使用 Read 工具读取模板 ❌ 自行编写输出格式 ❌ 修改模板结构  
**💡 原因：** 使用 Shell 输出确保非交互模式（`-p` 参数）下用户也能看到评审结果。

**详细说明和占位符定义见 [core/templates.md](core/templates.md)**

## 评审范围

**无需评审（工具自动处理）：** 格式化（Prettier）、Import 整理、Lint 违规（ESLint）、简单拼写错误

## 评审报告模板

详细的占位符定义见：**[core/templates.md](core/templates.md)**

模板文件位于 `core/templates/` 目录：
- `console-output.template.sh` - 控制台输出模板
- `html-report.template.html` - HTML 评审报告模板
