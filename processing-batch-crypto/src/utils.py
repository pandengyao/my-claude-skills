"""
便捷函数
提供简化的加解密接口
"""

from typing import Optional
from .manager import CryptoManager


def encrypt(data: str, algorithm: str = "AES", key: Optional[str] = None, **kwargs) -> str:
    """
    便捷加密函数
    
    Args:
        data: 原始数据
        algorithm: 算法名称
        key: 密钥
        **kwargs: 其他参数
        
    Returns:
        加密后的数据
    """
    return CryptoManager.encrypt(data, algorithm, key, **kwargs)


def decrypt(cipher_text: str, algorithm: str = "AES", key: Optional[str] = None, **kwargs) -> str:
    """
    便捷解密函数
    
    Args:
        cipher_text: 加密数据
        algorithm: 算法名称
        key: 密钥
        **kwargs: 其他参数
        
    Returns:
        解密后的数据
    """
    return CryptoManager.decrypt(cipher_text, algorithm, key, **kwargs)


def hash_password(password: str, algorithm: str = "SHA256", salt: Optional[str] = None) -> str:
    """
    密码哈希函数
    
    Args:
        password: 密码
        algorithm: 哈希算法
        salt: 盐值
        
    Returns:
        哈希值
    """
    return CryptoManager.encrypt(password, algorithm, key=salt, salt=salt)
