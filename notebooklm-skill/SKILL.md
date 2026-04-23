---
name: notebooklm-skill
description: "NotebookLM CLI (`nlm`) 和 MCP 服务器的专家指南 - Google NotebookLM 的接口。当用户想要通过编程方式与 NotebookLM 交互时使用此 skill，包括：创建/管理笔记本、添加来源（URL、YouTube、文本、Google Drive）、生成内容（播客、报告、测验、抽认卡、思维导图、幻灯片、信息图表、视频、数据表格）、进行研究、与来源对话或自动化 NotebookLM 工作流。触发关键词：\"nlm\"、\"notebooklm\"、\"notebook lm\"、\"播客生成\"、\"音频概览\"或任何 NotebookLM 相关的自动化任务。"
---

# NotebookLM CLI 与 MCP 专家指南

此 skill 为使用 NotebookLM 的 `nlm` CLI 和 MCP 工具提供全面指导。

## 工具检测（关键 - 请先阅读！）

**在继续之前，务必检查可用的工具：**

1. **检查 MCP 工具**：查找以 `mcp__notebooklm-mcp__*` 或 `mcp_notebooklm_*` 开头的工具
2. **如果 MCP 工具和 CLI 都可用**：**询问用户**在继续之前他们更喜欢使用哪一种
3. **如果只有 MCP 工具可用**：直接使用它们（参考工具文档字符串获取参数）
4. **如果只有 CLI 可用**：通过 Bash 使用 `nlm` CLI 命令

**决策逻辑：**
```
has_mcp_tools = check_available_tools()  # 查找 mcp__notebooklm-mcp__* 或 mcp_notebooklm_*
has_cli = check_bash_available()  # 可以运行 nlm 命令

if has_mcp_tools and has_cli:
    # 询问用户："我可以使用 MCP 工具或 nlm CLI。您更喜欢哪一种？"
    user_preference = ask_user()
else if has_mcp_tools:
    # 直接使用 MCP 工具
    mcp__notebooklm-mcp__notebook_list()
else:
    # 通过 Bash 使用 CLI
    bash("nlm notebook list")
```

此 skill 记录了**两种**方法。根据工具可用性和**用户偏好**选择合适的方法。

## 快速参考

**运行 `nlm --ai` 获取全面的 AI 优化文档** - 这提供了所有 CLI 功能的完整视图。

```bash
nlm --help              # 列出所有命令
nlm <command> --help    # 特定命令的帮助
nlm --ai                # 完整的 AI 优化文档（推荐）
nlm --version           # 检查已安装的版本
```

## 关键规则（请先阅读！）

1. **务必先进行身份验证**：在任何操作之前运行 `nlm login`
2. **会话约 20 分钟后过期**：如果命令开始失败，请重新运行 `nlm login`
3. **⚠️ 删除前务必询问用户**：在执行任何删除命令之前，请征求用户的明确确认。删除操作是**不可逆的**。显示将要删除的内容并警告永久数据丢失。
4. **`--confirm` 是必需的**：所有生成和删除命令都需要 `--confirm` 或 `-y`（CLI）或 `confirm=True`（MCP）
5. **研究需要 `--notebook-id`**：该标志是必需的，不是位置参数
6. **从输出中捕获 ID**：创建/启动命令返回后续操作所需的 ID
7. **使用别名**：使用 `nlm alias set <name> <uuid>` 简化长 UUID
8. **创建前检查别名**：在创建新别名之前运行 `nlm alias list` 以避免与现有名称冲突
9. **不要启动 REPL**：永远不要使用 `nlm chat start` - 它会打开一个 AI 工具无法控制的交互式 REPL。使用 `nlm notebook query` 进行一次性问答
10. **明智选择输出格式**：默认输出（无标志）紧凑且节省 token - 将其用于状态检查。使用 `--quiet` 捕获 ID 以进行管道传输。仅当需要以编程方式解析特定字段时才使用 `--json`
11. **不确定时使用 `--help`**：运行 `nlm <command> --help` 查看任何命令的可用选项和标志

## 工作流决策树

使用此方法确定正确的命令顺序：

```
用户想要...
│
├─► 首次使用 NotebookLM
│   └─► nlm login → nlm notebook create "标题"
│
├─► 向笔记本添加内容
│   ├─► 从 URL/网页 → nlm source add <nb-id> --url "https://..."
│   ├─► 从 YouTube → nlm source add <nb-id> --url "https://youtube.com/..."
│   ├─► 从粘贴的文本 → nlm source add <nb-id> --text "内容" --title "标题"
│   ├─► 从 Google Drive → nlm source add <nb-id> --drive <doc-id> --type doc
│   └─► 发现新来源 → nlm research start "查询" --notebook-id <nb-id>
│
├─► 从来源生成内容
│   ├─► 播客/音频 → nlm audio create <nb-id> --confirm
│   ├─► 书面摘要 → nlm report create <nb-id> --confirm
│   ├─► 学习资料 → nlm quiz/flashcards create <nb-id> --confirm
│   ├─► 视觉内容 → nlm mindmap/slides/infographic create <nb-id> --confirm
│   ├─► 视频 → nlm video create <nb-id> --confirm
│   └─► 提取数据 → nlm data-table create <nb-id> "描述" --confirm
│
├─► 询问来源相关问题
│   └─► nlm notebook query <nb-id> "问题"
│       （使用 --conversation-id 进行后续追问）
│       ⚠️ 不要使用 `nlm chat start` - 它仅供人类使用的 REPL
│
├─► 检查生成状态
│   └─► nlm studio status <nb-id>
│
└─► 管理/清理
    ├─► 列出笔记本 → nlm notebook list
    ├─► 列出来源 → nlm source list <nb-id>
    ├─► 删除来源 → nlm source delete <source-id> --confirm
    └─► 删除笔记本 → nlm notebook delete <nb-id> --confirm
```

## 命令分类

### 1. 身份验证

#### MCP 身份验证

如果使用 MCP 工具并遇到身份验证错误：

```bash
# 运行 CLI 身份验证（适用于 CLI 和 MCP）
nlm login

# 然后在 MCP 中重新加载令牌
mcp__notebooklm-mcp__refresh_auth()
```

或通过 MCP 手动保存 cookie（备用方案）：
```python
# 从 Chrome DevTools 提取 cookie 并保存
mcp__notebooklm-mcp__save_auth_tokens(cookies="<cookie_header>")
```

#### CLI 身份验证

```bash
nlm login                           # 启动 Chrome，提取 cookie（主要方法）
nlm login --check                   # 验证当前会话
nlm login --profile work            # 使用命名配置文件管理多个账户
nlm login switch <profile>          # 切换默认配置文件
nlm login profile list              # 列出所有配置文件及其电子邮件地址
nlm login profile delete <name>     # 删除配置文件
nlm login profile rename <old> <new> # 重命名配置文件
```

**多配置文件支持**：每个配置文件都有自己的隔离 Chrome 会话，因此您可以同时登录多个 Google 账户。

**会话生命周期**：约 20 分钟。当命令因身份验证错误而失败时，请重新进行身份验证。

**切换默认配置文件**：使用 `nlm login switch <name>` 快速更改默认配置文件，无需为每个命令输入 `--profile`。

**注意**：MCP 和 CLI 共享相同的身份验证后端，因此使用其中一个进行身份验证对两者都有效。

### 2. 笔记本管理

#### MCP 工具

使用工具：`notebook_list`、`notebook_create`、`notebook_get`、`notebook_describe`、`notebook_query`、`notebook_rename`、`notebook_delete`。所有都接受 `notebook_id` 参数。删除需要 `confirm=True`。

#### CLI 命令
```bash
nlm notebook list                      # 列出所有笔记本
nlm notebook list --json               # 用于解析的 JSON 输出
nlm notebook list --quiet              # 仅 ID（用于脚本）
nlm notebook create "标题"            # 创建笔记本，返回 ID
nlm notebook get <id>                  # 获取笔记本详细信息
nlm notebook describe <id>             # AI 生成的摘要 + 建议主题
nlm notebook query <id> "问题"     # 与来源进行一次性问答
nlm notebook rename <id> "新标题"   # 重命名笔记本
nlm notebook delete <id> --confirm     # 永久删除
```

### 3. 来源管理

#### MCP 工具

使用 `source_add` 配合以下 `source_type` 值：
- `url` - 网页或 YouTube URL（`url` 参数）
- `text` - 粘贴的内容（`text` + `title` 参数）
- `file` - 本地文件上传（`file_path` 参数）
- `drive` - Google Drive 文档（`document_id` + `doc_type` 参数）

其他工具：`source_list_drive`、`source_describe`、`source_get_content`、`source_sync_drive`（需要 `confirm=True`）、`source_delete`（需要 `confirm=True`）。

#### CLI 命令
```bash
# 添加来源
nlm source add <nb-id> --url "https://..."           # 网页
nlm source add <nb-id> --url "https://youtube.com/..." # YouTube 视频
nlm source add <nb-id> --text "内容" --title "X"  # 粘贴文本
nlm source add <nb-id> --drive <doc-id>              # Drive 文档（自动检测类型）
nlm source add <nb-id> --drive <doc-id> --type slides # 明确指定类型

# 列出和查看
nlm source list <nb-id>                # 来源表格
nlm source list <nb-id> --drive        # 显示带有新鲜度的 Drive 来源
nlm source list <nb-id> --drive -S     # 跳过新鲜度检查（更快）
nlm source get <source-id>             # 来源元数据
nlm source describe <source-id>        # AI 摘要 + 关键词
nlm source content <source-id>         # 原始文本内容
nlm source content <source-id> -o file.txt  # 导出到文件

# Drive 同步（用于过时的来源）
nlm source stale <nb-id>               # 列出过时的 Drive 来源
nlm source sync <nb-id> --confirm      # 同步所有过时的来源
nlm source sync <nb-id> --source-ids <ids> --confirm  # 同步特定来源

# 删除
nlm source delete <source-id> --confirm
```

**Drive 类型**：`doc`、`slides`、`sheets`、`pdf`

### 4. 研究（来源发现）

研究从网络或 Google Drive 发现新来源。

#### MCP 工具

使用 `research_start` 配合：
- `source`：`web` 或 `drive`
- `mode`：`fast`（约 30 秒）或 `deep`（约 5 分钟，仅限网络）

工作流：`research_start` → 轮询 `research_status` → `research_import`

#### CLI 命令
```bash
# 开始研究（--notebook-id 是必需的）
nlm research start "查询" --notebook-id <id>              # 快速网络搜索（约 30 秒）
nlm research start "查询" --notebook-id <id> --mode deep  # 深度网络搜索（约 5 分钟）
nlm research start "查询" --notebook-id <id> --source drive  # Drive 搜索

# 检查进度
nlm research status <nb-id>                   # 轮询直到完成（最多 5 分钟）
nlm research status <nb-id> --max-wait 0      # 单次检查，不等待
nlm research status <nb-id> --task-id <tid>   # 检查特定任务
nlm research status <nb-id> --full            # 完整详细信息

# 导入发现的来源
nlm research import <nb-id> <task-id>            # 导入全部
nlm research import <nb-id> <task-id> --indices 0,2,5  # 导入特定来源
```

**模式**：`fast`（约 30 秒，约 10 个来源）| `deep`（约 5 分钟，约 40+ 个来源，仅限网络）

### 5. 内容生成（Studio）

#### MCP 工具（统一创建）

使用 `studio_create` 配合 `artifact_type` 和特定类型的选项。所有都需要 `confirm=True`。

| artifact_type | 关键选项 |
|--------------|-------------|
| `audio` | `audio_format`：deep_dive/brief/critique/debate，`audio_length`：short/default/long |
| `video` | `video_format`：explainer/brief，`visual_style`：auto_select/classic/whiteboard/kawaii/anime/watercolor/retro_print/heritage/paper_craft |
| `report` | `report_format`：Briefing Doc/Study Guide/Blog Post/Create Your Own，`custom_prompt` |
| `quiz` | `question_count`，`difficulty`：easy/medium/hard |
| `flashcards` | `difficulty`：easy/medium/hard |
| `mind_map` | `title` |
| `slide_deck` | `slide_format`：detailed_deck/presenter_slides，`slide_length`：short/default |
| `infographic` | `orientation`：landscape/portrait/square，`detail_level`：concise/standard/detailed |
| `data_table` | `description`（必需）|

**通用选项**：`source_ids`、`language`（BCP-47 代码）、`focus_prompt`

#### CLI 命令

所有生成命令都共享这些标志：
- `--confirm` 或 `-y`：**必需**以执行
- `--source-ids <id1,id2>`：限制为特定来源
- `--language <code>`：BCP-47 语言代码（en、es、fr、de、ja）

```bash
# 音频（播客）
nlm audio create <id> --confirm
nlm audio create <id> --format deep_dive --length default --confirm
nlm audio create <id> --format brief --focus "关键主题" --confirm
# 格式：deep_dive、brief、critique、debate
# 长度：short、default、long

# 报告
nlm report create <id> --confirm
nlm report create <id> --format "Study Guide" --confirm
nlm report create <id> --format "Create Your Own" --prompt "自定义..." --confirm
# 格式："Briefing Doc"、"Study Guide"、"Blog Post"、"Create Your Own"

# 测验
nlm quiz create <id> --confirm
nlm quiz create <id> --count 5 --difficulty 3 --confirm
# 数量：问题数量（默认：2）
# 难度：1-5（1=简单，5=困难）

# 抽认卡
nlm flashcards create <id> --confirm
nlm flashcards create <id> --difficulty hard --confirm
# 难度：easy、medium、hard

# 思维导图
nlm mindmap create <id> --confirm
nlm mindmap create <id> --title "主题概览" --confirm
nlm mindmap list <id>  # 列出现有思维导图

# 幻灯片
nlm slides create <id> --confirm
nlm slides create <id> --format presenter --length short --confirm
# 格式：detailed、presenter | 长度：short、default

# 信息图表
nlm infographic create <id> --confirm
nlm infographic create <id> --orientation portrait --detail detailed --confirm
# 方向：landscape、portrait、square
# 详情：concise、standard、detailed

# 视频
nlm video create <id> --confirm
nlm video create <id> --format brief --style whiteboard --confirm
# 格式：explainer、brief
# 样式：auto_select、classic、whiteboard、kawaii、anime、watercolor、retro_print、heritage、paper_craft

# 数据表格
nlm data-table create <id> "提取所有日期和事件" --confirm
# 描述是作为第二个参数必需的
```

### 6. Studio（工件管理）

#### MCP 工具

使用 `studio_status` 检查进度（或使用 `action="rename"` 重命名）。使用 `download_artifact` 配合 `artifact_type` 和 `output_path`。使用 `export_artifact` 配合 `export_type`：docs/sheets。使用 `studio_delete` 删除（需要 `confirm=True`）。

#### CLI 命令
```bash
# 检查状态
nlm studio status <nb-id>                          # 列出所有工件
nlm studio status <nb-id> --full                   # 显示完整详细信息（包括自定义提示）
nlm studio status <nb-id> --json                   # JSON 输出

# 下载工件
nlm download audio <nb-id> --output podcast.mp3
nlm download video <nb-id> --output video.mp4
nlm download report <nb-id> --output report.md
nlm download quiz <nb-id> --output quiz.json --format json

# 导出到 Google Docs/Sheets
nlm export sheets <nb-id> <artifact-id> --title "我的数据表格"
nlm export docs <nb-id> <artifact-id> --title "我的报告"

# 删除工件
nlm studio delete <nb-id> <artifact-id> --confirm
```

**状态值**：`completed`（✓）、`in_progress`（●）、`failed`（✗）

### 重命名工件

#### MCP 工具

使用 `studio_status` 配合 `action="rename"`、`artifact_id` 和 `new_title`。

#### CLI 命令
```bash
nlm studio rename <artifact-id> "新标题"
nlm rename studio <artifact-id> "新标题"  # 动词优先的替代方案
```

### 服务器信息（版本检查）

#### MCP 工具

使用 `server_info` 获取版本并检查更新：

```python
mcp__notebooklm-mcp__server_info()
# 返回：version、latest_version、update_available、update_command
```

#### CLI 命令
```bash
nlm --version  # 显示版本和更新可用性
```

### 7. 聊天配置和笔记

#### MCP 工具

使用 `chat_configure` 配合 `goal`：default/learning_guide/custom。使用 `note` 配合 `action`：create/list/update/delete。删除需要 `confirm=True`。

#### CLI 命令

> ⚠️ **AI 工具：不要使用 `nlm chat start`** - 它会启动一个无法以编程方式控制的交互式 REPL。请使用 `nlm notebook query` 进行一次性问答

对于终端中的用户：

```bash
nlm chat start <nb-id>  # 启动交互式 REPL
```

**REPL 命令**：
- `/sources` - 列出可用来源
- `/clear` - 重置对话上下文
- `/help` - 显示命令
- `/exit` - 退出 REPL

**配置聊天行为**（适用于 REPL 和 query）：
```bash
nlm chat configure <id> --goal default
nlm chat configure <id> --goal learning_guide
nlm chat configure <id> --goal custom --prompt "充当导师..."
nlm chat configure <id> --response-length longer  # longer、default、shorter
```

**笔记管理**：
```bash
nlm note create <nb-id> "内容" --title "标题"
nlm note list <nb-id>
nlm note update <nb-id> <note-id> --content "新内容"
nlm note delete <nb-id> <note-id> --confirm
```

### 8. 笔记本共享

#### MCP 工具

使用 `notebook_share_status` 检查，`notebook_share_public` 启用/禁用公共链接，`notebook_share_invite` 配合 `email` 和 `role`：viewer/editor。

#### CLI 命令
```bash
# 检查共享状态
nlm share status <nb-id>

# 启用/禁用公共链接
nlm share public <nb-id>          # 启用
nlm share public <nb-id> --off    # 禁用

# 邀请协作者
nlm share invite <nb-id> user@example.com
nlm share invite <nb-id> user@example.com --role editor
```

### 9. 别名（UUID 快捷方式）

简化长 UUID：

```bash
nlm alias set myproject abc123-def456...  # 创建别名（自动检测类型）
nlm alias get myproject                    # 解析为 UUID
nlm alias list                             # 列出所有别名
nlm alias delete myproject                 # 删除别名

# 在任何地方使用别名
nlm notebook get myproject
nlm source list myproject
nlm audio create myproject --confirm
```

### 10. 配置

仅用于管理设置的 CLI 命令：

```bash
nlm config show                              # 显示当前配置
nlm config get <key>                         # 获取特定设置
nlm config set <key> <value>                 # 更新设置
nlm config set output.format json            # 更改默认输出

# 对于切换配置文件，首选更简单的命令：
nlm login switch work                        # 切换默认配置文件
```

**可用设置：**

| 键 | 默认值 | 描述 |
|-----|---------|-------------|
| `output.format` | `table` | 默认输出格式（table、json） |
| `output.color` | `true` | 启用彩色输出 |
| `output.short_ids` | `true` | 显示缩短的 ID |
| `auth.browser` | `auto` | 登录使用的浏览器（auto、chrome、chromium） |
| `auth.default_profile` | `default` | 未指定 `--profile` 时使用的配置文件 |

## 输出格式

大多数列表命令支持多种格式：

| 标志 | 描述 |
|------|-------------|
| (无) | 丰富的表格（人类可读） |
| `--json` | JSON 输出（用于解析） |
| `--quiet` | 仅 ID（用于管道传输） |
| `--title` | "ID: 标题" 格式 |
| `--url` | "ID: URL" 格式（仅来源） |
| `--full` | 所有列/详细信息 |

## 常见模式

### 模式 1：研究 → 播客流程

```bash
nlm notebook create "AI 研究 2026"   # 捕获 ID
nlm alias set ai <notebook-id>
nlm research start "智能体 AI 趋势" --notebook-id ai --mode deep
nlm research status ai --max-wait 300    # 最多等待 5 分钟
nlm research import ai <task-id>         # 导入所有来源
nlm audio create ai --format deep_dive --confirm
nlm studio status ai                     # 检查生成进度
```

### 模式 2：快速内容摄取

```bash
nlm source add <id> --url "https://example1.com"
nlm source add <id> --url "https://example2.com"
nlm source add <id> --text "我的笔记..." --title "笔记"
nlm source list <id>
```

### 模式 3：学习资料生成

```bash
nlm report create <id> --format "Study Guide" --confirm
nlm quiz create <id> --count 10 --difficulty 3 --confirm
nlm flashcards create <id> --difficulty medium --confirm
```

### 模式 4： Drive 文档工作流

```bash
nlm source add <id> --drive 1KQH3eW0hMBp7WK... --type slides
# ...时间流逝，文档被编辑...
nlm source stale <id>                    # 检查新鲜度
nlm source sync <id> --confirm           # 如果过时则同步
```

## 错误恢复

| 错误 | 原因 | 解决方案 |
|-------|-------|----------|
| "Cookies have expired" | 会话超时 | `nlm login` |
| "authentication may have expired" | 会话超时 | `nlm login` |
| "Notebook not found" | 无效 ID | `nlm notebook list` |
| "Source not found" | 无效 ID | `nlm source list <nb-id>` |
| "Rate limit exceeded" | 调用过多 | 等待 30 秒，重试 |
| "Research already in progress" | 待处理的研究 | 使用 `--force` 或先导入 |
| Chrome 无法启动 | 端口冲突 | 关闭 Chrome，重试 |

## 速率限制

在操作之间等待以避免速率限制：
- 来源操作：2 秒
- 内容生成：5 秒
- 研究操作：2 秒
- 查询操作：2 秒

## 高级参考

有关详细信息，请参阅：
- **[references/command_reference.md](references/command_reference.md)**：完整命令签名
- **[references/troubleshooting.md](references/troubleshooting.md)**：详细错误处理
- **[references/workflows.md](references/workflows.md)**：端到端任务序列
