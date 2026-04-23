# 百度邮箱 API 文档索引

本目录包含百度邮箱各 API 接口的详细参数说明、请求/响应示例和调用代码。

## 邮件查询

| 接口 | 方法 | 文档 | 说明 |
|------|------|------|------|
| `POST /ews/findItem` | `get_all_emails()` | [get_all_emails.md](./get_all_emails.md) | 查询邮件列表，支持按文件夹、主题、发件人、未读状态、时间范围筛选 |
| `POST /ews/getItemDetail` | `get_email_detail()` | [get_email_detail.md](./get_email_detail.md) | 查询指定邮件详情（正文、收发件人、抄送、附件等） |
| `POST /ews/getCollected` | `get_collected_email()` | [get_collected_email.md](./get_collected_email.md) | 获取用户星标（收藏）邮件列表，支持分页 |

## 邮件操作

| 接口 | 方法 | 文档 | 说明 |
|------|------|------|------|
| `POST /ews/send` | `send_email()` / `reply_email()` / `forward_email()` | [send_email.md](./send_email.md) | 发送新邮件、回复、回复全部、转发 |
| `POST /ews/deleteMail` | `delete_email()` | [delete_email.md](./delete_email.md) | 删除指定邮件 |
| `POST /ews/markRead` | `mark_read()` | [mark_read.md](./mark_read.md) | 标记邮件已读/未读 |
| `POST /ews/markFolderRead` | `mark_folder_read()` | [mark_folder_read.md](./mark_folder_read.md) | 标记目录下所有邮件已读/未读 |

## 文件夹管理

| 接口 | 方法 | 文档 | 说明 |
|------|------|------|------|
| `POST /ews/getAllFolders` | `get_all_folders()` | [get_all_folders.md](./get_all_folders.md) | 获取用户名下所有邮箱目录（支持递归子目录） |

## Agent 按需加载指引

根据用户意图读取对应文档：

| 用户意图 | 应读取的文档 |
|---------|-------------|
| 查看/搜索邮件 | [get_all_emails.md](./get_all_emails.md) |
| 查看邮件正文/详情 | [get_email_detail.md](./get_email_detail.md) |
| 发送/回复/转发邮件 | [send_email.md](./send_email.md) |
| 删除邮件 | [delete_email.md](./delete_email.md) |
| 标记邮件已读/未读 | [mark_read.md](./mark_read.md) |
| 标记目录所有邮件已读/未读 | [mark_folder_read.md](./mark_folder_read.md) |
| 查看邮箱文件夹 | [get_all_folders.md](./get_all_folders.md) |
| 查看星标/收藏邮件 | [get_collected_email.md](./get_collected_email.md) |
