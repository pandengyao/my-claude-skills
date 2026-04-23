# 查询指定文件夹中的邮件

根据用户输入的文件夹名称查询文件夹中的邮件列表信息

## API信息

- **接口**: `POST /ews/findItem`
- **Python方法**: `client.get_all_emails(folder='inbox', pageSize=50)`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| folder | string | 否* | 邮箱名称：inbox(收件箱)、sent(已发送)、drafts(草稿)、deleted(已删除)、junk(垃圾邮件)、all(所有目录)|
| folderId | String | 否* | 目录ID：对于非folder中定义的目录，需要先通过目录接口获取到id，然后再传进来|
| pageSize | int | 否* | 每页数量|
| subject | string | 否* | 邮件主题 |
| body | string | 否* | 邮件内容 |
| unreadOnly | boolean | 否* | 是否只查询未读邮件|
| lastHours | int | 否* | 最近多少小时|
| from | string | 否* | 发件人，如果是中文，自动转换成拼音|
| offset | int | 否* | 偏移量|
| startTime | string | 否* | 起始时间，ISO 8601格式，如 2026-04-01T00:00:00+08:00|
| endTime | string | 否* | 结束时间，ISO 8601格式，如 2026-04-02T00:00:00+08:00|


*注：folder 不传默认为inbox*

## 响应示例

```json
{
    "itemIdList": [
        {
            "itemId": "邮件ID",
            "subject": "邮件主题",
            "body": "邮件内容",
            "from": "发件人",
            "to": [
                "收件人"
            ],
            "receivedTime": "接收时间",
            "isRead": false,
            "preview": null,
            "folderId": "AAMkADZm...",
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

# 查询收件箱邮件（默认）
result = client.get_all_emails(folder="inbox")

# 指定每页条数
result = client.get_all_emails(folder="inbox", pageSize=10)

# 按发件人和主题筛选
result = client.get_all_emails(folder="inbox", form="张三", subject="周报")

# 查询未读邮件
result = client.get_all_emails(unread_only=True)

# 使用 folderId 查询自定义目录
result = client.get_all_emails(folderId="some_folder_id")

# 按发件人和邮件正文筛选
result = client.get_all_emails(folder="inbox", form="张三", body="周报")

# 按时间段查询
result = client.get_all_emails(folder="inbox", start_time="2026-04-01T00:00:00+08:00", end_time="2026-04-02T00:00:00+08:00")
```

## 使用场景

- 获取指定文件夹中的邮件信息
- 批量获取指定文件夹中的邮件信息
