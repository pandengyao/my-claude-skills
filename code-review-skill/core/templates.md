# 代码评审模板使用说明

## 模板概述

本目录的 `templates/` 文件夹包含两个独立的模板文件：

1. **`templates/console-output.template.sh`** - 控制台输出模板（heredoc 纯文本格式）
2. **`templates/html-report.template.html`** - HTML 评审报告模板（详细的 HTML 报告）

每个模板都使用 `{{占位符}}` 标记需要填充的内容，LLM 只需读取模板并替换占位符即可生成最终输出。

---

## 统一占位符说明

所有模板共享以下占位符定义，不同模板使用不同的占位符子集。

| 占位符 | 说明 | 示例值 | 使用模板 |
|--------|------|--------|----------|
| `{{SUMMARY}}` | 评审总结一句话 | "代码质量良好，未发现问题。" | Console |
| `{{DECISION}}` | 评审结论（带图标） | "✅ 批准合并" | Console |
| `{{DECISION_ICON}}` | 评审结论图标 | "✅" / "💬" / "🔄" | HTML |
| `{{DECISION_TEXT}}` | 评审结论文字 | "批准合并" | HTML |
| `{{DECISION_DESC}}` | 评审结论描述 | "代码质量良好，未发现问题。" | HTML |
| `{{P0_COUNT}}` | P0 严重问题数量 | "0" 或 "2" | Console, HTML |
| `{{P0_ISSUES}}` | P0 问题内容 | 见下方格式说明 | Console, HTML |
| `{{P1_COUNT}}` | P1 主要问题数量 | "0" 或 "1" | Console, HTML |
| `{{P1_ISSUES}}` | P1 问题内容 | 见下方格式说明 | Console, HTML |
| `{{P2_COUNT}}` | P2 小问题数量 | "0" 或 "3" | Console, HTML |
| `{{P2_ISSUES}}` | P2 问题内容 | 见下方格式说明 | Console, HTML |
| `{{P3_COUNT}}` | P3 建议数量 | "0" 或 "1" | Console, HTML |
| `{{P3_ISSUES}}` | P3 建议内容 | 见下方格式说明 | Console, HTML |
| `{{REVIEW_TIME}}` | 评审时间 | "2026年1月19日 14:30" | HTML |
| `{{BRANCH_NAME}}` | 分支名称 | "feature/user-profile" | HTML |
| `{{COMMIT_INFO}}` | 提交信息 | "a1b2c3d - 添加用户资料功能" | HTML |
| `{{FILES_CHANGED}}` | 变更文件数 | "8" | HTML |
| `{{LINES_CHANGED}}` | 变更行数 | "+245 / -67" | HTML |

---

## 一、控制台输出模板

### 模板文件
**文件路径**: `templates/console-output.template.sh`

### 用途
使用 Bash echo 输出评审结果，确保在**非交互模式（-p 参数）**下用户也能看到评审摘要。

### 格式要求
- ✅ **使用 heredoc 输出**（简洁优雅）
- ✅ **纯文本格式，便于管道和日志捕获**
- ✅ **包含评审结论和问题列表**
- ✅ **不包含元数据**（文件数、行数、commit 信息等）
- ❌ **不包含时间戳或日志前缀**

### 使用的占位符

`{{SUMMARY}}`, `{{DECISION}}`, `{{P0_COUNT}}`, `{{P0_ISSUES}}`, `{{P1_COUNT}}`, `{{P1_ISSUES}}`, `{{P2_COUNT}}`, `{{P2_ISSUES}}`, `{{P3_COUNT}}`, `{{P3_ISSUES}}`

### 问题内容格式

**如果有问题**，每个问题使用以下格式（纯文本，问题之间用空行分隔）：
```
1. **问题标题**
   - 位置：文件路径:行号
   - 问题：问题描述
   - 建议：修复建议

```

**如果无问题**，填充：
```
无
```

### 使用步骤

1. **读取模板文件**: `templates/console-output.template.sh`
2. **替换占位符**: 将 `{{占位符}}` 替换为实际内容
3. **使用 Shell 工具执行**: 将替换后的脚本通过 Shell 工具执行

---

## 二、HTML 评审报告模板

### 模板文件
**文件路径**: `templates/html-report.template.html`

### 用途
生成详细的 HTML 格式评审报告文件，便于保存、分享和归档。

### 格式要求
- ✅ **CSS 样式已固定在模板中**，无需修改
- ✅ **LLM 只需要替换占位符**
- ✅ **必须包含所有等级的问题**（🔴P0严重/🟡P1主要/🟢P2小问题/💡P3建议）
- ✅ **使用中文撰写所有内容**
- ✅ **文件名固定**：`code-review-result.html`
- ✅ **位置固定**：项目根目录

### 使用的占位符

`{{DECISION_ICON}}`, `{{DECISION_TEXT}}`, `{{DECISION_DESC}}`, `{{P0_COUNT}}`, `{{P0_ISSUES}}`, `{{P1_COUNT}}`, `{{P1_ISSUES}}`, `{{P2_COUNT}}`, `{{P2_ISSUES}}`, `{{P3_COUNT}}`, `{{P3_ISSUES}}`, `{{REVIEW_TIME}}`, `{{BRANCH_NAME}}`, `{{COMMIT_INFO}}`, `{{FILES_CHANGED}}`, `{{LINES_CHANGED}}`

### 问题 HTML 格式

**如果有问题**，每个问题使用以下 HTML 格式：
```html
<div class="issue">
  <h3>1. 问题标题 <span style="color: #666; font-size: 0.85em;">[p1-naming-semantic]</span></h3>
  <p><strong>位置：</strong>文件路径:行号</p>
  <p><strong>问题：</strong>问题描述</p>
  <p><strong>建议：</strong>修复建议</p>
  <!-- 可选：代码示例 -->
  <pre><code>代码示例</code></pre>
</div>
```

**规则ID说明（🚨 必须严格遵守 🚨）：**
- 每个问题标题旁必须用灰色小字标注对应的规则ID
- ⚠️ **规则ID必须100%来自 checklist 文件中实际存在的 `id` 字段**（包括 checklist-common.yaml、checklist-fe.yaml 和 checklist-<语言>.yaml）
- ❌ **严禁编造、修改、组合规则ID**（如：不能编造 `p1-use-cosmic-tokens-improvement` 这种不存在的ID）
- 格式：`[规则id]`（如：[p0-division-by-zero-check], [p1-naming-semantic]）

**🚨 问题分类规则（必须遵守）：**

问题必须根据规则ID的前缀放入对应的等级列表：
- `p0-xxx` 规则 → 放入 `{{P0_ISSUES}}`（P0 严重问题）
- `p1-xxx` 规则 → 放入 `{{P1_ISSUES}}`（P1 主要问题）
- `p2-xxx` 规则 → 放入 `{{P2_ISSUES}}`（P2 小问题）
- `p3-xxx` 规则 → 放入 `{{P3_ISSUES}}`（P3 建议）

**Cosmic Token 特殊格式（`p0-use-cosmic-tokens`）**
- 必须只输出 1 条 issue（不可按文件拆分为多条）
- 标题统一：`样式文件中存在硬编码值，应使用 Cosmic Token [p0-use-cosmic-tokens]`
- 位置与检测结果必须按文件分块（按脚本 `results[]` 顺序），每个文件块格式：
  - 位置：`<results[i].file>:<results[i].lines>`
  - 检测到的硬编码值：使用 `results[i].issue_points`
- 该 issue 的通用部分必须包含：
  - 问题：未使用已有的 Cosmic Token，而使用了硬编码数值

**如果无问题**，填充：
```html
<p>无</p>
```

### 使用步骤

1. **读取模板文件**: `templates/html-report.template.html`
2. **替换占位符**: 将 `{{占位符}}` 替换为实际内容
3. **使用 Write 工具输出**: 保存为 `code-review-result.html`（项目根目录）

