# 发送/转发/回复邮件

根据用户输入的信息，进行邮件的发送、转发与回复等操作

## API信息

- **接口**: `POST /ews/send`
- **Python方法**: `client.send(action='action', to='to', cc='cc', bcc='bcc', subject='subject', body='body', originalItemId='originalItemId', forwardTo='forwardTo')`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| action | string | 否* | 操作类型：send/reply/replyAll/forward|
| to |  List<String> | 否* | 收件人列表|
| cc |  List<String> | 否* | 抄送人列表|
| bcc |  List<String> | 否* | 密送人列表|
| subject | string | 否* | 邮件主题 |
| isHtml | boolean | 否* | 是否是html 默认：是 |
| body | string | 否* | 邮件内容 |
| originalItemId | string | 否* | 原始邮件ID|
| forwardTo | string | 否* | 转发人列表，多个用换行符隔开|

*注：if from为空，则使用当前登录账号作为发件人,若action为reply/replyAll，则使用原始邮件发件人作为发件人,若action不传则action为send*

## 请求示例
### 新邮件

```json
{
  "action": "send",
  "to": ["lisi@baidu.com", "wangwu@baidu.com"],
  "cc": ["zhaoliu@baidu.com"],
  "subject": "项目周报",
  "body": "本周项目进展如下..."
}
```

### 回复邮件

```json
{
  "action": "reply",
  "originalItemId": "AAMkAGU2...",
  "body": "好的，收到。"
}
```

### 回复全部

```json
{
  "action": "replyAll",
  "originalItemId": "AAMkAGU2...",
  "body": "感谢大家的回复。"
}
```

### 转发邮件

```json
{
  "action": "forward",
  "originalItemId": "AAMkAGU2...",
  "forwardTo": ["sunqi@baidu.com"],
  "body": "请查收。"
}
```

## 响应示例

```json
{
  "success": true,
  "message": "邮件发送成功"
}
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 发送新邮件（默认HTML格式）
client.send_email(
    to=["zongshuai@baidu.com"],
    subject="项目周报",
    body="本周项目进展如下..."
)

# 发送纯文本邮件
client.send_email(
    to=["zongshuai@baidu.com"],
    subject="项目周报",
    body="本周项目进展如下...",
    is_html=False
)

# 回复邮件
client.reply_email(original_item_id="AAMkAGU2...", body="好的，收到。")

# 回复全部
client.reply_email(original_item_id="AAMkAGU2...", body="感谢大家。", reply_all=True)

# 转发邮件
client.forward_email(
    original_item_id="AAMkAGU2...",
    forward_to=["zongshuai@baidu.com"],
    body="请查收。"
)
```
## 使用场景

- 根据用户的场景进行邮件的发送、转发、回复等操作
