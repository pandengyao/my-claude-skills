<!-- nlm-skill-start -->
## NLM - NotebookLM CLI 专家

**触发关键词：** "nlm"、"notebooklm"、"notebook lm"、"podcast"、"audio overview"、"research"

Google NotebookLM 自动化的专家助手，通过 CLI 操作。当用户想要创建/管理笔记本、添加来源（URL、YouTube、文本、Google Drive）、生成 AI 内容（播客、报告、测验、抽认卡、思维导图、幻灯片、信息图表、视频、数据表格）、进行研究或与来源聊天时使用。

### 快速参考

```bash
nlm login                    # 使用 NotebookLM 进行身份验证
nlm notebook create "标题"  # 创建笔记本
nlm source add <id> --url "https://..."  # 添加网页来源
nlm audio create <id> --confirm          # 生成播客
nlm research start "查询" --notebook-id <id>  # 发现来源
```

### 关键规则

1. **始终先进行身份验证**：操作前运行 `nlm login`
2. **会话约 20 分钟后过期**：如果身份验证失败，请重新运行 `nlm login`
3. **生成/删除命令需要 `--confirm`**
4. **从输出中捕获 ID** 用于后续操作
5. **使用 `nlm alias set`** 简化 UUID
6. **⚠️ 永远不要自动删除**：执行 `nlm delete` 前务必询问用户
7. **⚠️ 永远不要使用 `nlm chat start`**：它是交互式 REPL。改用 `nlm notebook query`

### 常见工作流

**研究 → 播客流程：**
```bash
nlm notebook create "AI 研究"
nlm alias set ai <notebook-id>
nlm research start "AI 趋势" --notebook-id ai --mode deep
nlm research status ai
nlm research import ai <task-id>
nlm audio create ai --confirm
nlm studio status ai
```

**快速内容摄取：**
```bash
nlm source add <id> --url "https://example.com"
nlm source add <id> --text "笔记..." --title "我的笔记"
nlm source add <id> --drive <doc-id>
```

**学习资料：**
```bash
nlm report create <id> --format "学习指南" --confirm
nlm quiz create <id> --count 10 --confirm
nlm flashcards create <id> --confirm
```

### 完整文档

有关完整的命令参考、故障排除和工作流，请安装完整技能：

```bash
# 通过 uv 安装
uv tool install notebooklm-mcp-cli

# 然后为您的 AI 工具安装技能
nlm skill install <tool>  # claude-code、opencode、gemini-cli、antigravity、codex
```

或直接查看：`nlm --ai`

<!-- nlm-skill-end -->
