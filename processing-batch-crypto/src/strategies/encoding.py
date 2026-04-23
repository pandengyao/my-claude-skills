"""
编码策略
包含 Base64 等编码算法
"""

import base64
from typing import Optional
from .base import CryptoStrategy


class Base64Strategy(CryptoStrategy):
    """Base64 编码策略（非加密，仅编码）"""
    
    @property
    def algorithm_name(self) -> str:
        return "BASE64"
    
    @property
    def algorithm_type(self) -> str:
        return "encoding"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """Base64 编码"""
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """Base64 解码"""
        return base64.b64decode(cipher_text.encode('utf-8')).decode('utf-8')
