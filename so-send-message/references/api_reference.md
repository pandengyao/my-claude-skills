# 群消息发送API参考

## 概述

本技能提供向如流(Hi)群组发送消息的能力，支持文本、Markdown和图片消息格式。

> **📢 开箱即用**: 本技能已内置默认应用凭证，无需配置即可直接使用。如需自定义凭证，可通过命令行参数或代码传入。

## API接口

### 1. 获取应用访问令牌

**Endpoint:** `POST http://apiin.im.baidu.com/api/v1/auth/app_access_token`

**请求参数:**
```json
{
    "app_key": "应用Key",
    "app_secret": "应用Secret的MD5小写"
}
```

**响应示例:**
```json
{
    "code": "ok",
    "data": {
        "app_access_token": "xxxxxxxxxxxx",
        "expires_in": 7200
    }
}
```

### 2. 发送群消息

**Endpoint:** `POST http://apiin.im.baidu.com/api/v1/robot/msg/groupmsgsend`

**请求头:**
```
Authorization: Bearer-{app_access_token}
Content-Type: application/json; charset=utf-8
LOGID: {唯一日志ID}
```

**请求体结构:**
```json
{
    "message": {
        "header": {
            "toid": "群组ID",
            "totype": "GROUP",
            "msgtype": "消息类型",
            "clientmsgid": 时间戳毫秒数,
            "role": "robot"
        },
        "body": [
            {
                "type": "消息体类型",
                "content": "消息内容"
            }
        ]
    }
}
```

## 消息类型

### 1. 文本消息 (TEXT)

**请求体示例:**
```json
{
    "message": {
        "header": {
            "toid": "123456789",
            "totype": "GROUP",
            "msgtype": "TEXT",
            "clientmsgid": 1700000000000,
            "role": "robot"
        },
        "body": [
            {
                "type": "TEXT",
                "content": "这是一条文本消息"
            }
        ]
    }
}
```

### 2. Markdown消息 (MD)

**请求体示例:**
```json
{
    "message": {
        "header": {
            "toid": "123456789",
            "totype": "GROUP",
            "msgtype": "MD",
            "clientmsgid": 1700000000000,
            "role": "robot"
        },
        "body": [
            {
                "type": "MD",
                "content": "# 标题\n\n* 列表项1\n* 列表项2\n\n**加粗文本**"
            }
        ]
    }
}
```

### 3. 图片消息 (IMAGE)

**请求体示例:**
```json
{
    "message": {
        "header": {
            "toid": "123456789",
            "totype": "GROUP",
            "msgtype": "IMAGE",
            "clientmsgid": 1700000000000,
            "role": "robot"
        },
        "body": [
            {
                "type": "IMAGE",
                "content": "https://example.com/image.jpg"
            }
        ]
    }
}
```

## Markdown语法支持

如流支持以下Markdown语法：

### 标题
```markdown
# 一级标题
## 二级标题
### 三级标题
```

### 文本样式
```markdown
**加粗文本**
*斜体文本*
~~删除线文本~~
`行内代码`
```

### 列表
```markdown
* 无序列表项
* 无序列表项

1. 有序列表项
2. 有序列表项
```

### 链接和图片
```markdown
[链接文本](https://example.com)
![图片描述](https://example.com/image.jpg)
```

### 引用
```markdown
> 引用文本
> 多行引用
```

### 代码块
````markdown
```python
def hello():
    print("Hello World")
```
````

### 表格
```markdown
| 表头1 | 表头2 |
|-------|-------|
| 单元格1 | 单元格2 |
| 单元格3 | 单元格4 |
```

## 响应格式

### 成功响应
```json
{
    "code": "ok",
    "data": {
        "errcode": 0,
        "errmsg": "ok",
        "data": {
            "messageid": 1856190392527088293,
            "msgseqid": 300018341,
            "ctime": 1770201103763
        }
    }
}
```

### 错误响应
```json
{
    "code": "error",
    "message": "错误描述"
}
```

## 常见错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 10001 | 无效的app_key或app_secret | 检查应用配置 |
| 10002 | 访问令牌过期 | 重新获取token |
| 10003 | 无效的token | 重新获取token |
| 20001 | 群组不存在 | 检查群组ID |
| 20002 | 机器人不在群组中 | 将机器人加入群组 |
| 20003 | 机器人被禁言 | 解除禁言 |
| 30001 | 消息格式错误 | 检查消息结构 |
| 30002 | 消息内容过长 | 缩短消息长度 |
| 30003 | 包含敏感词 | 修改消息内容 |

## 限制说明

1. **频率限制**：单个机器人每分钟最多发送30条消息
2. **消息长度**：
   - 文本消息：最大2000字符
   - Markdown消息：最大5000字符
3. **图片限制**：
   - 支持格式：JPG、PNG、GIF
   - 最大大小：10MB
   - 建议尺寸：不超过2000x2000像素
4. **token有效期**：7200秒（2小时）

## 最佳实践

### 1. Token管理
- 缓存token并重用，避免频繁获取
- 在token过期前刷新
- 实现token自动刷新机制

### 2. 错误处理
- 实现重试机制（建议最多重试3次）
- 记录详细的错误日志
- 对网络超时进行特殊处理

### 3. 消息优化
- 长消息使用Markdown格式，提高可读性
- 重要消息添加适当的格式强调
- 避免发送重复或过于频繁的消息

### 4. 安全性
- 不要在代码中硬编码敏感信息
- 使用环境变量或配置文件存储app_key和app_secret
- 定期更新应用凭证

## 调试技巧

1. **启用详细日志**：使用`--verbose`参数查看详细请求信息
2. **测试连接**：先获取token测试API连通性
3. **验证群组**：确保机器人已加入目标群组
4. **检查权限**：确认机器人未被禁言
5. **内容审查**：避免包含平台敏感词