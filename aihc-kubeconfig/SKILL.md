---
name: aihc-kubeconfig
description: 百舸托管资源池kubeconfig获取工具。触发词:托管资源池/kubeconfig/CCE集群ID/资源池ID/队列ID/节点ID/aihc/aihcq/aihcn/百舸托管。
---

# 百舸托管资源池 Kubeconfig 获取工具

百度智能云百舸托管资源池查询技能，用于获取 CCE 集群 ID 和 kubeconfig 配置。

## 功能概览

本技能提供 3 个核心查询 API：

### 查询功能
- **get_cce_cluster_by_resource_pool_id** - 根据托管资源池 ID 获取 CCE 集群 ID 和 kubeconfig
- **get_cce_cluster_by_queue_id** - 根据托管队列 ID 获取 CCE 集群 ID 和 kubeconfig
- **get_node_info_by_instance_id** - 根据托管节点 ID 获取 BCC 等信息

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

### ID 格式说明
| 资源类型 | ID 前缀 | 示例 |
|----------|---------|------|
| 资源池 | aihc- | aihc-cdac4orfnkiz |
| 队列 | aihcq- | aihcq-fmrnpeybk8hy |
| 节点 | aihcn- | aihcn-xxxxx |

## 快速开始

### 基本使用

```python
# 导入客户端
from scripts import AihcClient

# 初始化客户端
client = AihcClient()

# 根据资源池ID获取CCE集群信息
result = client.get_cce_cluster_by_resource_pool_id(
    region="bj",
    resource_pool_id="aihc-cdac4orfnkiz"
)

# 根据队列ID获取CCE集群信息
result = client.get_cce_cluster_by_queue_id(
    region="bj",
    queue_id="aihcq-fmrnpeybk8hy"
)

# 根据节点ID获取BCC信息
result = client.get_node_info_by_instance_id(
    region="bj",
    instance_id="aihcn-xxxxx"
)
```

## 返回结果说明

查询成功后返回的数据包含：

| 字段 | 说明 |
|------|------|
| cceClusterID | CCE 集群 ID |
| internalConfig | 开发机 B 区访问的 kubeconfig |
| vpcConfig | VPC 访问的 kubeconfig |
| publicConfig | 公网访问的 kubeconfig |
| region | 地域 |
| zoneName | 可用区 |

## API 详细文档

每个 API 的详细文档已拆分到独立文件中：

- [get_cce_cluster_by_resource_pool_id.md](./references/get_cce_cluster_by_resource_pool_id.md)
- [get_cce_cluster_by_queue_id.md](./references/get_cce_cluster_by_queue_id.md)
- [get_node_info_by_instance_id.md](./references/get_node_info_by_instance_id.md)

## 常见错误码

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用场景

1. **获取 kubeconfig**：通过资源池 ID 或队列 ID 快速获取 CCE 集群的 kubeconfig 配置
2. **排查问题**：查询节点详细信息用于问题排查
3. **集群管理**：获取 CCE 集群 ID 后进行后续管理操作
