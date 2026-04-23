# NotebookLM CLI - 故障排除指南

本文档为使用 `nlm` CLI 时的常见问题提供详细解决方案。

## 快速诊断

| 症状 | 可能原因 | 快速修复 |
|---------|--------------|-----------|
| "Cookies have expired" | 会话超时 | `nlm login` |
| "Notebook not found" | 无效/过时 ID | `nlm notebook list` |
| "Source not found" | 无效来源 ID | `nlm source list <nb-id>` |
| Chrome 无法打开 | 端口冲突 | 关闭现有 Chrome，重试 |
| "Research already in progress" | 待处理任务 | `--force` 或导入现有结果 |
| "nodename nor servname" | 网络被阻止 | 参见 [沙盒用户](#沙盒环境) |
| 命令永远挂起 | 网络/身份验证问题 | Ctrl+C、`nlm login` |

---

## 身份验证问题

### 会话过期

**症状：**
```
Error: Cookies have expired. Please run 'nlm login' to re-authenticate.
Error: authentication may have expired
```

**原因：** NotebookLM 会话持续约 20 分钟。

**解决方案：**
```bash
nlm login
```

**预防：** 对于长时间运行的脚本，实施定期重新身份验证：
```bash
# 在关键操作前检查身份验证
nlm login --check || nlm login
```

### Chrome 无法启动

**症状：**
- `nlm login` 挂起，没有浏览器窗口
- 错误提示找不到 Chrome

**解决方案：**

1. **确保已安装 Chrome 并在 PATH 中：**
   ```bash
   which google-chrome || which chromium
   # 在 macOS 上，Chrome 位于 /Applications/Google Chrome.app
   ```

2. **关闭现有 Chrome 实例：**
   ```bash
   pkill -f "Chrome"
   # 等待片刻，然后重试
   nlm login
   ```

3. **端口冲突（端口 9222 正在使用）：**
   CLI 会自动尝试端口 9222-9231，但如果所有端口都被阻止：
   ```bash
   lsof -i :9222
   # 终止使用该端口的进程
   kill -9 <PID>
   ```

### 配置文件问题

**症状：** "Profile not found" 或使用了错误的账户。

**解决方案：**

1. **列出现有配置文件：**
   ```bash
   nlm login profile list
   ```

2. **创建新配置文件：**
   ```bash
   nlm login --profile work
   ```

3. **删除损坏的配置文件：**
   ```bash
   nlm login profile delete <profile-name>
   nlm login --profile <profile-name>
   ```

4. **切换默认配置文件：**
   ```bash
   nlm login switch <profile-name>
   ```

5. **检查当前会话：**
   ```bash
   nlm login --check
   ```

---

## 网络问题

### 沙盒环境

**症状：**
```
Error: Request failed: [Errno 8] nodename nor servname provided, or not known
Hint: Check your internet connection.
```

**原因：** 在阻止网络访问的沙盒环境（OpenAI Codex、容器）中运行。

**OpenAI Codex 的解决方案：**

添加到 `~/.codex/config.toml`：
```toml
[sandbox_workspace_write]
network_access = true
```

或使用完全网络访问运行：
```bash
codex exec --sandbox danger-full-access "nlm notebook list"
```

**Docker/容器的解决方案：**
确保容器具有网络访问权限并可以访问 `notebooklm.google.com`。

### 速率限制

**症状：**
```
Error: Rate limit exceeded
```

**原因：** 短时间内 API 调用过多。免费层级：每天约 50 次查询。

**解决方案：**

1. **等待并重试：**
   ```bash
   sleep 30
   # 重试命令
   ```

2. **在脚本中实施节流：**
   ```bash
   # 操作之间等待 2 秒
   nlm source add $ID --url "..." && sleep 2
   nlm source add $ID --url "..." && sleep 2
   ```

3. **尽可能使用批量操作：**
   - 使用 `nlm research import` 一次导入多个来源
   - 使用 `nlm source sync` 一次同步所有过时来源

---

## 来源问题

### 来源未找到

**症状：**
```
Error: Source not found
```

**解决方案：**

1. **验证来源存在：**
   ```bash
   nlm source list <notebook-id>
   ```

2. **检查正确的笔记本：**
   来源范围限于笔记本。确保您使用的是正确的笔记本 ID。

3. **来源可能已被删除：**
   如果来源最近被删除，则它不再存在。

### Drive 来源问题

**症状：** Drive 文档添加失败或显示错误内容。

**解决方案：**

1. **验证文档 ID：**
   从 URL 中提取：`https://docs.google.com/document/d/[DOC_ID]/edit`

2. **指定正确的类型：**
   ```bash
   nlm source add <nb-id> --drive <doc-id> --type slides  # 用于 Slides
   nlm source add <nb-id> --drive <doc-id> --type sheets  # 用于 Sheets
   nlm source add <nb-id> --drive <doc-id> --type pdf     # 用于 PDF
   ```

3. **检查权限：**
   确保您的 Google 账户有权访问 Drive 文档。

4. **大型文档超时：**
   非常大的文档（100+ 张幻灯片）可能需要更长时间。CLI 有 120 秒的超时时间。

### 过时的 Drive 来源

**症状：** Drive 来源内容已过期。

**解决方案：**
```bash
# 检查哪些来源已过时
nlm source stale <notebook-id>

# 同步所有过时来源
nlm source sync <notebook-id> --confirm

# 同步特定来源
nlm source sync <notebook-id> --source-ids <id1>,<id2> --confirm
```

---

## 研究问题

### 研究已在进行中

**症状：**
```
Error: Research already in progress
```

**解决方案：**

1. **等待完成：**
   ```bash
   nlm research status <notebook-id>
   ```

2. **导入现有结果：**
   ```bash
   nlm research status <notebook-id> --full  # 获取任务 ID
   nlm research import <notebook-id> <task-id>
   ```

3. **强制新研究：**
   ```bash
   nlm research start "查询" --notebook-id <id> --force
   ```

### 研究耗时过长

**预期持续时间：**
- 快速模式：约 30 秒
- 深度模式：约 5 分钟

**如果超过这些时间：**

1. **不等待就检查状态：**
   ```bash
   nlm research status <notebook-id> --max-wait 0
   ```

2. **尝试更具体的查询：**
   更广泛的查询需要更长时间。缩小搜索词范围。

---

## 生成问题

### 工件仍在生成中

**症状：** `nlm studio status` 显示 "in_progress" 状态的时间过长。

**预期生成时间：**
- 报告、测验、抽认卡：30-60 秒
- 音频播客：2-5 分钟
- 视频：3-7 分钟
- 深度研究：4-5 分钟

**解决方案：** 继续轮询：
```bash
nlm studio status <notebook-id>
```

### 生成失败

**症状：** 工件状态显示 "failed" 或 (✗)。

**可能的原因和解决方案：**

1. **笔记本中没有来源：**
   ```bash
   nlm source list <notebook-id>
   # 如果为空，首先添加来源
   ```

2. **来源太短：**
   为来源添加更充实的内容。

3. **重试生成：**
   ```bash
   # 删除失败的工件
   nlm studio delete <notebook-id> <artifact-id> --confirm
   # 重新生成
   nlm audio create <notebook-id> --confirm
   ```

### 缺少 --confirm 标志

**症状：**
```
Error: Missing required flag: --confirm
```

**原因：** 所有生成和删除命令都需要明确的确认。

**解决方案：** 添加 `--confirm` 或 `-y`：
```bash
nlm audio create <notebook-id> --confirm
# 或
nlm audio create <notebook-id> -y
```

---

## 命令语法问题

### 参数顺序错误

**常见错误：**

```bash
# 错误：research start 没有 --notebook-id
nlm research start "查询" <notebook-id>

# 正确：--notebook-id 是必需标志
nlm research start "查询" --notebook-id <notebook-id>
```

```bash
# 错误：data-table 没有描述
nlm data-table create <notebook-id> --confirm

# 正确：描述是必需的位置参数
nlm data-table create <notebook-id> "提取所有日期" --confirm
```

### 自定义聊天提示没有 --goal

**症状：**
```
Error: --prompt is required when goal is 'custom'
```

**解决方案：**
```bash
# 正确：同时指定 --goal custom 和 --prompt
nlm chat configure <id> --goal custom --prompt "充当导师..."
```

---

## 获取更多帮助

1. **检查命令帮助：**
   ```bash
   nlm <command> --help
   ```

2. **获取完整的 AI 文档：**
   ```bash
   nlm --ai
   ```

3. **检查版本：**
   ```bash
   nlm --version
   ```

4. **GitHub 问题：**
   https://github.com/jacob-bd/notebooklm-cli/issues
