#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发送群消息脚本
支持向指定群组发送MD格式消息
"""

import sys
import json
import time
import requests
import argparse
import logging
import re
import base64
import os
from typing import Dict, Any, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# 内置默认凭证（优先读取环境变量，否则使用内置默认值）
DEFAULT_APP_KEY = os.environ.get('INFOFLOW_APP_KEY', '')
DEFAULT_APP_SECRET = os.environ.get('INFOFLOW_APP_SECRET', '')

def format_markdown_for_hi(content: str) -> str:
    """
    格式化Markdown内容以符合如流规范
    
    Args:
        content: 原始Markdown内容
        
    Returns:
        格式化后的Markdown内容
    """
    if not content:
        return content
    
    # 1. 处理标题格式：确保#号和文本之间有一个空格
    def format_header(match):
        level = match.group(1)
        text = match.group(2)
        return f"{level} {text}"
    
    # 修复标题格式
    content = re.sub(r'^(#{1,6})(\S)', format_header, content, flags=re.MULTILINE)
    
    # 2. 处理不规范的粗体语法（四个*或_）
    # 注意：正确处理转义，避免与分组引用冲突
    content = re.sub(r'\*\*\*\*([^*]+)\*\*\*\*', r'**\1**', content)  # ****text**** -> **text**
    content = re.sub(r'____([^_]+)____', r'__\1__', content)  # ____text____ -> __text__
    
    # 3. 处理不规范的斜体语法（两个*或_）
    # 先处理不规范的粗体，再处理规范的
    # 注意：这里的替换逻辑需要更智能，避免误伤
    
    # 4. 处理表格格式：确保表格行有正确格式
    lines = content.split('\n')
    in_table = False
    table_lines = []
    
    # 4. 处理表格格式：确保表格行有正确格式
    lines = content.split('\n')
    in_table = False
    table_lines = []
    
    for i, line in enumerate(lines):
        # 检测表格开始
        if '|' in line and (i == 0 or '|' in lines[i-1] or '|' in lines[min(i+1, len(lines)-1)]):
            if not in_table:
                in_table = True
                table_lines = [line]
            else:
                table_lines.append(line)
        else:
            if in_table:
                # 处理表格数据
                formatted_table = format_table(table_lines)
                lines[i-len(table_lines):i] = formatted_table
                in_table = False
                table_lines = []
    
    if in_table:
        formatted_table = format_table(table_lines)
        lines[-len(table_lines):] = formatted_table
    
    content = '\n'.join(lines)
    
    # 5. 处理分割线格式：确保前后有空行
    content = re.sub(r'(\S)\s*\n\s*[\-\*]{3,}\s*\n(\S)', r'\1\n\n---\n\n\2', content)
    content = re.sub(r'(\S)\s*\n\s*[\-\*]{3,}\s*\n(\S)', r'\1\n\n---\n\n\2', content)
    
    # 6. 移除不支持的HTML标签（如<br>, <br/>）
    content = re.sub(r'<br\s*/?>', '\n', content)
    
    # 7. 处理列表格式：确保列表项之间有明确分隔
    content = re.sub(r'(\n\s*[-*+\d\.]\s+.*\n)(\S)', r'\1\n\2', content)
    
    # 8. 确保引用格式正确
    content = re.sub(r'^&gt;\s*', '> ', content, flags=re.MULTILINE)
    
    # 9. 处理代码块格式
    content = re.sub(r'```(\w+)?', r'```\1', content)
    
    return content


def format_table(table_lines: list) -> list:
    """格式化表格内容"""
    if len(table_lines) < 2:
        return table_lines
    
    # 检查是否有分隔行
    has_separator = any(re.search(r'\|\s*[-:\s]+\s*\|', line) for line in table_lines)
    
    if not has_separator and len(table_lines) >= 1:
        # 添加分隔行
        first_line = table_lines[0]
        columns = first_line.count('|') - 1
        separator = '|' + ' --- |' * columns
        table_lines.insert(1, separator)
    
    # 确保每行单元格对齐
    formatted_lines = []
    for line in table_lines:
        # 清理多余的空白
        line = re.sub(r'\|\s+', '| ', line)
        line = re.sub(r'\s+\|', ' |', line)
        line = line.strip()
        if not line.startswith('|'):
            line = '|' + line
        if not line.endswith('|'):
            line = line + '|'
        formatted_lines.append(line)
    
    return formatted_lines


class GroupMessageSender:
    """群消息发送器"""
    
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
        import hashlib
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
                # token通常有效期为7200秒，这里设置为7100秒以确保安全
                self.token_expire_time = current_time + 7100
                logger.info(f"✅ 获取token成功，有效期至: {self.token_expire_time}")
                return self.app_access_token
            else:
                logger.error(f"获取token失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"获取token异常: {str(e)}")
            return None
    
    def send_md_message(self, group_id: str, content: str) -> Dict[str, Any]:
        """
        发送MD格式消息到群组
        
        Args:
            group_id: 群组ID
            content: MD格式消息内容
            
        Returns:
            发送结果
        """
        try:
            # 获取应用访问令牌
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            # 构造API请求URL和消息体
            url = "http://apiin.im.baidu.com/api/v1/robot/msg/groupmsgsend"
            payload = json.dumps({
                "message": {
                    "header": {
                        "toid": int(group_id),  # 目标群组ID，必须是整数类型
                        "totype": "GROUP",  # 接收方类型为群组
                        "msgtype": "MD",  # 消息类型为MD
                        "clientmsgid": int(time.time() * 1000),  # 使用时间戳生成唯一消息ID
                        "role": "robot"  # 发送者角色为机器人
                    },
                    "body": [{"type": "MD", "content": content}]  # 消息内容
                }
            })
            
            # 设置请求头
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            # 发送POST请求
            logger.info(f"发送MD消息到群组 {group_id}，内容长度: {len(content)}")
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"发送消息超时")
            return {"code": "error", "message": "请求超时"}
        except requests.exceptions.RequestException as e:
            logger.error(f"发送消息请求异常: {str(e)}")
            return {"code": "error", "message": f"请求异常: {str(e)}"}
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": f"异常: {str(e)}"}
    
    def send_text_message(self, group_id: str, content: str) -> Dict[str, Any]:
        """
        发送文本消息到群组
        
        Args:
            group_id: 群组ID
            content: 文本消息内容
            
        Returns:
            发送结果
        """
        try:
            # 获取应用访问令牌
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            # 构造API请求URL和消息体
            url = "http://apiin.im.baidu.com/api/v1/robot/msg/groupmsgsend"
            payload = json.dumps({
                "message": {
                    "header": {
                        "toid": int(group_id),  # 目标群组ID，必须是整数类型
                        "totype": "GROUP",  # 接收方类型为群组
                        "msgtype": "TEXT",  # 消息类型为文本
                        "clientmsgid": int(time.time() * 1000),  # 使用时间戳生成唯一消息ID
                        "role": "robot"  # 发送者角色为机器人
                    },
                    "body": [{"type": "TEXT", "content": content}]  # 消息内容
                }
            })
            
            # 设置请求头
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            # 发送POST请求
            logger.info(f"发送文本消息到群组 {group_id}，内容长度: {len(content)}")
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": str(e)}
    
    def send_image_message(self, group_id: str, image_url: str) -> Dict[str, Any]:
        """
        发送图片消息到群组
        
        Args:
            group_id: 群组ID
            image_url: 图片URL
            
        Returns:
            发送结果
        """
        try:
            # 获取应用访问令牌
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            # 构造API请求URL和消息体
            url = "http://apiin.im.baidu.com/api/v1/robot/msg/groupmsgsend"
            payload = json.dumps({
                "message": {
                    "header": {
                        "toid": int(group_id),  # 目标群组ID，必须是整数类型
                        "totype": "GROUP",  # 接收方类型为群组
                        "msgtype": "IMAGE",  # 消息类型为图片
                        "clientmsgid": int(time.time() * 1000),  # 使用时间戳生成唯一消息ID
                        "role": "robot"  # 发送者角色为机器人
                    },
                    "body": [{"type": "IMAGE", "content": image_url}]  # 图片URL
                }
            })
            
            # 设置请求头
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            # 发送POST请求
            logger.info(f"发送图片消息到群组 {group_id}，图片URL: {image_url}")
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送图片消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": str(e)}

    def send_app_message(self, to_users: str, msg_type: str, content: str = None, image_url: str = None) -> Dict[str, Any]:
        """
        使用 /app/message/send 接口发送单人/多人消息
        
        Args:
            to_users: 目标用户，多个用户用|分隔，如 "user1|user2"
            msg_type: 消息类型 'text', 'markdown', 'image'
            content: 文本或Markdown内容
            image_url: 图片链接
            
        Returns:
            发送结果
        """
        try:
            # 获取应用访问令牌
            token = self.get_app_access_token()
            if not token:
                return {"code": "error", "message": "获取token失败"}
            
            # 构造API请求URL
            url = "http://apiin.im.baidu.com/api/v1/app/message/send"
            
            # 构造基础payload
            payload = {
                "touser": to_users,
                "msgtype": msg_type
            }
            
            if msg_type == 'text':
                payload["text"] = {"content": content}
            elif msg_type == 'markdown':
                # 注意：虽然参数名为markdown，但如流文档中通常使用 'markdown': {'content': ...} 或 'md': {'content': ...}
                # 参考常见如流API，markdown类型键名通常为 markdown
                payload["markdown"] = {"content": content}
            elif msg_type == 'image':
                if not image_url:
                    return {"code": "error", "message": "发送图片消息必须提供image_url"}
                
                # 下载图片并转为Base64
                try:
                    logger.info(f"正在下载图片: {image_url}")
                    img_resp = requests.get(image_url, timeout=30)
                    img_resp.raise_for_status()
                    img_base64 = base64.b64encode(img_resp.content).decode('utf-8')
                    payload["image"] = {"content": img_base64}
                except Exception as e:
                    logger.error(f"下载或处理图片失败: {str(e)}")
                    return {"code": "error", "message": f"图片处理失败: {str(e)}"}
            else:
                # 尝试支持 'md' 作为 'markdown' 的别名，如果传入 md
                if msg_type == 'md':
                    payload["msgtype"] = "markdown"
                    payload["markdown"] = {"content": content}
                else:
                    return {"code": "error", "message": f"不支持的消息类型: {msg_type}"}
            
            # 设置请求头
            headers = {
                'Authorization': f'Bearer-{token}',
                'Content-Type': 'application/json; charset=utf-8',
                'LOGID': str(int(time.time() * 1000000))
            }
            
            # 发送POST请求
            logger.info(f"发送消息到用户 {to_users} (类型: {msg_type})")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"发送结果: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送应用消息异常: {str(e)}", exc_info=True)
            return {"code": "error", "message": f"异常: {str(e)}"}

def main():
    parser = argparse.ArgumentParser(description='发送群消息或单人消息')
    parser.add_argument('--group-id', help='群组ID (发送群消息时必填，与 --user 二选一)')
    parser.add_argument('--user', help='接收消息的用户名，支持多个，用|分隔 (发送单人消息时必填，与 --group-id 二选一)')
    parser.add_argument('--content', help='消息内容 (text/md类型必填)')
    parser.add_argument('--type', choices=['text', 'md', 'markdown', 'image'], default='md', 
                       help='消息类型: text(文本), md/markdown(Markdown), image(图片)')
    parser.add_argument('--app-key', default=DEFAULT_APP_KEY, 
                       help='应用Key（已内置默认值，无需配置）')
    parser.add_argument('--app-secret', default=DEFAULT_APP_SECRET, 
                       help='应用Secret（已内置默认值，无需配置）')
    parser.add_argument('--image-url', help='图片URL（当type=image时使用）')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    # 参数校验
    if not args.group_id and not args.user:
        print("错误: 必须指定 --group-id 或 --user 其中之一")
        sys.exit(1)
        
    if args.type in ['text', 'md', 'markdown'] and not args.content:
        print("错误: 发送文本或Markdown消息需要指定 --content")
        sys.exit(1)

    if args.type == 'image' and not args.image_url:
        print("错误: 发送图片消息需要指定 --image-url")
        sys.exit(1)
    
    # 创建发送器实例
    sender = GroupMessageSender(args.app_key, args.app_secret)
    
    # 准备内容
    content = args.content
    if content and args.type in ['md', 'markdown']:
         content = content.replace('\\n', '\n')
         if args.group_id: # 仅针对群组消息做特殊的MD格式化，或者两者都做？
             # 原有逻辑是对群消息做了 format_markdown_for_hi。
             # 假设单人消息也需要同样的格式化以保证兼容性。
             content = format_markdown_for_hi(content)
    
    # 发送消息
    result = None
    if args.user:
        # 发送单人/多人应用消息
        msg_type = args.type
        if msg_type == 'md':
            msg_type = 'markdown'
        
        result = sender.send_app_message(
            to_users=args.user,
            msg_type=msg_type,
            content=content,
            image_url=args.image_url
        )
    else:
        # 发送群组消息 (保持原有逻辑)
        if args.type == 'md' or args.type == 'markdown':
            result = sender.send_md_message(args.group_id, content)
        elif args.type == 'text':
            result = sender.send_text_message(args.group_id, content)
        elif args.type == 'image':
            result = sender.send_image_message(args.group_id, args.image_url)
    
    # 输出结果
    if result.get('code') == 'ok':
        print(f"✅ 消息发送成功")
        print(f"   消息ID: {result.get('data', {}).get('messageid', 'N/A')}")
        print(f"   发送时间: {result.get('data', {}).get('ctime', 'N/A')}")
    else:
        print(f"❌ 消息发送失败")
        print(f"   错误码: {result.get('code', 'N/A')}")
        print(f"   错误信息: {result.get('message', 'N/A')}")
        sys.exit(1)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())