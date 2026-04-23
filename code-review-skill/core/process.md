# 代码评审流程

本文档详细说明了代码评审的 5 个阶段流程。

## 阶段 1: 收集上下文

在开始评审前，先获取变更信息和上下文：

### 1.1 检查项目技术栈

**在执行任何评审之前，必须先确认项目技术栈：**

**技术栈识别步骤：**

1. **检查项目文件和配置**
   - 前端项目: 读取 `package.json`
   - Go 项目: 检查 `go.mod` 文件
   - Java 项目: 检查 `pom.xml` 或 `build.gradle` 文件

2. **技术栈识别规则：**

   **前端项目 (检查 package.json):**
   - 包含 `san` 依赖 → San.js 项目
   - 包含 `vue` 依赖 → Vue.js 项目
   - 包含 `react` 依赖 → React.js 项目
   - 包含 `typescript` 或存在 `tsconfig.json` → TypeScript

   **后端项目:**
   - 存在 `go.mod` → Go 项目
   - 存在 `pom.xml` 或 `build.gradle` → Java 项目

3. **匹配评审指南（预定义文件夹名称）：**
   - San.js → `languages/sanjs/`
   - 其他技术栈 → 使用通用评审原则

4. **执行语言专属 CR Tool 依赖校验：**
   - San.js → `bash languages/sanjs/pre-install.sh`
   - 其他技术栈（暂无对应 pre-install）→ 跳过此步骤
   - `pre-install.sh` 会先校验依赖，缺失时按语言约定自动安装所需工具

5. **加载对应的检查清单：**
   - 读取语言特定的 checklist 文件（如 `languages/sanjs/checklist.yaml`）
   - 解析其 `metadata.inherits` 字段，按数组声明顺序依次加载依赖的 checklist
   - 最后加载当前文件自身的规则，形成完整的评审标准

**输出示例：**
```markdown
📋 技术栈识别结果：
- 技术栈: San.js + TypeScript
- 主要依赖: san (^3.13.0), @baidu/cosmic (^2.1.0)
- 评审指南: ✅ languages/sanjs/
```

或

```markdown
📋 技术栈识别结果：
- 技术栈: Go
- Go版本: 1.21
- 评审指南: ⚠️  未找到对应指南，使用通用评审原则
```

### 1.2 收集代码变更信息

**使用收集脚本:**

项目提供了 `collect-changes.sh` 脚本来自动收集代码变更信息:

```bash
# 场景 1: 用户指定了 commit（支持一个或多个）
bash scripts/collect-changes.sh <commit1> [commit2...]

# 场景 2: 未指定 commit，自动从 $AGILE_COMMENTS 或 fallback 获取
bash scripts/collect-changes.sh
```

**commit 获取优先级（脚本自动处理）：**
1. **命令行参数**：用户明确指定的 commit（最高优先级）
2. **环境变量 `$AGILE_COMMENTS`**：CI/PR 场景自动注入的 commit 列表
3. **兜底策略**：自动使用最新的一个 commit

**脚本功能:**
1. 查看当前 Git 状态
2. 按优先级获取 commit 列表（命令行参数 > `$AGILE_COMMENTS` > 最新 commit）
3. 验证 commit 是否存在（命令行参数模式会校验）
4. 获取每个 commit 的信息
5. 显示所有 commits 的变更摘要
6. 提供完整差异查看命令
7. 导出环境变量供后续使用 (COMMIT_IDS, FIRST_COMMIT, LAST_COMMIT, COMMIT_COUNT)

**🚨 读取脚本输出的强制规则：**
- ✅ **只读一次**：脚本输出结果只能读取一次，读完即进入下一阶段，禁止重复读取同一文件
- ✅ **超大输出处理**：若输出超过 2000 行，使用 `limit=2000` 读取前半段，再用 `offset` 读取后半段，每个区段只读一次
- ❌ **禁止循环读取**：禁止因"内容不够"而反复读取同一文件，如变更过大（>500行 diff）应在概览阶段标注"变更规模较大"，不影响评审继续进行

**理解上下文：**
```markdown
1. 理解变更目的（修复 bug？新功能？重构？）
2. 检查变更规模（>400 行？建议拆分）
3. 了解业务需求（解决什么问题？）
4. 注意相关架构决策（符合现有设计吗？）
```

**重要提示：**
- ✅ **用户指定了 commit 时，将其作为命令行参数传入脚本**
- ✅ **用户未指定时，直接运行脚本（不带参数），不要提前检查 `$AGILE_COMMENTS`**
- ✅ **脚本会自动处理优先级：命令行参数 > 环境变量 > 最新 commit**
- ✅ **`$AGILE_COMMENTS` 格式示例: `[{"Commit":"e5ba5cb","author":"username","comment":"feat: xxx","committer":"username"}]`**
- ✅ **使用 `git show $COMMIT` 或 `git diff $FIRST_COMMIT^..$LAST_COMMIT` 获取差异**
- ✅ **支持单个或多个 commit 的评审**
- ❌ **不要硬编码 commit ID，必须从脚本导出的环境变量获取**

## 阶段 2: 高层设计评审

先评估整体设计，再关注细节：

1. **架构与设计**
   - 解决方案是否匹配问题？有更简单的方法吗？
   - 与现有模式一致吗？能扩展吗？
   - 大型功能是否有设计文档？是否应分阶段提交（核心抽象 → 实现 → 集成测试）？

2. **文件组织**
   - 新文件放对地方了吗？代码分组合理吗？有重复文件吗？

## 阶段 3: 逐行代码评审

**准备工作：加载检查清单**

在开始逐行评审前，需要加载对应的检查清单配置：

1. 根据阶段1识别的技术栈，找到对应的语言 checklist 文件
   - San.js → `languages/sanjs/checklist.yaml`
   - Vue.js → `languages/vue/checklist.yaml`（如果存在）
   - 其他 → 使用 `core/checklists/checklist-common.yaml`

2. 读取该 checklist 文件的 `metadata` 字段：
   ```yaml
   metadata:
     language: SanJS
     inherits:
       - ../../core/checklists/checklist-common.yaml
       - ../../core/checklists/checklist-fe.yaml
   ```

3. 按 inherits 数组声明的顺序依次加载依赖的 checklist，最后加载当前文件自身规则

多个 checklist 文件的规则**互补使用**，共同构成完整的评审标准。

**🚨 严格分级执行（必须遵守）：**

评审必须严格按照以下优先级顺序进行，每个级别完成后再进入下一级别：

1. **第一轮：P0 级别检查（🔴 critical）** - 从已加载的所有 checklist 文件读取 `p0_*` 分组的检查项，逐项检查代码变更
2. **第二轮：P1 级别检查（🟡 major）** - 从已加载的所有 checklist 文件读取 `p1_*` 分组的检查项，逐项检查代码变更
3. **第三轮：P2 级别检查（🟢 minor）** - 从已加载的所有 checklist 文件读取 `p2_*` 分组的检查项，逐项检查代码变更
4. **第四轮：P3 级别检查（💡 nit）** - 从已加载的所有 checklist 文件读取 `p3_*` 分组的检查项，逐项检查代码变更

**⚠️ 同一问题只记录最高优先级（去重原则）：**

如果同一个代码问题可以匹配多个优先级的规则，**只记录最高优先级的规则**，避免重复上报：
- 例如：某段代码同时违反 P0 和 P2 规则 → 只记录 P0 规则
- 原因：高优先级规则已经覆盖了问题，无需重复记录

**🚨 发现问题时必须同时记录规则ID和精确行号（核心要求）：**

评审过程中，当检查某个规则并发现问题时，**必须立即将问题和该规则的 `id` 绑定记录，同时记录精确的代码行号**：

```
检查规则: p0-use-cosmic-tokens
↓ 发现问题
记录: { 规则ID: "p0-use-cosmic-tokens", 文件: "src/style.less", 行号: 42, 问题描述: "xxx" }
```

**⚠️ 行号直接从 diff 输出的前缀读取，无需手动计算：**

`collect-changes.sh` 脚本已在每行前标注新文件行号（`+` 侧），格式如下：

```
[hunk   ] @@ -850,8 +850,8 @@
[L:850  ]  context line
[L:851  ]  context line
[del    ] -catch (e) { console.log(e) }   ← 已删除行，在新文件中不存在
[L:852  ] +catch (e) { /* fixed */ }       ← 新增行，新文件第 852 行
[L:853  ]  context line
[meta   ] diff --git a/src/foo.ts b/src/foo.ts
```

**行号使用规则：**
- `[L:行号]` 前缀的行 → 直接使用该行号作为问题行号（对应修改后新文件的行号）
- `[del   ]` 前缀的行（已删除行）→ 该行在新文件中已不存在，若问题在此，使用最近上下文的 `[L:行号]` 行号作为参考
- 禁止手动推算，禁止使用 hunk header 中的数字

**⚠️ 位置格式必须严格为 `文件路径:行号`，不得附加任何括号说明或描述文字。**

**示例：**
- 检查 `p0-use-cosmic-tokens` 规则 → 发现硬编码颜色值 → 记录问题，规则ID 为 `p0-use-cosmic-tokens`
- 检查 `p1-naming-semantic` 规则 → 发现变量命名不清晰 → 记录问题，规则ID 为 `p1-naming-semantic`

**🚨 问题等级由规则ID前缀决定（输出报告时必须遵守）：**
- `p0-xxx` 规则ID → 必须放入 **P0 严重问题** 列表
- `p1-xxx` 规则ID → 必须放入 **P1 主要问题** 列表
- `p2-xxx` 规则ID → 必须放入 **P2 小问题** 列表
- `p3-xxx` 规则ID → 必须放入 **P3 建议** 列表

**⚠️ 禁止的行为：**
- ❌ 发现问题后自己编造一个规则ID（如 `p2-cosmic-token`）
- ✅ 只使用触发该检查的规则的原始 `id` 字段值，并按前缀分类到对应等级

**🚨 验证工具使用规则：**

当检查项配置了 `cr_tool` 字段时，必须按工具类型执行验证：
1. 文档工具（如 `san-doc`）→ 调用对应文档查询能力
2. 脚本工具（如 `cosmic_token_check.sh`）→ 调用统一脚本：
   - `bash scripts/cosmic_token_check.sh "<file:line1,line2;file:line3>"`
   - 必须传 `file:lines`
   - 脚本内部通过 `npx cosmic token check` 执行校验，并完成平台识别
3. 禁止凭经验猜测 token 名称或组件属性名
4. 使用工具返回的准确结果，不得修改

**示例**：发现硬编码颜色 `color: #333333`
- ❌ 错误：未执行脚本，直接猜测使用 `--cos-color-text-primary`
- ✅ 正确：执行 `cosmic_token_check.sh`，仅输出 1 条 `p0-use-cosmic-tokens` 问题，并在该问题下按 `results[]` 做文件分块；每个分块展示 `file:lines` 与 `issue_points`（包含问题与可修复建议）

## 阶段 4: 总结与决策

总结关键问题（按优先级），明确决策：✅ 批准合并 / 💬 仅评论（不阻塞）/ 🔄 请求修改（必须解决后重新评审）

## 阶段 5: 输出评审报告（必须执行）

**🚨🚨🚨 强制要求：评审完成后必须按顺序输出两部分内容，缺一不可！🚨🚨🚨**

**执行顺序（必须严格遵守）：**
1. **第一步：生成 HTML 详细评审报告文件**（持久化保存的完整记录）
2. **第二步：使用 Shell 脚本输出控制台摘要**（确保非交互模式下用户也能看到）

---

### 5.1 生成 HTML 评审报告（第一步）

**目的：提供完整详细的评审报告，持久化保存评审记录。**

**使用步骤：**
1. 读取模板：`core/templates/html-report.template.html`
2. 替换占位符：`{{DECISION_ICON}}`、`{{DECISION_TEXT}}`、`{{P0_ISSUES}}` 等
3. **填充问题时**：直接使用阶段3评审时已记录的规则ID（规则ID在发现问题时就已确定）
4. 生成文件：使用 Write 工具，保存到 `code-review-result.html`（项目根目录）

**注意事项：**
- ✅ 包含评审结论、P0/P1/P2/P3 问题列表、评审概览（时间、分支、commit、文件数、行数）
- ✅ 必须使用中文撰写
- ✅ **规则ID已在阶段3评审时确定**，直接使用即可，无需重新查找或编造

> 📖 详细格式说明见：`core/templates.md`

---

### 5.2 使用 Shell 脚本输出控制台摘要（第二步，必须执行）

**🚨 关键：必须使用 Shell 脚本输出摘要，确保非交互模式（`-p` 参数）下用户也能看到评审结果！**

**使用步骤：**
1. 读取模板：`core/templates/console-output.template.sh`
2. 替换占位符：`{{SUMMARY}}`、`{{DECISION}}`、`{{P0_COUNT}}`、`{{P0_ISSUES}}` 等
3. 执行脚本：使用 Shell 工具执行

**注意事项：**
- ✅ 包含评审结论和 P0/P1/P2/P3 四个等级的问题
- ❌ 不包含时间戳、文件数、行数、commit 信息等元数据（仅在 HTML 中展示）

> 📖 详细格式说明见：`core/templates.md`

---

**🚨 重要提醒：**
- ✅ **必须按顺序执行：** 先生成 HTML 文件，再输出控制台摘要
- ❌ **禁止跳过：** 不能只生成 HTML 而不输出控制台摘要（非交互模式下用户看不到结果）
- ❌ **禁止替代：** 不能用响应消息代替 Shell 输出（非交互模式下不可见）
