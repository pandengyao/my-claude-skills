# 标记邮件已读/未读

标记指定邮件的已读/未读状态

## API信息

- **接口**: `POST /ews/markRead`
- **Python方法**: `client.mark_read(item_id='itemId', is_read=True)`

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| itemId | String | 是 | - | 邮件ID |
| isRead | Boolean | 否 | true | 是否已读：true(已读)、false(未读) |

## 响应示例

```json
true
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 标记邮件为已读
result = client.mark_read(item_id="AAMkAGU2...")

# 标记邮件为未读
result = client.mark_read(item_id="AAMkAGU2...", is_read=False)
```

## 使用场景

- 标记指定邮件为已读
- 标记指定邮件为未读
