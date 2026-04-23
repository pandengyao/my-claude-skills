#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百舸托管资源池 API 客户端
用于查询 CCE 集群 ID 和 kubeconfig 配置

作者: wangluhui
版本: v1.0.0
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional, Any


# 地域 URL 映射
REGION_URLS = {
    "bj": "http://10.180.114.235:8688",
    "bd": "http://10.70.1.21:8688",
    "su": "http://10.191.105.211:8688",
    "bjtest": "http://10.144.208.16:8688",
    "bjtest3": "http://10.209.54.223:8688",
    "bjtest4": "http://10.209.54.224:8688",
    "bdtest": "http://10.160.52.163:8688",
}

# API 路径映射
API_PATHS = {
    "get_cce_cluster_by_resource_pool_id": {
        "path": "resourcePool",
        "param": "resourcePoolID",
        "description": "根据托管资源池ID获取CCE集群ID",
    },
    "get_cce_cluster_by_queue_id": {
        "path": "queue",
        "param": "queueID",
        "description": "根据托管队列ID获取CCE集群ID",
    },
    "get_node_info_by_instance_id": {
        "path": "bccInfo",
        "param": "instanceID",
        "description": "根据托管节点ID获取BCC等信息",
    },
}


class AihcClient:
    """百舸托管资源池查询客户端"""

    def __init__(self, timeout: int = 30):
        """
        初始化客户端

        Args:
            timeout: 请求超时时间（秒），默认 30 秒
        """
        self.timeout = timeout

    def _get_region_url(self, region: str) -> Optional[str]:
        """获取地域对应的 URL"""
        return REGION_URLS.get(region)

    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            url: 请求 URL

        Returns:
            响应 JSON 数据
        """
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AihcClient/1.0"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_json = json.loads(error_body)
                return {
                    "code": e.code,
                    "message": error_json.get("message", str(e)),
                    "error": True,
                }
            except json.JSONDecodeError:
                return {"code": e.code, "message": str(e), "error": True}
        except urllib.error.URLError as e:
            return {"code": 0, "message": f"网络错误: {str(e)}", "error": True}
        except Exception as e:
            return {"code": 0, "message": f"未知错误: {str(e)}", "error": True}

    def _query(
        self, operation: str, region: str, resource_id: str
    ) -> Dict[str, Any]:
        """
        通用查询方法

        Args:
            operation: 操作类型
            region: 地域代码
            resource_id: 资源 ID

        Returns:
            查询结果
        """
        # 验证地域
        base_url = self._get_region_url(region)
        if not base_url:
            return {
                "code": 400,
                "message": f"不支持的地域: {region}。支持的地域: {', '.join(REGION_URLS.keys())}",
                "error": True,
            }

        # 获取 API 配置
        api_config = API_PATHS.get(operation)
        if not api_config:
            return {
                "code": 400,
                "message": f"不支持的操作类型: {operation}",
                "error": True,
            }

        # 构建完整 URL
        url = f"{base_url}/admin/{api_config['path']}?{api_config['param']}={resource_id}"

        # 发送请求
        result = self._make_request(url)
        result["query_info"] = {
            "operation": operation,
            "operation_desc": api_config["description"],
            "region": region,
            "resource_id": resource_id,
            "url": url,
        }

        return result

    def get_cce_cluster_by_resource_pool_id(
        self, region: str, resource_pool_id: str
    ) -> Dict[str, Any]:
        """
        根据托管资源池 ID 获取 CCE 集群 ID 和 kubeconfig

        Args:
            region: 地域代码 (bj, bd, su, bjtest, bjtest3, bjtest4, bdtest)
            resource_pool_id: 资源池 ID，格式: aihc-xxx

        Returns:
            查询结果，包含 cceClusterID, internalConfig, vpcConfig, publicConfig 等字段

        Example:
            >>> client = AihcClient()
            >>> result = client.get_cce_cluster_by_resource_pool_id("bj", "aihc-cdac4orfnkiz")
            >>> print(result["result"]["cceClusterID"])
            'cce-1i824a4y'
        """
        return self._query(
            "get_cce_cluster_by_resource_pool_id", region, resource_pool_id
        )

    def get_cce_cluster_by_queue_id(
        self, region: str, queue_id: str
    ) -> Dict[str, Any]:
        """
        根据托管队列 ID 获取 CCE 集群 ID 和 kubeconfig

        Args:
            region: 地域代码 (bj, bd, su, bjtest, bjtest3, bjtest4, bdtest)
            queue_id: 队列 ID，格式: aihcq-xxx

        Returns:
            查询结果，包含 cceClusterID, internalConfig, vpcConfig, publicConfig 等字段

        Example:
            >>> client = AihcClient()
            >>> result = client.get_cce_cluster_by_queue_id("bj", "aihcq-fmrnpeybk8hy")
            >>> print(result["result"]["cceClusterID"])
            'cce-xxx'
        """
        return self._query("get_cce_cluster_by_queue_id", region, queue_id)

    def get_node_info_by_instance_id(
        self, region: str, instance_id: str
    ) -> Dict[str, Any]:
        """
        根据托管节点 ID 获取 BCC 等信息

        Args:
            region: 地域代码 (bj, bd, su, bjtest, bjtest3, bjtest4, bdtest)
            instance_id: 节点 ID，格式: aihcn-xxx

        Returns:
            查询结果，包含节点详细信息

        Example:
            >>> client = AihcClient()
            >>> result = client.get_node_info_by_instance_id("bj", "aihcn-xxxxx")
        """
        return self._query("get_node_info_by_instance_id", region, instance_id)

    def save_kubeconfig(
        self,
        result: Dict[str, Any],
        config_type: str = "internal",
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        从查询结果中提取并保存 kubeconfig

        Args:
            result: 查询结果
            config_type: 配置类型 (internal, vpc, public)
            output_path: 输出文件路径，默认为 ~/.kube/config-<cceClusterID>

        Returns:
            保存的文件路径，失败返回 None
        """
        if result.get("code") != 200:
            print(f"查询失败: {result.get('message')}")
            return None

        result_data = result.get("result", {})
        cce_cluster_id = result_data.get("cceClusterID")
        config_key = f"{config_type}Config"
        kubeconfig = result_data.get(config_key)

        if not kubeconfig:
            print(f"没有找到 {config_type} 类型的 kubeconfig")
            return None

        # 处理换行符
        kubeconfig = kubeconfig.replace("\\n", "\n")

        # 确定输出路径
        import os

        if not output_path:
            output_path = os.path.expanduser(f"~/.kube/config-{cce_cluster_id}")

        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 写入文件
        with open(output_path, "w") as f:
            f.write(kubeconfig)

        print(f"kubeconfig 已保存到: {output_path}")
        return output_path


# 便捷函数
def query_resource_pool(region: str, resource_pool_id: str) -> Dict[str, Any]:
    """快捷查询资源池"""
    client = AihcClient()
    return client.get_cce_cluster_by_resource_pool_id(region, resource_pool_id)


def query_queue(region: str, queue_id: str) -> Dict[str, Any]:
    """快捷查询队列"""
    client = AihcClient()
    return client.get_cce_cluster_by_queue_id(region, queue_id)


def query_node(region: str, instance_id: str) -> Dict[str, Any]:
    """快捷查询节点"""
    client = AihcClient()
    return client.get_node_info_by_instance_id(region, instance_id)
