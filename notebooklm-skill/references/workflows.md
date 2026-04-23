# NotebookLM CLI - 完整工作流序列

本文档为 `nlm` CLI 的常见任务提供端到端的工作流序列。

## 关键 AI 行为规则

### 始终确认破坏性操作

**在执行任何删除操作之前，务必征求用户的明确确认。** 删除操作是不可逆的。

AI 执行前需要用户确认的命令：
- `nlm notebook delete <id> --confirm`
- `nlm source delete <id> --confirm`
- `nlm studio delete <notebook-id> <artifact-id> --confirm`
- `nlm auth delete <profile> --confirm`

**AI 行为示例：**
```
用户："删除那个笔记本"

AI："我找到了笔记本 'AI Research'（ID: abc123...）。
⚠️ 这将永久删除该笔记本及其所有来源、生成内容和历史记录。
此操作无法撤销。

您想要继续删除吗？"

[等待用户确认后运行: nlm notebook delete abc123... --confirm]
```

---

## 工作流 1：首次设置

### 目标：身份验证并创建第一个笔记本

```bash
# 步骤 1：身份验证（打开 Chrome）
nlm login

# 步骤 2：验证身份验证
nlm login --check
# 预期: "Authentication valid! Notebooks found: N"

# 步骤 3：创建笔记本
nlm notebook create "我的第一个笔记本"
# 输出: Created notebook: <notebook-id>

# 步骤 4：为方便设置别名
nlm alias set first <notebook-id>

# 步骤 5：验证
nlm notebook get first
```

---

## 工作流 2：内容摄取

### 目标：向笔记本添加多个来源

```bash
# 前提条件：已身份验证，拥有笔记本 ID

# 添加网页
nlm source add <notebook-id> --url "https://example.com/article1"
sleep 2  # 节流以避免速率限制

nlm source add <notebook-id> --url "https://example.com/article2"
sleep 2

# 添加 YouTube 视频
nlm source add <notebook-id> --url "https://youtube.com/watch?v=VIDEO_ID"
sleep 2

# 添加粘贴的文本/笔记
nlm source add <notebook-id> --text "我关于此主题的个人笔记和观察..." --title "我的笔记"
sleep 2

# 添加 Google Drive 文档
nlm source add <notebook-id> --drive 1KQH3eW0hMBp7WKukQ1oURhnW-SdOT1qq --type doc
sleep 2

# 验证所有来源已添加
nlm source list <notebook-id>
```

---

## 工作流 3：研究 → 播客流程

### 目标：通过研究发现来源并生成播客

```bash
# 步骤 1：创建专用笔记本
nlm notebook create "AI 趋势研究 2026"
# 捕获: NOTEBOOK_ID=<id>

# 步骤 2：设置别名
nlm alias set research <notebook-id>

# 步骤 3：开始深度研究（约需 5 分钟）
nlm research start "智能体 AI 和自主系统趋势 2026" --notebook-id research --mode deep
# 捕获: TASK_ID=<task_id>

# 步骤 4：监控进度（轮询直到完成或超时）
nlm research status research --max-wait 300

# 步骤 5：查看发现的来源
nlm research status research --full

# 步骤 6：导入所有发现的来源
nlm research import research <task-id>
# 或导入特定来源:
# nlm research import research <task-id> --indices 0,2,5,7

# 步骤 7：生成播客
nlm audio create research --format deep_dive --length default --confirm

# 步骤 8：检查生成状态（播客需要 2-5 分钟）
nlm studio status research
# 重复直到状态显示 "completed"

# 步骤 9：从 studio status 输出获取播客 URL
```

---

## 工作流 4：学习资料生成

### 目标：从来源创建综合学习资料

```bash
# 前提条件：已添加来源的笔记本

# 步骤 1：验证来源存在
nlm source list <notebook-id>

# 步骤 2：生成学习指南报告
nlm report create <notebook-id> --format "Study Guide" --confirm
sleep 5

# 步骤 3：生成测验（10 个问题，中等难度）
nlm quiz create <notebook-id> --count 10 --difficulty 3 --confirm
sleep 3

# 步骤 4：生成抽认卡
nlm flashcards create <notebook-id> --difficulty medium --confirm
sleep 3

# 步骤 5：生成思维导图以进行视觉概览
nlm mindmap create <notebook-id> --title "主题概览" --confirm

# 步骤 6：检查所有生成的工件
nlm studio status <notebook-id>
```

---

## 工作流 5：快速问答会话

### 目标：询问关于来源的问题

```bash
# 选项 A：一次性问题
nlm notebook query <notebook-id> "这些来源中的主要主题是什么？"
# 捕获: 来自输出的 CONVERSATION_ID

# 追问（保持上下文）
nlm notebook query <notebook-id> "你能详细说明第一个主题吗？" --conversation-id <conv-id>

# 选项 B：交互式聊天会话
nlm chat start <notebook-id>
# 在 REPL 中:
#   自然地输入问题
#   /sources - 查看可用来源
#   /clear - 重置对话
#   /exit - 退出 REPL
```

---

## 工作流 6：Drive 文档同步

### 目标：保持 Drive 来源为最新

```bash
# 步骤 1：检查当前新鲜度状态
nlm source list <notebook-id> --drive
# 显示: 来源 ID、标题、类型、新鲜状态

# 步骤 2：快速检查（跳过新鲜度 API 调用）
nlm source list <notebook-id> --drive -S

# 步骤 3：查找过时的来源
nlm source stale <notebook-id>
# 列出自导入以来在 Drive 中被修改过的来源

# 步骤 4：同步所有过时的来源
nlm source sync <notebook-id> --confirm

# 步骤 5：仅同步特定来源
nlm source sync <notebook-id> --source-ids <id1>,<id2> --confirm

# 步骤 6：验证全部新鲜
nlm source stale <notebook-id>
# 应该显示没有过时的来源
```

---

## 工作流 7：多账户管理

### 目标：使用多个 Google 账户

```bash
# 步骤 1：登录工作账户
nlm login --profile work

# 步骤 2：登录个人账户
nlm login --profile personal

# 步骤 3：列出所有配置文件
nlm login profile list

# 步骤 4：切换默认配置文件
nlm login switch work

# 步骤 5：为命令使用特定配置文件
nlm notebook list --profile work
nlm notebook list --profile personal

# 步骤 6：在特定账户中创建笔记本
nlm notebook create "工作项目" --profile work
```

---

## 工作流 8：内容导出

### 目标：提取和导出来源内容

```bash
# 步骤 1：列出来源
nlm source list <notebook-id>

# 步骤 2：获取来源的 AI 摘要
nlm source describe <source-id>

# 步骤 3：获取原始文本内容
nlm source content <source-id>

# 步骤 4：导出到文件
nlm source content <source-id> --output ./export/source_content.txt

# 步骤 5：导出多个来源（脚本模式）
for id in $(nlm source list <notebook-id> --quiet); do
    nlm source content $id --output "./export/${id}.txt"
    sleep 1
done
```

---

## 工作流 9：演示准备

### 目标：生成演示材料

```bash
# 步骤 1：创建专注于的笔记本
nlm notebook create "Q4 演示准备"
nlm alias set pres <notebook-id>

# 步骤 2：添加相关来源
nlm source add pres --url "https://company.com/q4-results"
nlm source add pres --drive <slides-doc-id> --type slides
nlm source add pres --text "关键要点: ..." --title "要点"

# 步骤 3：生成幻灯片组
nlm slides create pres --format detailed --confirm
sleep 5

# 步骤 4：生成简报文档
nlm report create pres --format "Briefing Doc" --confirm
sleep 5

# 步骤 5：生成信息图表以进行视觉摘要
nlm infographic create pres --orientation landscape --detail standard --confirm

# 步骤 6：检查输出
nlm studio status pres
```

---

## 工作流 10：笔记本共享和协作

### 目标：与协作者共享笔记本

```bash
# 步骤 1：检查当前共享状态
nlm share status <notebook-id>

# 步骤 2：启用公共链接共享
nlm share public <notebook-id>
# 输出包括公共 URL

# 步骤 3：邀请特定协作者
nlm share invite <notebook-id> colleague@example.com --role viewer
nlm share invite <notebook-id> editor@example.com --role editor

# 步骤 4：完成后禁用公共链接
nlm share public <notebook-id> --off

# 步骤 5：验证共享设置
nlm share status <notebook-id>
```

---

## 工作流 11：使用笔记

### 目标：在笔记本中添加和管理个人笔记

```bash
# 步骤 1：创建笔记
nlm note create <notebook-id> --content "我对此主题的关键观察..." --title "关键见解"

# 步骤 2：列出所有笔记
nlm note list <notebook-id>

# 步骤 3：更新笔记
nlm note update <notebook-id> <note-id> --content "更新的观察..."

# 步骤 4：笔记包含在查询中
nlm notebook query <notebook-id> "我的个人笔记是什么？"

# 步骤 5：删除笔记（用户确认后）
nlm note delete <notebook-id> <note-id> --confirm
```

---

## 工作流 12：下载和导出工件

### 目标：在本地下载生成的内容或导出到 Google Docs/Sheets

```bash
# 步骤 1：检查可用工件
nlm studio status <notebook-id>

# 步骤 2：下载音频播客
nlm download audio <notebook-id> --output ./downloads/podcast.mp3

# 步骤 3：下载报告
nlm download report <notebook-id> --output ./downloads/report.md

# 步骤 4：以不同格式下载测验
nlm download quiz <notebook-id> --output quiz.json --format json
nlm download quiz <notebook-id> --output quiz.html --format html
nlm download flashcards <notebook-id> --output cards.html --format html

# 步骤 5：将数据表格导出到 Google Sheets
nlm export sheets <notebook-id> <artifact-id> --title "提取的数据"

# 步骤 6：将报告导出到 Google Docs
nlm export docs <notebook-id> <artifact-id> --title "我的报告"
```

---

## 工作流 13：清理和删除

### 目标：清理笔记本和工件

**⚠️ 重要：在执行删除命令之前，务必与用户确认！**

```bash
# 步骤 1：列出现有笔记本
nlm notebook list

# 步骤 2：删除前获取笔记本详细信息
nlm notebook get <notebook-id>
nlm source list <notebook-id>
nlm studio status <notebook-id>

# 步骤 3：删除特定工件（用户确认后）
# AI："您确定要从笔记本 Y 中删除工件 X 吗？"
nlm studio delete <notebook-id> <artifact-id> --confirm

# 步骤 4：删除特定来源（用户确认后）
# AI："您确定要删除来源 X 吗？"
nlm source delete <source-id> --confirm

# 步骤 5：删除整个笔记本（用户确认后）
# AI："这将永久删除笔记本 X 及其所有内容。继续吗？"
nlm notebook delete <notebook-id> --confirm

# 步骤 6：清理别名
nlm alias delete <alias-name>
```

---

## 工作流 14：脚本和自动化

### 目标：自动化重复任务

```bash
#!/bin/bash
# 示例：每日研究自动化

# 配置
NOTEBOOK_ID="abc123..."
QUERY="最新 AI 新闻 $(date +%Y-%m-%d)"

# 确保已身份验证
nlm login --check || nlm login

# 开始快速研究
nlm research start "$QUERY" --notebook-id $NOTEBOOK_ID --mode fast

# 等待完成
nlm research status $NOTEBOOK_ID --max-wait 60

# 从状态获取任务 ID
TASK_ID=$(nlm research status $NOTEBOOK_ID --max-wait 0 2>&1 | grep -oE 'task_id=[^ ]+' | cut -d= -f2)

# 导入所有来源
nlm research import $NOTEBOOK_ID $TASK_ID

# 生成简短音频摘要
nlm audio create $NOTEBOOK_ID --format brief --length short --confirm

# 检查状态
nlm studio status $NOTEBOOK_ID
```

---

## 速率限制指南

为避免达到 API 速率限制：

| 操作类型 | 推荐延迟 |
|---------------|-------------------|
| 来源添加 | 2 秒 |
| 内容生成 | 5 秒 |
| 研究操作 | 2 秒 |
| 查询操作 | 2 秒 |
| 批量操作 | 10 秒 |

**每日限制（免费层级）**：每天约 50 次查询/操作。

---

## 错误恢复模式

### 模式：失败时重新身份验证

```bash
# 尝试命令，失败则重新身份验证
nlm notebook list || (nlm login && nlm notebook list)
```

### 模式：指数退避重试

```bash
retry_command() {
    local max=3 delay=5
    for ((i=1; i<=max; i++)); do
        "$@" && return 0
        sleep $delay
        delay=$((delay * 2))
    done
    return 1
}

retry_command nlm audio create $NOTEBOOK_ID --confirm
```

### 模式：生成前检查

```bash
# 在生成前确保来源存在
SOURCE_COUNT=$(nlm source list $NOTEBOOK_ID --quiet | wc -l)
if [ "$SOURCE_COUNT" -gt 0 ]; then
    nlm audio create $NOTEBOOK_ID --confirm
else
    echo "错误：笔记本中没有来源"
fi
```
