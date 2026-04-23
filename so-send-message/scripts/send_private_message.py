#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送单聊消息脚本
支持向指定用户发送单聊消息
"""

import sys
import json
import time
import requests
import argparse
import logging
import hashlib
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# 内置默认凭证
DEFAULT_APP_KEY = os.environ.get('INFOFLOW_APP_KEY', '')
DEFAULT_APP_SECRET = os.environ.get('INFOFLOW_APP_SECRET', '')

class PrivateMessageSender:
    """单聊消息发送器"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        """
        初始化发送器
        
        Args:
            app_key: 应用Key（可选，已内置默认值）
            app_secret: 应用Secret（可选，已内置默认值）
        """
        self.app_key = app_key or DEFAULT_APP_KEY
        self.app_secret = app_secret or DEFAULT_APP_SECRET
        self.app_access_token = None
        self.token_expire_time = 0
        
    def get_app_access_token(self) -> str:
        """
        获取应用访问令牌
        
        Returns:
            访问令牌字符串
        """
        # 如果token未过期，直接返回
        current_time = int(time.time())
        if self.app_access_token and current_time < self.token_expire_time:
            return self.app_access_token
        
        url = "http://apiin.im.baidu.com/api/v1/auth/app_access_token"
        md5_secret = hashlib.md5(self.app_secret.encode('utf-8')).hexdigest().lower()
        
        payload = {
            "app_key": self.app_key,
            "app_secret": md5_secret
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 'ok':
                data = result.get('data', {})
                self.app_access_token = data.get('app_access_token')
                self.token_expire_time = current_time + 7100
                logger.info(f"✅ 获取token成功")
                return self.app_access_token
            else:
                logger.error(f"获取token失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取token异常: {str(e)}")
            return None
    
    def get_user_id_by_username(self, username: str) -> Optional[str]:
        """
        通过用户名查询用户ID
        
        Args:
            username: 用户名（如 huangzhen09）
            
        Returns:
            用户ID，如果查询失败返回None
        """
        try:
            token = self.get_app_access_token()
            if not token:
                return None
            
            # 查询用户信息接口
            url = "http://apiin.im.baidu.com/api/v1/user/get"
            
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8'
            }
            
            payload = {
                "username": username
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if result.get('code') == 'ok':
                user_id = result.get('data', {}).get('user_id')
                logger.info(f"查询到用户 {username} 的ID: {user_id}")
                return user_id
            else:
                logger.error(f"查询用户ID失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"查询用户ID异常: {str(e)}")
            return None
    
    def send_text_message(self, user_id: str, content: str, use_username: bool = False) -> Dict[str, Any]:
        """
        发送文本消息给指定用户
        
        Args:
            user_id: 用户ID或用户名
            content: 文本消息内容
            use_username: 是否使用用户名模式
            
        Returns:
            发送结果
        """
        try:
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            # 单聊消息发送接口
            url = "http://apiin.im.baidu.com/api/v1/robot/msg/p2pmsgsend"
            
            # 如果使用用户名，则设置totype为USERNAME
            totype = "USERNAME" if use_username else "USER"
            
            payload = json.dumps({
                "message": {
                    "header": {
                        "toid": str(user_id),  # 用户ID或用户名
                        "totype": totype,  # 接收方类型
                        "msgtype": "TEXT",
                        "clientmsgid": int(time.time() * 1000),
                        "role": "robot"
                    },
                    "body": [{"type": "TEXT", "content": content}]
                }
            })
            
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            logger.info(f"发送单聊消息给用户 {user_id}")
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": str(e)}
    
    def send_md_message(self, user_id: str, content: str, use_username: bool = False) -> Dict[str, Any]:
        """
        发送Markdown消息给指定用户
        
        Args:
            user_id: 用户ID或用户名
            content: MD格式消息内容
            use_username: 是否使用用户名模式
            
        Returns:
            发送结果
        """
        try:
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            url = "http://apiin.im.baidu.com/api/v1/robot/msg/p2pmsgsend"
            
            # 如果使用用户名，则设置totype为USERNAME
            totype = "USERNAME" if use_username else "USER"
            
            payload = json.dumps({
                "message": {
                    "header": {
                        "toid": str(user_id),
                        "totype": totype,
                        "msgtype": "MD",
                        "clientmsgid": int(time.time() * 1000),
                        "role": "robot"
                    },
                    "body": [{"type": "MD", "content": content}]
                }
            })
            
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            logger.info(f"发送MD消息给用户 {user_id}")
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(description='发送单聊消息')
    parser.add_argument('--user-id', help='用户ID（数字）')
    parser.add_argument('--username', help='用户名（如 huangzhen09）')
    parser.add_argument('--content', required=True, help='消息内容')
    parser.add_argument('--type', choices=['text', 'md'], default='text', help='消息类型')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if not args.user_id and not args.username:
        print("错误: 需要指定 --user-id 或 --username")
        sys.exit(1)
    
    sender = PrivateMessageSender()
    
    # 确定发送模式
    use_username_mode = False
    user_id = args.user_id
    
    if args.username and not args.user_id:
        # 尝试查询用户ID
        user_id = sender.get_user_id_by_username(args.username)
        if not user_id:
            # 查询失败，尝试直接使用用户名发送
            logger.info("用户ID查询失败，尝试直接使用用户名发送")
            use_username_mode = True
            user_id = args.username
    
    # 发送消息
    if args.type == 'md':
        content = args.content.replace('\\n', '\n')
        result = sender.send_md_message(user_id, content, use_username=use_username_mode)
    else:
        result = sender.send_text_message(user_id, args.content, use_username=use_username_mode)
    
    # 输出结果
    if result.get('code') == 'ok':
        print(f"✅ 消息发送成功")
        print(f"   接收用户: {args.username or user_id}")
        print(f"   消息ID: {result.get('data', {}).get('messageid', 'N/A')}")
    else:
        print(f"❌ 消息发送失败")
        print(f"   错误码: {result.get('code', 'N/A')}")
        print(f"   错误信息: {result.get('message', 'N/A')}")
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
