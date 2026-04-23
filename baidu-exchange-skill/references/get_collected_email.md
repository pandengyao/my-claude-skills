# 获取用户的星标邮件

根据用户输入的条件，获取用户星标邮件列表

## API信息

- **接口**: `POST /ews/getCollected`
- **Python方法**: `client.get_collected_email(itemId='itemId')`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| pageSize | int | 否* | 每页条数 |
| offset | int | 否* | 偏移量 |

*注：pageSize不传默认为10，offSet不传默认为0*



## 响应示例

```json
{
    "itemIdList": [
        {
            "itemId": "邮件ID",
            "subject": "邮件主题",
            "from": "发件人",
            "to": [
                "收件人"
            ],
            "receivedTime": "接收时间",
            "isRead": false,
            "preview": null,
            "summary": "摘要"
        }
    ],
    "total": 总数
}
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 根据邮件ID删除
result = client.get_collected_email()
```


## 使用场景

- 获取用户星标邮件列表
