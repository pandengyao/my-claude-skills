# 删除用户指定的邮件

根据用户输入的条件，删除用户指定的邮件

## API信息

- **接口**: `POST /ews/deleteMail`
- **Python方法**: `client.delete_email(itemId='itemId')`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| itemId | string | 是* | 邮件ID |


## 响应示例

```json
{
  "success": true,
  "message": "邮件删除成功"
}
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 根据邮件ID删除
result = client.delete_email(item_id="AAMkAGU2...")
```


## 使用场景

- 根据邮件ID删除指定邮件信息
