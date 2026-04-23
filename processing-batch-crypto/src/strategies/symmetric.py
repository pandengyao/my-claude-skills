"""
对称加密策略
包含 AES 和 DES 算法
"""

import os
import base64
import hashlib
from typing import Optional
from .base import CryptoStrategy


class AESStrategy(CryptoStrategy):
    """AES-256-CBC 对称加密策略"""
    
    def __init__(self):
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import padding
            self._cryptography_available = True
        except ImportError:
            self._cryptography_available = False
    
    @property
    def algorithm_name(self) -> str:
        return "AES"
    
    @property
    def algorithm_type(self) -> str:
        return "symmetric"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """AES-256-CBC 加密"""
        if not self._cryptography_available:
            raise ImportError("需要安装 cryptography 库: pip install cryptography")
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding as crypto_padding
        
        # 处理密钥（强制要求配置）
        if key is None:
            key = os.getenv('CRYPTO_KEY')
        if not key:
            raise ValueError("未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY")
        key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
        
        # 处理IV（强制要求配置）
        iv = kwargs.get('iv')
        if iv is None:
            iv = os.getenv('CRYPTO_IV')
        if not iv:
            raise ValueError("未配置初始化向量！请通过参数传入 iv 或设置环境变量 CRYPTO_IV")
        iv_bytes = hashlib.md5(iv.encode('utf-8')).digest()
        
        # PKCS7填充
        padder = crypto_padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
        
        # 加密
        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CBC(iv_bytes),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """AES-256-CBC 解密"""
        if not self._cryptography_available:
            raise ImportError("需要安装 cryptography 库: pip install cryptography")
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import padding as crypto_padding
        
        # 处理密钥（强制要求配置）
        if key is None:
            key = os.getenv('CRYPTO_KEY')
        if not key:
            raise ValueError("未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY")
        key_bytes = hashlib.sha256(key.encode('utf-8')).digest()
        
        # 处理IV（强制要求配置）
        iv = kwargs.get('iv')
        if iv is None:
            iv = os.getenv('CRYPTO_IV')
        if not iv:
            raise ValueError("未配置初始化向量！请通过参数传入 iv 或设置环境变量 CRYPTO_IV")
        iv_bytes = hashlib.md5(iv.encode('utf-8')).digest()
        
        # Base64解码
        encrypted = base64.b64decode(cipher_text.encode('utf-8'))
        
        # 解密
        cipher = Cipher(
            algorithms.AES(key_bytes),
            modes.CBC(iv_bytes),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(encrypted) + decryptor.finalize()
        
        # 去除填充
        unpadder = crypto_padding.PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data.decode('utf-8')


class DESStrategy(CryptoStrategy):
    """DES 对称加密策略（仅作示例，不推荐生产使用）"""
    
    @property
    def algorithm_name(self) -> str:
        return "DES"
    
    @property
    def algorithm_type(self) -> str:
        return "symmetric"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """DES 加密"""
        try:
            from Crypto.Cipher import DES
            from Crypto.Util.Padding import pad
        except ImportError:
            raise ImportError("需要安装 pycryptodome: pip install pycryptodome")
        
        if key is None:
            key = os.getenv('CRYPTO_KEY')
        if not key:
            raise ValueError("未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY")
        key_bytes = hashlib.md5(key.encode('utf-8')).digest()[:8]
        
        cipher = DES.new(key_bytes, DES.MODE_ECB)
        padded_data = pad(data.encode('utf-8'), DES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """DES 解密"""
        try:
            from Crypto.Cipher import DES
            from Crypto.Util.Padding import unpad
        except ImportError:
            raise ImportError("需要安装 pycryptodome: pip install pycryptodome")
        
        if key is None:
            key = os.getenv('CRYPTO_KEY')
        if not key:
            raise ValueError("未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY")
        key_bytes = hashlib.md5(key.encode('utf-8')).digest()[:8]
        
        encrypted = base64.b64decode(cipher_text.encode('utf-8'))
        cipher = DES.new(key_bytes, DES.MODE_ECB)
        padded_data = cipher.decrypt(encrypted)
        data = unpad(padded_data, DES.block_size)
        
        return data.decode('utf-8')
