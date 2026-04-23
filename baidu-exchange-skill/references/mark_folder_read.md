# 标记目录所有邮件已读/未读

标记目录下所有邮件的已读/未读状态

## API信息

- **接口**: `POST /ews/markFolderRead`
- **Python方法**: `client.mark_folder_read(folder_id='inbox', read_state=True)`

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| folderId | String | 是 | - | 目录ID（支持 folderId 或 inbox 这种名称） |
| readState | Boolean | 是 | - | 目标状态：true(标记为已读)、false(标记为未读) |

## 响应示例

```json
true
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 标记收件箱所有邮件为已读
result = client.mark_folder_read(folder_id="inbox")

# 标记指定目录所有邮件为未读
result = client.mark_folder_read(folder_id="AAMkAGU2...", read_state=False)
```

## 使用场景

- 一键标记收件箱所有邮件为已读
- 标记指定目录下所有邮件为已读/未读
