# 获取邮箱的所有目录

获取用户名下的所有邮箱目录

## API信息

- **接口**: `POST /ews/getAllFolders`
- **Python方法**: `client.get_all_folders(deep=True)`

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| deep | boolean | 否* | 是否递归查询子目录|

*注：deep 不传默认为true*

## 响应示例

```json
[
  {
    "id": "目录ID",
    "displayName": "目录名",
    "parentId": "父目录ID",
    "childFolderCount": 2,
    "children": [
      {
        "id": "important",
        "displayName": "重要邮件",
        "parentId": "inbox",
        "childFolderCount": 0,
        "children": []
      }
    ]
  },
  {
    "id": "sent",
    "displayName": "已发送",
    "parentId": null,
    "childFolderCount": 0,
    "children": []
  }
]
```

## Python调用示例

```python
from scripts import MailApiClient

client = MailApiClient()

# 递归获取所有目录（默认 deep=True）
result = client.get_all_folders()

# 只获取顶级目录
result = client.get_all_folders(deep=False)
```

## 使用场景

- 获取用户名下的所有邮箱目录
