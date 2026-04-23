#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTTP 请求模块

封装带认证重试逻辑的 HTTP POST 请求。
"""

import requests
from typing import Dict, Any

from .auth import AuthManager


class HttpClient:
    """带自动 token 刷新的 HTTP 客户端"""

    def __init__(self, base_url: str, auth: AuthManager):
        """
        Args:
            base_url: API 基础 URL
            auth: 认证管理器实例
        """
        self.base_url = base_url
        self.auth = auth

    def request(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """
        发送HTTP请求，认证失败时自动刷新 token 重试

        Args:
            endpoint: API端点路径
            data: 请求数据

        Returns:
            API响应结果（dict 或 list）
        """
        max_retries = 2
        retry_count = 0

        while retry_count < max_retries:
            url = f"{self.base_url}{endpoint}"
            headers = self.auth.get_headers()

            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)

                # 先尝试解析JSON响应
                try:
                    result = response.json()
                except Exception:
                    # 如果无法解析JSON，按HTTP状态码处理
                    if response.status_code in [401, 403]:
                        print(f"\n⚠️  认证失败 (HTTP {response.status_code})")
                        if self.auth.try_refresh_token():
                            retry_count += 1
                            continue
                        else:
                            response.raise_for_status()
                    response.raise_for_status()
                    raise

                # 响应可能是 dict（错误或单个对象）或 list（正常业务数据列表）
                # 只有 dict 类型才可能包含错误码字段
                if isinstance(result, dict):
                    # 检查响应体中的code字段
                    response_code = result.get('code') or result.get('returnCode')
                    error_msg = result.get('error_msg') or result.get('msg') or result.get('returnMessage', '')

                    # ugate-token 过期：仅当错误信息明确包含 token 相关关键词时才判定
                    _token_keywords = (
                        'ugateToken', 'ugate_token',
                        'ugate-token', 'token invalid',
                        'token expired',
                    )
                    is_ugate_token_error = (
                        isinstance(error_msg, str) and
                        any(kw in error_msg for kw in _token_keywords)
                    )

                    if is_ugate_token_error:
                        print(f"\n⚠️  ugate-token 已过期或无效 (code: {response_code}, {error_msg})")
                        if self.auth.try_refresh_token():
                            retry_count += 1
                            continue
                        else:
                            return result

                    # 认证失败的错误码：401, 403, 60413
                    if response_code in [401, 403, 60413]:
                        print(f"\n⚠️  认证失败 (code: {response_code}, {error_msg})")
                        if self.auth.try_refresh_token():
                            retry_count += 1
                            continue
                        else:
                            return result

                # 检查HTTP状态码（dict 和 list 都需要检查）
                if response.status_code in [401, 403]:
                    print(f"\n⚠️  认证失败 (HTTP {response.status_code})")
                    if self.auth.try_refresh_token():
                        retry_count += 1
                        continue
                    else:
                        response.raise_for_status()

                # 如果状态码不是2xx，抛出异常
                response.raise_for_status()

                return result

            except requests.exceptions.RequestException as e:
                # 网络错误或其他异常
                if hasattr(e, 'response') and e.response is not None and e.response.status_code in [401, 403]:
                    print(f"\n⚠️  认证失败")
                    if self.auth.try_refresh_token():
                        retry_count += 1
                        continue

                print(f"❌ 请求失败: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"响应内容: {e.response.text}")
                raise

        # 所有重试都失败
        self.auth.print_auth_help()
        raise RuntimeError("认证失败，token 刷新后仍无法完成请求")
