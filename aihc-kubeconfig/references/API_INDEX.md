# API 索引

百舸托管资源池 kubeconfig 获取工具 API 索引。

## 快速查询

| 方法 | 说明 | 文档 |
|------|------|------|
| `get_cce_cluster_by_resource_pool_id` | 根据资源池 ID 获取 CCE 集群信息 | [详情](./get_cce_cluster_by_resource_pool_id.md) |
| `get_cce_cluster_by_queue_id` | 根据队列 ID 获取 CCE 集群信息 | [详情](./get_cce_cluster_by_queue_id.md) |
| `get_node_info_by_instance_id` | 根据节点 ID 获取 BCC 信息 | [详情](./get_node_info_by_instance_id.md) |

## 使用示例

### 1. 根据资源池 ID 查询

```python
from scripts import AihcClient

client = AihcClient()
result = client.get_cce_cluster_by_resource_pool_id("bj", "aihc-cdac4orfnkiz")
print(result["result"]["cceClusterID"])  # 输出: cce-1i824a4y
```

### 2. 根据队列 ID 查询

```python
from scripts import AihcClient

client = AihcClient()
result = client.get_cce_cluster_by_queue_id("bj", "aihcq-fmrnpeybk8hy")
print(result["result"]["cceClusterID"])
```

### 3. 保存 kubeconfig 到文件

```python
from scripts import AihcClient

client = AihcClient()
result = client.get_cce_cluster_by_resource_pool_id("bj", "aihc-cdac4orfnkiz")

# 保存 internal 类型的 kubeconfig
client.save_kubeconfig(result, config_type="internal")
# 输出: kubeconfig 已保存到: ~/.kube/config-cce-1i824a4y
```

### 4. 使用快捷函数

```python
from scripts import query_resource_pool, query_queue, query_node

# 查询资源池
result = query_resource_pool("bj", "aihc-cdac4orfnkiz")

# 查询队列
result = query_queue("bj", "aihcq-fmrnpeybk8hy")

# 查询节点
result = query_node("bj", "aihcn-xxxxx")
```

## ID 格式速查

| 资源类型 | ID 前缀 | 示例 |
|----------|---------|------|
| 资源池 | aihc- | aihc-cdac4orfnkiz |
| 队列 | aihcq- | aihcq-fmrnpeybk8hy |
| 节点 | aihcn- | aihcn-xxxxx |

## 地域代码速查

| 代码 | 环境 |
|------|------|
| bj | 北京 |
| bd | 保定 |
| su | 苏州 |
| bjtest | 北京测试 |
| bjtest3 | 北京测试3 |
| bjtest4 | 北京测试4 |
| bdtest | 保定测试 |
