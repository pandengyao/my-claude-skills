"""平台化需求自动管理 API 客户端包"""

from .platform_client import PlatformClient, PlatformConfig, create_client

__all__ = [
    'PlatformClient',
    'PlatformConfig',
    'create_client'
]
