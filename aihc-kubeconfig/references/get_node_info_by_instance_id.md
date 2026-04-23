# get_node_info_by_instance_id

根据托管节点 ID 获取 BCC 等信息。

## 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| region | string | 是 | 地域代码 |
| instance_id | string | 是 | 节点 ID，格式: aihcn-xxx |

### 支持的地域

| 地域代码 | 环境说明 |
|----------|----------|
| bj | 北京环境 |
| bd | 保定环境 |
| su | 苏州环境 |
| bjtest | 北京测试 |
| bjtest3 | 北京测试3 |
| bjtest4 | 北京测试4 |
| bdtest | 保定测试 |

## 返回值

返回 JSON 对象，包含节点详细信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，200 表示成功 |
| message | string | 状态信息 |
| result | object | 结果对象，包含节点详细信息 |

## 调用示例

### Python 调用

```python
from scripts import AihcClient

client = AihcClient()
result = client.get_node_info_by_instance_id(
    region="bj",
    instance_id="aihcn-xxxxx"
)

if result.get("code") == 200:
    print(f"节点信息: {result['result']}")
else:
    print(f"查询失败: {result.get('message')}")
```

## 应用场景

1. **节点信息查询**：获取节点的 BCC 实例信息
2. **问题排查**：查询节点详细信息用于问题诊断
3. **资源管理**：了解节点的配置和状态

## 注意事项

- 节点 ID 格式为 `aihcn-xxx`
- 确保使用正确的地域代码
