# NotebookLM CLI - 完整命令参考

本文档包含每个 `nlm` 命令的完整命令签名和所有可用选项。

## 目录

1. [全局选项](#全局选项)
2. [身份验证](#身份验证)
3. [笔记本命令](#笔记本命令)
4. [来源命令](#来源命令)
5. [研究命令](#研究命令)
6. [生成命令](#生成命令)
7. [Studio 命令](#studio-命令)
8. [下载命令](#下载命令)
9. [导出命令](#导出命令)
10. [共享命令](#共享命令)
11. [笔记命令](#笔记命令)
12. [聊天命令](#聊天命令)
13. [别名命令](#别名命令)
14. [配置命令](#配置命令)

---

## 全局选项

```bash
nlm --version, -v      # 显示版本并退出
nlm --ai               # 输出 AI 友好的文档
nlm --install-completion  # 安装 shell 自动补全
nlm --show-completion  # 显示自动补全脚本
nlm --help             # 显示帮助并退出
```

---

## 身份验证

### nlm login

使用 Chrome DevTools 协议与 NotebookLM 进行身份验证。

```bash
nlm login [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 用于多账户的配置文件名称 |
| `--check` | | 验证当前凭据而无需重新进行身份验证 |
| `--legacy` | `-l` | 使用 browser-cookie3 备用方案（不推荐） |
| `--browser` | `-b` | 备用模式的浏览器（chrome、firefox、edge） |
| `--manual` | `-m` | 从文件导入 cookie |
| `--file` | `-f` | 手动模式的 cookie 文件路径 |

**注意**：每个配置文件都有自己的隔离 Chrome 会话，因此您可以同时登录多个 Google 账户。

### nlm login profile list

列出所有身份验证配置文件及其关联的电子邮件地址。

```bash
nlm login profile list
```

### nlm login profile delete

删除身份验证配置文件及其凭据。

```bash
nlm login profile delete <profile>
```

### nlm login profile rename

重命名身份验证配置文件。

```bash
nlm login profile rename <旧名称> <新名称>
```

### nlm login switch

切换所有命令的默认配置文件。

```bash
nlm login switch <profile>
```

| 参数 | 描述 |
|----------|-------------|
| `<profile>` | 要切换到的配置文件名称 |

**示例：**
```bash
nlm login switch work
# 输出：✓ 已将默认配置文件切换到 work
#         账户：jsmith@company.com
```

---

## 笔记本命令

### nlm notebook list

列出所有笔记本。

```bash
nlm notebook list [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--json` | | 输出为 JSON |
| `--quiet` | `-q` | 仅输出 ID |
| `--title` | | 输出为 "ID: 标题" |
| `--full` | | 显示所有列 |
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook create

创建新笔记本。

```bash
nlm notebook create <标题> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook get

获取笔记本详细信息。

```bash
nlm notebook get <notebook-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook describe

获取 AI 生成的笔记本摘要和建议主题。

```bash
nlm notebook describe <notebook-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook query

询问关于笔记本来源的问题。

```bash
nlm notebook query <notebook-id> <问题> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--source-ids` | | 限制为特定来源（逗号分隔） |
| `--conversation-id` | | 继续现有对话 |
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook rename

重命名笔记本。

```bash
nlm notebook rename <notebook-id> <新标题> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm notebook delete

永久删除笔记本。

```bash
nlm notebook delete <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--confirm` | **必需** 以确认删除 |
| `--profile` | 使用特定配置文件 |

---

## 来源命令

### nlm source list

列出笔记本中的来源。

```bash
nlm source list <notebook-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--json` | | 输出为 JSON |
| `--quiet` | `-q` | 仅输出 ID |
| `--title` | | 输出为 "ID: 标题" |
| `--url` | | 输出为 "ID: URL" |
| `--full` | | 显示所有列（更宽的 URL 显示） |
| `--drive` | | 显示带有新鲜度状态的 Drive 来源 |
| `--skip-freshness` | `-S` | 跳过新鲜度检查（配合 --drive 更快） |
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source add

向笔记本添加来源。

```bash
nlm source add <notebook-id> [选项]
```

**URL 来源：**
| 选项 | 描述 |
|--------|-------------|
| `--url` | 要添加的 URL（网页或 YouTube）|

**文本来源：**
| 选项 | 描述 |
|--------|-------------|
| `--text` | 要添加的文本内容 |
| `--title` | 文本来源的标题 |

**Drive 来源：**
| 选项 | 描述 |
|--------|-------------|
| `--drive` | Google Drive 文档 ID |
| `--type` | Drive 文档类型：`doc`、`slides`、`sheets`、`pdf` |
| `--title` | 显示标题 |

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source get

获取来源元数据。

```bash
nlm source get <source-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source describe

获取 AI 生成的来源摘要和关键词。

```bash
nlm source describe <source-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source content

获取来源的原始文本内容。

```bash
nlm source content <source-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--output` | `-o` | 导出到文件路径 |
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source stale

列出过时（过期）的 Drive 来源。

```bash
nlm source stale <notebook-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

### nlm source sync

将 Drive 来源与最新内容同步。

```bash
nlm source sync <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--confirm` | **必需** 以执行同步 |
| `--source-ids` | 要同步的特定来源 ID（逗号分隔） |
| `--profile` | 使用特定配置文件 |

### nlm source delete

永久删除来源。

```bash
nlm source delete <source-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--confirm` | **必需** 以确认删除 |
| `--profile` | 使用特定配置文件 |

---

## 研究命令

### nlm research start

启动研究任务以发现新来源。

```bash
nlm research start <查询> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--notebook-id` | **必需** - 目标笔记本 ID |
| `--mode` | `fast`（默认，约 30 秒）或 `deep`（约 5 分钟，仅限网络） |
| `--source` | `web`（默认）或 `drive` |
| `--force` | 覆盖待处理的研究 |
| `--profile` | 使用特定配置文件 |

### nlm research status

检查研究任务进度。

```bash
nlm research status <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--task-id` | 检查特定任务（如果省略则自动检测） |
| `--max-wait` | 最多等待秒数（默认：300，0=单次检查） |
| `--full` | 显示完整详细信息 |
| `--profile` | 使用特定配置文件 |

### nlm research import

将发现的来源导入笔记本。

```bash
nlm research import <notebook-id> <task-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--indices` | 要导入的来源索引（逗号分隔，默认：全部） |
| `--profile` | 使用特定配置文件 |

---

## 生成命令

所有生成命令都共享这些通用选项：

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--confirm` | `-y` | **必需** 以执行生成 |
| `--source-ids` | | 限制为特定来源（逗号分隔） |
| `--language` | | BCP-47 语言代码（en、es、fr、de、ja） |
| `--profile` | `-p` | 使用特定配置文件 |

### nlm audio create

生成音频概览（播客）。

```bash
nlm audio create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--format` | `deep_dive`、`brief`、`critique`、`debate` | `deep_dive` |
| `--length` | `short`、`default`、`long` | `default` |
| `--focus` | 聚焦文本/主题 | |

### nlm report create

生成书面报告。

```bash
nlm report create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--format` | `"Briefing Doc"`、`"Study Guide"`、`"Blog Post"`、`"Create Your Own"` | `"Briefing Doc"` |
| `--prompt` | 自定义提示（"Create Your Own" 所需） | |

### nlm quiz create

生成测验问题。

```bash
nlm quiz create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--count` | 问题数量 | 2 |
| `--difficulty` | 1-5（1=简单，5=困难） | 2 |

### nlm flashcards create

生成抽认卡。

```bash
nlm flashcards create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--difficulty` | `easy`、`medium`、`hard` | `medium` |

### nlm mindmap create

生成思维导图。

```bash
nlm mindmap create <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--title` | 思维导图的显示标题 |

### nlm mindmap list

列出现有思维导图。

```bash
nlm mindmap list <notebook-id> [选项]
```

### nlm slides create

生成幻灯片组。

```bash
nlm slides create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--format` | `detailed`、`presenter` | `detailed` |
| `--length` | `short`、`default` | `default` |
| `--focus` | 聚焦文本/主题 | |

### nlm infographic create

生成信息图表。

```bash
nlm infographic create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--orientation` | `landscape`、`portrait`、`square` | `landscape` |
| `--detail` | `concise`、`standard`、`detailed` | `standard` |
| `--focus` | 聚焦文本/主题 | |

### nlm video create

生成视频概览。

```bash
nlm video create <notebook-id> [选项]
```

| 选项 | 值 | 默认值 |
|--------|--------|---------|
| `--format` | `explainer`、`brief` | `explainer` |
| `--style` | `auto_select`、`classic`、`whiteboard`、`kawaii`、`anime`、`watercolor`、`retro_print`、`heritage`、`paper_craft` | `auto_select` |
| `--focus` | 聚焦文本/主题 | |

### nlm data-table create

将结构化数据提取为表格。

```bash
nlm data-table create <notebook-id> <描述> [选项]
```

**注意**：`<描述>` 是描述要提取什么的**必需位置参数**。

---

## Studio 命令

### nlm studio status

列出笔记本中的所有生成工件。

```bash
nlm studio status <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--json` | 输出为 JSON |
| `--full` | 显示所有详细信息 |
| `--profile` | 使用特定配置文件 |

### nlm studio delete

删除生成的工件。

```bash
nlm studio delete <notebook-id> <artifact-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--confirm` | **必需** 以确认删除 |
| `--profile` | 使用特定配置文件 |

---

## 下载命令

### nlm download

将生成的工件下载到本地文件。

```bash
nlm download <类型> <notebook-id> [选项]
```

**可用类型：** `audio`、`video`、`report`、`mind-map`、`slides`、`infographic`、`quiz`、`flashcards`、`data-table`

| 选项 | 描述 |
|--------|-------------|
| `--id` | 特定工件 ID（如果省略则使用最新的） |
| `--format` | quiz/flashcards 的输出格式：`json`、`markdown`、`html` |
| `--profile` | 使用特定配置文件 |

**示例：**
```bash
nlm download audio <nb-id> --output podcast.mp3
nlm download video <nb-id> --output video.mp4
nlm download report <nb-id> --output report.md
nlm download quiz <nb-id> --output quiz.html --format html
nlm download flashcards <nb-id> --output cards.json --format json
```

---

## 导出命令

### nlm export

将工件导出到 Google Docs 或 Sheets。

```bash
nlm export <类型> <notebook-id> <artifact-id> [选项]
```

**可用类型：** `docs`、`sheets`

| 选项 | 描述 |
|--------|-------------|
| `--title` | 导出文档的标题 |
| `--profile` | 使用特定配置文件 |

**示例：**
```bash
nlm export sheets <nb-id> <artifact-id> --title "数据表格导出"
nlm export docs <nb-id> <artifact-id> --title "我的报告"
```

---

## 共享命令

### nlm share status

获取笔记本的当前共享设置。

```bash
nlm share status <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--profile` | 使用特定配置文件 |

### nlm share public

启用或禁用公共链接共享。

```bash
nlm share public <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--off` | 禁用公共共享（默认：启用） |
| `--profile` | 使用特定配置文件 |

**示例：**
```bash
nlm share public <nb-id>         # 启用公共链接
nlm share public <nb-id> --off   # 禁用公共链接
```

### nlm share invite

通过电子邮件邀请协作者。

```bash
nlm share invite <notebook-id> <email> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--role` | `viewer`（默认）或 `editor` |
| `--profile` | 使用特定配置文件 |

**示例：**
```bash
nlm share invite <nb-id> user@example.com
nlm share invite <nb-id> user@example.com --role editor
```

---

## 笔记命令

### nlm note create

在笔记本中创建笔记。

```bash
nlm note create <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--content` | 笔记内容（必需） |
| `--title` | 笔记标题 |
| `--profile` | 使用特定配置文件 |

### nlm note list

列出笔记本中的所有笔记。

```bash
nlm note list <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--json` | 输出为 JSON |
| `--profile` | 使用特定配置文件 |

### nlm note update

更新现有笔记。

```bash
nlm note update <notebook-id> <note-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--content` | 新内容 |
| `--title` | 新标题 |
| `--profile` | 使用特定配置文件 |

### nlm note delete

永久删除笔记。

```bash
nlm note delete <notebook-id> <note-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--confirm` | **必需** 以确认删除 |
| `--profile` | 使用特定配置文件 |

## 聊天命令

### nlm chat start

启动交互式聊天 REPL 会话。

```bash
nlm chat start <notebook-id> [选项]
```

| 选项 | 简写 | 描述 |
|--------|-------|-------------|
| `--profile` | `-p` | 使用特定配置文件 |

**REPL 命令：**
- `/sources` - 列出可用来源
- `/clear` - 重置对话上下文
- `/help` - 显示可用命令
- `/exit` - 退出 REPL

### nlm chat configure

为笔记本配置聊天行为。

```bash
nlm chat configure <notebook-id> [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--goal` | `default`、`learning_guide`、`custom` |
| `--prompt` | 自定义系统提示（goal 为 `custom` 时必需） |
| `--response-length` | `default`、`longer`、`shorter` |
| `--profile` | 使用特定配置文件 |

---

## 别名命令

### nlm alias set

为 UUID 创建或更新别名。

```bash
nlm alias set <名称> <uuid>
```

类型自动检测（notebook、source、artifact、task）。

### nlm alias get

将别名解析为其 UUID。

```bash
nlm alias get <名称>
```

### nlm alias list

列出所有别名。

```bash
nlm alias list
```

### nlm alias delete

删除别名。

```bash
nlm alias delete <名称>
```

---

## 配置命令

### nlm config show

显示当前配置。

```bash
nlm config show [选项]
```

| 选项 | 描述 |
|--------|-------------|
| `--json` | 输出为 JSON 而不是 TOML |

### nlm config get

获取特定配置值。

```bash
nlm config get <key>
```

### nlm config set

设置配置值。

```bash
nlm config set <key> <value>
```

**可用配置键：**

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `output.format` | `table` | 默认输出格式（table、json） |
| `output.color` | `true` | 启用彩色输出 |
| `output.short_ids` | `true` | 显示缩短的 ID |
| `auth.browser` | `auto` | 登录使用的浏览器（auto、chrome、chromium） |
| `auth.default_profile` | `default` | 未指定 `--profile` 时使用的配置文件 |

**示例**：设置默认配置文件以避免为每个命令输入 `--profile`：

```bash
# 首选方法（更简单）
nlm login switch work

# 备用方法（通过配置）
nlm config set auth.default_profile work
```
