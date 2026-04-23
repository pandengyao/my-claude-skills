# 查询指定邮件详情

根据用户输入的信息查询指定邮件的详情

## API信息

- **接口**: `POST /ews/getItemDetail`
- **Python方法**: `client.get_email_detail(itemId='itemId', folder='inbox')`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| itemId | string | 是* | 邮件ID |
| folder | string | 否* | 邮件目录, 可选值有：inbox（收件箱）、sent（已发送）、drafts（草稿箱）、deleted（已删除）、deleted_items（已永久删除）、junk（垃圾邮件）、all（所有目录）|

*注：folder 不传默认为inbox

## 响应示例

```json
{
    "id": "邮件ID",
    "subject": "邮件主题",
    "sender": "发件人",
    "toRecipients": [
        "收件人列表"
    ],
    "ccRecipients": [
        "抄送人列表"
    ],
    "bccRecipients": [
		"密送人列表"
	],
    "body": "<html>邮件正文</html>",
    "datetimeSent": "发送时间",
    "datetimeReceived": "接收时间",
    "isRead": false,
    "hasAttachments": true
}
```
*注：isRead 是否已读，hasAttachments 是否有附件*

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 使用邮件ID查询详情
result = client.get_email_detail(item_id="AAMkAGU2...")

# 指定邮件所在目录
result = client.get_email_detail(item_id="AAMkAGU2...", folder="sent")
```

## 使用场景

- 获取指定邮件的详情信息
- 根据用户指定的邮件ID与目录信息查询指定邮件的详情信息
