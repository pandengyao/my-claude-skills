"""
非对称加密策略
包含 RSA 算法
"""

import base64
from typing import Optional
from .base import CryptoStrategy


class RSAStrategy(CryptoStrategy):
    """RSA 非对称加密策略"""
    
    def __init__(self):
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa, padding
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.backends import default_backend
            self._cryptography_available = True
        except ImportError:
            self._cryptography_available = False
    
    @property
    def algorithm_name(self) -> str:
        return "RSA"
    
    @property
    def algorithm_type(self) -> str:
        return "asymmetric"
    
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """RSA 公钥加密"""
        if not self._cryptography_available:
            raise ImportError("需要安装 cryptography 库: pip install cryptography")
        
        from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.backends import default_backend
        
        # 获取公钥
        public_key_path = kwargs.get('public_key_path')
        if public_key_path:
            with open(public_key_path, 'rb') as f:
                public_key_data = f.read()
        elif key:
            public_key_data = key.encode('utf-8') if isinstance(key, str) else key
        else:
            raise ValueError("必须提供公钥（key参数或public_key_path参数）")
        
        # 加载公钥
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        public_key = load_pem_public_key(public_key_data, backend=default_backend())
        
        # 加密
        encrypted = public_key.encrypt(
            data.encode('utf-8'),
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """RSA 私钥解密"""
        if not self._cryptography_available:
            raise ImportError("需要安装 cryptography 库: pip install cryptography")
        
        from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.backends import default_backend
        
        # 获取私钥
        private_key_path = kwargs.get('private_key_path')
        if private_key_path:
            with open(private_key_path, 'rb') as f:
                private_key_data = f.read()
        elif key:
            private_key_data = key.encode('utf-8') if isinstance(key, str) else key
        else:
            raise ValueError("必须提供私钥（key参数或private_key_path参数）")
        
        # 加载私钥
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        private_key = load_pem_private_key(
            private_key_data,
            password=None,
            backend=default_backend()
        )
        
        # Base64解码
        encrypted = base64.b64decode(cipher_text.encode('utf-8'))
        
        # 解密
        decrypted = private_key.decrypt(
            encrypted,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return decrypted.decode('utf-8')
