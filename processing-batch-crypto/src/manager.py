"""
加解密管理器（工厂模式）
统一管理所有加解密策略
"""

from typing import Dict, Any, Optional
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


class CryptoManager:
    """加解密管理器（工厂模式）"""
    
    # 策略注册表
    _strategies: Dict[str, CryptoStrategy] = {
        "AES": AESStrategy(),
        "DES": DESStrategy(),
        "RSA": RSAStrategy(),
        "SHA256": SHA256Strategy(),
        "MD5": MD5Strategy(),
        "SHA512": SHA512Strategy(),
        "BASE64": Base64Strategy(),
    }
    
    # 默认算法
    _default_algorithm = "AES"
    
    @classmethod
    def register_strategy(cls, name: str, strategy: CryptoStrategy):
        """注册新的加密策略"""
        cls._strategies[name.upper()] = strategy
    
    @classmethod
    def get_strategy(cls, algorithm: str) -> CryptoStrategy:
        """获取加密策略"""
        strategy = cls._strategies.get(algorithm.upper())
        if not strategy:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(
                f"不支持的加密算法: {algorithm}\n"
                f"可用算法: {available}"
            )
        return strategy
    
    @classmethod
    def set_default_algorithm(cls, algorithm: str):
        """设置默认算法"""
        if algorithm.upper() not in cls._strategies:
            raise ValueError(f"算法不存在: {algorithm}")
        cls._default_algorithm = algorithm.upper()
    
    @classmethod
    def encrypt(cls, data: str, algorithm: Optional[str] = None, 
                key: Optional[str] = None, **kwargs) -> str:
        """加密数据"""
        if algorithm is None:
            algorithm = cls._default_algorithm
        
        strategy = cls.get_strategy(algorithm)
        return strategy.encrypt(data, key, **kwargs)
    
    @classmethod
    def decrypt(cls, cipher_text: str, algorithm: Optional[str] = None,
                key: Optional[str] = None, **kwargs) -> str:
        """解密数据"""
        if algorithm is None:
            algorithm = cls._default_algorithm
        
        strategy = cls.get_strategy(algorithm)
        return strategy.decrypt(cipher_text, key, **kwargs)
    
    @classmethod
    def list_algorithms(cls) -> Dict[str, str]:
        """列出所有可用算法"""
        return {
            name: strategy.algorithm_type 
            for name, strategy in cls._strategies.items()
        }
    
    @classmethod
    def get_algorithm_info(cls, algorithm: str) -> Dict[str, Any]:
        """获取算法信息"""
        strategy = cls.get_strategy(algorithm)
        return {
            'name': strategy.algorithm_name,
            'type': strategy.algorithm_type,
            'class': strategy.__class__.__name__
        }
