# 百度邮箱助手 Skill

百度企业邮箱的 Agent Skill，通过自然语言管理邮件，
支持收发邮件、查看未读、管理文件夹等操作。

## 目录结构

```
baidu-dumail-skill/
├── SKILL.md                        # Skill 主入口文档（Agent 首先读取）
├── README.md                       # 项目说明
├── requirements.txt                # Python 依赖
├── contact_memory_rules.md         # 联系人记忆规则
├── assets/
│   └── template.md                 # Markdown 输出模板
├── scripts/                        # Python 客户端
│   ├── __init__.py                 # 包入口，导出 MailApiClient
│   ├── config.py                   # 配置加载（config.yaml + SKILL.md）
│   ├── auth.py                     # 认证管理（Ugate-Token）
│   ├── http_client.py              # HTTP 请求（自动重试 + token 刷新）
│   ├── formatter.py                # Markdown 格式化
│   ├── telemetry.py                # Prompt 异步上报
│   ├── mail_api_client.py          # MailApiClient 门面类
│   └── config.yaml                 # 运行时配置
└── references/                     # API 详细文档（按需加载）
    ├── API_INDEX.md                # API 索引
    ├── MEMORY.md                   # 联系人记忆存储
    ├── get_all_emails.md           # 查询邮件列表
    ├── get_email_detail.md         # 查询邮件详情
    ├── get_all_folders.md          # 获取邮箱目录
    ├── get_collected_email.md      # 获取星标邮件
    ├── delete_email.md             # 删除邮件
    └── send_email.md               # 发送邮件
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from scripts import MailApiClient

client = MailApiClient()

# 查询收件箱邮件（支持多条件筛选）
emails = client.get_all_emails(folder="inbox", pageSize=10)
emails = client.get_all_emails(unread_only=True, last_hours=24)
emails = client.get_all_emails(from="张三", subject="周报")

# 查看邮件详情
detail = client.get_email_detail(item_id="AAMkAGU2...")

# 发送邮件
client.send_email(
    to=["lisi@baidu.com"],
    subject="会议通知",
    body="明天下午3点开会"
)

# 回复邮件
client.reply_email(
    original_item_id="AAMkAGU2...",
    body="好的，收到。"
)

# 转发邮件
client.forward_email(
    original_item_id="AAMkAGU2...",
    forward_to=["wangwu@baidu.com"]
)

# 获取所有邮箱目录
folders = client.get_all_folders(deep=True)

# 删除邮件
result = client.delete_email(item_id="AAMkAGU2...")

# 获取星标邮件
collected = client.get_collected_email(pageSize=10)

# Markdown 格式化输出
print(client.format_emails_markdown(emails, folder="inbox"))
print(client.format_email_detail_markdown(detail))
print(client.format_folders_markdown(folders))
print(client.format_collected_emails_markdown(collected))
```

## 模块架构

采用组合（Composition）模式，按职责拆分为独立模块：

```
MailApiClient（门面类）
  ├── AuthManager        认证管理：token 获取/解析/刷新/缓存
  ├── HttpClient         HTTP 请求：POST + 自动重试 + token 刷新
  ├── MailFormatter      格式化：API 响应 → Markdown 输出
  └── TelemetryReporter  遥测：异步上报用户 prompt
```

| 模块 | 文件 | 职责 |
|------|------|------|
| `config` | `scripts/config.py` | 加载 config.yaml、解析 SKILL.md |
| `AuthManager` | `scripts/auth.py` | Ugate-Token 生命周期管理 |
| `HttpClient` | `scripts/http_client.py` | 带认证重试的 HTTP POST |
| `MailFormatter` | `scripts/formatter.py` | 邮件/文件夹 Markdown 格式化 |
| `TelemetryReporter` | `scripts/telemetry.py` | Prompt 异步上报 |
| `MailApiClient` | `scripts/mail_api_client.py` | 门面类，组合委托 |

## 设计理念

### 渐进式加载

- **SKILL.md** — 功能概览、意图识别、调用指南，Agent 首次加载
- **references/** — 各 API 的详细参数与示例，Agent 按需读取
- **assets/template.md** — Markdown 输出模板，集中管理样式

### Agent 工作流程

```
1. 用户触发邮箱相关操作
2. Agent 读取 SKILL.md 了解能力全貌
3. 根据用户意图按需读取 references/ 下的 API 文档
4. 调用 MailApiClient 完成任务，格式化输出结果
```

## 认证说明

- 认证方式：`Ugate-Token`（个人身份认证）
- Token 来源：优先从本地文件
  `~/.config/uuap/.eac_ugate_token_{username}` 读取
- 自动刷新：认证失败时自动调用 `get-ugate-token` Skill
  获取新 Token（最多重试 2 次）
- 环境变量：需设置 `SANDBOX_USERNAME` 或 `BAIDU_CC_USERNAME`

## API 文档索引

| 接口 | 方法 | 文档 |
|------|------|------|
| `POST /ews/findItem` | `get_all_emails()` | [get_all_emails.md](./references/get_all_emails.md) |
| `POST /ews/getItemDetail` | `get_email_detail()` | [get_email_detail.md](./references/get_email_detail.md) |
| `POST /ews/send` | `send_email()` | [send_email.md](./references/send_email.md) |
| `POST /ews/getAllFolders` | `get_all_folders()` | [get_all_folders.md](./references/get_all_folders.md) |
| `POST /ews/getCollected` | `get_collected_email()` | [get_collected_email.md](./references/get_collected_email.md) |
| `POST /ews/deleteMail` | `delete_email()` | [delete_email.md](./references/delete_email.md) |

## 联系人记忆

当用户表达联系人偏好（如"XXX是我领导"、"记住XXX的邮箱"）时，
Agent 会自动将信息记录到 `references/MEMORY.md`。

详细规则见 [contact_memory_rules.md](./contact_memory_rules.md)。
