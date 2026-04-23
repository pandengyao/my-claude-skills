---
name: weiyun-log-query
description: 从微云 LogHub API 查询日志，支持认证签名。当用户需要搜索、查询或检索微云/百度云日志系统的日志时使用此技能。支持按应用名、服务名、消息关键词和时间范围过滤。可通过 Python 脚本被其他技能程序化调用。
---

# 微云日志查询

从微云 LogHub API 查询日志，自动处理认证签名。

## 概述

此技能提供一个基于 Python 的工具，用于从微云 LogHub API 查询日志。自动处理认证（AK/SK 签名生成）、查询构建和响应解析。

## 使用场景

当以下情况时使用此技能：
- 用户需要从微云/百度云日志系统查询日志
- 用户提到"微云日志"、"loghub"、"eci-cloud-loghub"
- 用户想按应用名、服务名或消息内容搜索日志
- 其他技能需要程序化查询日志

## 配置

使用前，在技能目录创建 `config.json` 文件，填入凭证：

```json
{
  "ak": "your_access_key",
  "sk": "your_secret_key"
}
```

**安全提示：** `config.json` 文件已被 .gitignore 排除。切勿将凭证提交到版本控制。

## 使用方法

### 命令行接口

```bash
# 基本查询
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --app new-gc-dashboard-qa --message "error"

# 相对时间查询（最近1小时）
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --last 1h

# 绝对时间戳查询（毫秒）
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --start 1766661652540 --end 1766662552541

# 多个消息关键词
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --message "requestId" --message "error"

# 自定义匹配短语
~/py312/bin/python3 scripts/weiyun_log_query.py --match weiyun_prod_name new-gc-qa --match weiyun_env qa

# 输出格式
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --last 1h --output json    # 原始 JSON
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --last 1h --output logs    # 仅日志消息
~/py312/bin/python3 scripts/weiyun_log_query.py --product new-gc-qa --last 1h --output pretty  # 美化 JSON（默认）
```

### 程序化调用（从其他技能）

其他技能可以直接导入并使用查询函数：

```python
import sys
sys.path.insert(0, '/path/to/weiyun-log-query/scripts')
from weiyun_log_query import query_logs, load_config

# 加载凭证
config = load_config()

# 查询日志
result = query_logs(
    api_url='https://developer.weiyun.baidu.com/eci-cloud-loghub/v1/openApi/queryLog/conditionQuery',
    ak=config['ak'],
    sk=config['sk'],
    must={
        'matchPhraseList': [
            {'weiyun_prod_name': 'new-gc-qa'},
            {'weiyun_app_name': 'new-gc-dashboard-qa'}
        ],
        'participleMatchList': [
            {'message': 'requestId'}
        ]
    },
    start_time='1766661652540',
    end_time='1766662552541'
)

# 处理结果
for log in result.get('data', {}).get('logInfoList', []):
    print(log.get('message'))
```

### 使用 exec 工具

从任何技能都可以通过 exec 工具执行脚本：

```json
{
  "command": "~/py312/bin/python3 /home/gem/.openclaw/skills/weiyun-log-query/scripts/weiyun_log_query.py --product new-gc-qa --last 1h --output json",
  "workdir": "/home/gem/.openclaw/skills/weiyun-log-query"
}
```

## 参数说明

### 查询条件

| 参数 | 描述 | 示例 |
|------|------|------|
| `--product` | 应用名（weiyun_prod_name） | `new-gc-qa` |
| `--app` | 服务名（weiyun_app_name） | `new-gc-dashboard-qa` |
| `--message` | 消息关键词（可多次使用） | `error`, `requestId` |
| `--match KEY VALUE` | 自定义匹配短语（可多次使用） | `--match weiyun_env qa` |

### 时间范围

| 参数 | 描述 | 示例 |
|------|------|------|
| `--start` | 开始时间戳（毫秒） | `1766661652540` |
| `--end` | 结束时间戳（毫秒） | `1766662552541` |
| `--last` | 相对时间 | `1h`, `30m`, `1d` |

### 输出格式

| 格式 | 描述 |
|------|------|
| `pretty` | 美化打印的 JSON（默认） |
| `json` | 紧凑 JSON（适合管道传输） |
| `logs` | 仅日志消息，每行一条 |

## API 详情

**接口地址：** `https://developer.weiyun.baidu.com/eci-cloud-loghub/v1/openApi/queryLog/conditionQuery`

**认证方式：**
- HMAC-SHA256 签名，包含 HTTP 方法、路径、时间戳和随机数
- 请求头：`X-AK`, `X-Timestamp`, `X-Nonce`, `X-Signature`

**签名算法：**
```
string_to_sign = HTTP_METHOD + "\n" + PATH + "\n" + TIMESTAMP + "\n" + NONCE
signature = Base64(HMAC-SHA256(string_to_sign, SecretKey))
```

示例：
```
string_to_sign = "POST\n/eci-cloud-loghub/v1/openApi/queryLog/conditionQuery\n1766662552541\n1766662552541"
signature = Base64(HMAC-SHA256(string_to_sign, sk))
```

**请求体：**
```json
{
  "must": {
    "matchPhraseList": [
      {"weiyun_prod_name": "product-name"},
      {"weiyun_app_name": "app-name"}
    ],
    "participleMatchList": [
      {"message": "keyword"}
    ]
  },
  "startTime": "1766661652540",
  "endTime": "1766662552541"
}
```

## 资源文件

### scripts/weiyun_log_query.py
主 Python 脚本，用于查询日志。处理：
- 配置加载
- HMAC-SHA256 签名生成
- 查询构建
- API 通信
- 响应格式化

### config.json.example
配置文件模板示例。复制为 `config.json` 并填入凭证。

## 故障排除

**"Config file not found"**
- 创建 `config.json` 并填入 AK/SK 凭证

**"HTTP Error 401/403"**
- 检查 AK/SK 凭证是否正确
- 验证签名生成是否正常工作

**"No logs returned"**
- 检查时间范围是否正确
- 验证应用名/服务名是否匹配您的环境
- 尝试更宽泛的搜索词

**"requests library not installed"**
- 运行：`~/py312/bin/pip install requests`