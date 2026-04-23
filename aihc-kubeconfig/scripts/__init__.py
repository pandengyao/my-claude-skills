#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百舸托管资源池 API 客户端包初始化文件
导出 AihcClient 类供外部使用
"""

from .aihc_client import AihcClient, query_resource_pool, query_queue, query_node

__all__ = ["AihcClient", "query_resource_pool", "query_queue", "query_node"]
