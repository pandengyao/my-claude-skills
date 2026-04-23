"""
加解密工具包
使用策略模式和工厂模式实现的多算法加解密系统
"""

from .manager import CryptoManager
from .utils import encrypt, decrypt, hash_password
from .strategies import (
    CryptoStrategy,
    AESStrategy,
    DESStrategy,
    RSAStrategy,
    SHA256Strategy,
    MD5Strategy,
    SHA512Strategy,
    Base64Strategy,
)

__version__ = '1.0.0'
__all__ = [
    'CryptoManager',
    'encrypt',
    'decrypt',
    'hash_password',
    'CryptoStrategy',
    'AESStrategy',
    'DESStrategy',
    'RSAStrategy',
    'SHA256Strategy',
    'MD5Strategy',
    'SHA512Strategy',
    'Base64Strategy',
]
