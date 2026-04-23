"""
加密策略抽象基类
定义所有加密算法的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional


class CryptoStrategy(ABC):
    """加解密策略抽象基类"""
    
    @abstractmethod
    def encrypt(self, data: str, key: Optional[str] = None, **kwargs) -> str:
        """
        加密数据
        
        Args:
            data: 原始数据
            key: 密钥（可选）
            **kwargs: 其他参数
            
        Returns:
            加密后的数据
        """
        pass
    
    @abstractmethod
    def decrypt(self, cipher_text: str, key: Optional[str] = None, **kwargs) -> str:
        """
        解密数据
        
        Args:
            cipher_text: 加密数据
            key: 密钥（可选）
            **kwargs: 其他参数
            
        Returns:
            解密后的原始数据
        """
        pass
    
    @property
    @abstractmethod
    def algorithm_name(self) -> str:
        """算法名称"""
        pass
    
    @property
    def algorithm_type(self) -> str:
        """算法类型：symmetric/asymmetric/hash/encoding"""
        return "unknown"
