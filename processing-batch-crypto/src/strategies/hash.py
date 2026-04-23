"""
哈希算法策略
包含 SHA256, MD5, SHA512 等哈希算法
"""

import hashlib
from typing import Optional
from .base import CryptoStrategy


class SHA256Strategy(CryptoStrategy):
    """SHA256 哈希策略"""
    
    @property
    def algorithm_name(self) -> str:
        return "SHA256"
    
    @property
    def algorithm_type(self) -> str:
        return "hash"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """SHA256 哈希（可加盐）"""
        salt = key or kwargs.get('salt') or ''
        salted_data = data + salt
        return hashlib.sha256(salted_data.encode('utf-8')).hexdigest()
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """SHA256是单向哈希，不支持解密"""
        raise ValueError("SHA256 是单向哈希算法，不支持解密操作！")


class MD5Strategy(CryptoStrategy):
    """MD5 哈希策略（不推荐用于安全场景）"""
    
    @property
    def algorithm_name(self) -> str:
        return "MD5"
    
    @property
    def algorithm_type(self) -> str:
        return "hash"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """MD5 哈希（可加盐）"""
        salt = key or kwargs.get('salt') or ''
        salted_data = data + salt
        return hashlib.md5(salted_data.encode('utf-8')).hexdigest()
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """MD5是单向哈希，不支持解密"""
        raise ValueError("MD5 是单向哈希算法，不支持解密操作！")


class SHA512Strategy(CryptoStrategy):
    """SHA512 哈希策略"""
    
    @property
    def algorithm_name(self) -> str:
        return "SHA512"
    
    @property
    def algorithm_type(self) -> str:
        return "hash"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """SHA512 哈希（可加盐）"""
        salt = key or kwargs.get('salt') or ''
        salted_data = data + salt
        return hashlib.sha512(salted_data.encode('utf-8')).hexdigest()
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """SHA512是单向哈希，不支持解密"""
        raise ValueError("SHA512 是单向哈希算法，不支持解密操作！")
