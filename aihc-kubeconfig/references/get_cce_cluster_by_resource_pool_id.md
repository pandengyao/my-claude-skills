# get_cce_cluster_by_resource_pool_id

根据托管资源池 ID 获取 CCE 集群 ID 和 kubeconfig 配置。

## 参数说明

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| region | string | 是 | 地域代码 |
| resource_pool_id | string | 是 | 资源池 ID，格式: aihc-xxx |

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

返回 JSON 对象，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 状态码，200 表示成功 |
| message | string | 状态信息 |
| result | object | 结果对象 |
| result.cceClusterID | string | CCE 集群 ID |
| result.internalConfig | string | 开发机 B 区访问的 kubeconfig |
| result.vpcConfig | string | VPC 访问的 kubeconfig |
| result.publicConfig | string | 公网访问的 kubeconfig |
| result.region | string | 地域 |
| result.zoneName | string | 可用区 |

## 调用示例

### Python 调用

```python
from scripts import AihcClient

client = AihcClient()
result = client.get_cce_cluster_by_resource_pool_id(
    region="bj",
    resource_pool_id="aihc-cdac4orfnkiz"
)

if result.get("code") == 200:
    print(f"CCE集群ID: {result['result']['cceClusterID']}")
else:
    print(f"查询失败: {result.get('message')}")
```

### 返回示例

```json
{
  "code": 200,
  "message": "success",
  "result": {
    "cceClusterID": "cce-1i824a4y",
    "internalConfig": "apiVersion: v1\nclusters:\n- cluster:\n    ...",
    "vpcConfig": "apiVersion: v1\nclusters:\n- cluster:\n    ...",
    "publicConfig": "",
    "region": "bj",
    "zoneName": "cn-bj-i"
  }
}
```

## 应用场景

1. **获取 kubeconfig**：快速获取 CCE 集群的 kubeconfig 配置用于 kubectl 访问
2. **集群信息查询**：获取 CCE 集群 ID 用于后续管理操作
3. **问题排查**：查询资源池对应的集群信息

## 注意事项

- 返回的 kubeconfig 中可能包含换行符 `\n`，需要替换为实际换行
- 可使用 `client.save_kubeconfig()` 方法自动保存 kubeconfig 到文件
