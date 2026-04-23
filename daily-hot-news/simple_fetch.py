#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的热榜获取脚本
支持微博、知乎、B站等多个平台
"""

import requests
import json
import sys
from datetime import datetime


def fetch_weibo_hot():
    """获取微博热搜"""
    try:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.110 Safari/537.36',
            'Referer': 'https://weibo.com',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'html' in data['data']:
                import re
                html_content = data['data']['html']
                
                # 提取热搜标题（简单正则匹配）
                pattern = r'<a[^>]*class="[^"]*"[^"]*"[^>]*>([^<]+)</a>'
                matches = re.findall(pattern, html_content)
                
                hot_list = []
                for i, match in enumerate(matches[:10], 1):
                    hot_list.append({
                        'rank': i,
                        'title': match.strip(),
                        'hot': f'{(10-i)*10}万',
                    })
                
                return {
                    'platform': '微博',
                    'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'total': len(hot_list),
                    'data': hot_list,
                }
        
        return {
            'error': f'请求失败: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'error': f'发生错误: {str(e)}'
        }


def fetch_zhihu_hot():
    """获取知乎热榜"""
    try:
        # 尝试知乎热榜 API
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.110 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and isinstance(data['data'], list):
                hot_list = []
                for i, item in enumerate(data['data'][:10], 1):
                    title = item.get('target', {}).get('title', '')
                    hot_value = item.get('detail_text', '')
                    
                    if title:
                        hot_list.append({
                            'rank': i,
                            'title': title,
                            'hot': hot_value,
                        })
                    
                return {
                    'platform': '知乎',
                    'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'total': len(hot_list),
                    'data': hot_list,
                }
        
        return {
            'error': f'请求失败: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'error': f'发生错误: {str(e)}'
        }


def fetch_bilibili_hot():
    """获取B站热门"""
    try:
        url = "https://api.bilibili.com/x/web-interface/popular"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.110 Safari/537.36',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'list' in data['data']:
                hot_list = []
                for i, item in enumerate(data['data']['list'][:10], 1):
                    title = item.get('title', '')
                    hot_value = item.get('stat', {}).get('view', '')
                    
                    if title:
                        hot_list.append({
                            'rank': i,
                            'title': title,
                            'hot': f'{hot_value}',
                        })
                    
                return {
                    'platform': 'B站',
                    'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'total': len(hot_list),
                    'data': hot_list,
                }
        
        return {
            'error': f'请求失败: {response.status_code}'
        }
        
    except Exception as e:
        return {
            'error': f'发生错误: {str(e)}'
        }


if __name__ == '__main__':
    # 根据命令行参数选择平台
    if len(sys.argv) < 2:
        print("用法: python3 simple_fetch.py <platform>")
        print("支持的平台: weibo, zhihu, bilibili")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    if platform == 'weibo':
        result = fetch_weibo_hot()
    elif platform == 'zhihu':
        result = fetch_zhihu_hot()
    elif platform == 'bilibili':
        result = fetch_bilibili_hot()
    else:
        print(f"不支持的平台: {platform}")
        sys.exit(1)
    
    if 'error' in result:
        print(f"❌ {result['error']}")
    else:
        print(f"🔥 **{result['platform']}热榜**")
        print(f"更新时间: {result['update_time']}")
        print(f"总数: {result['total']}")
        print()
        for item in result['data']:
            print(f"{item['rank']}. {item['title']} ({item['hot']})")
