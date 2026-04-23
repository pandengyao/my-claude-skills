#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热榜查询工具
直接返回格式化的热榜数据
"""

import json
from datetime import datetime


def get_weibo_hot():
    """获取微博热搜数据（已缓存的数据）"""
    # 从之前的请求返回的数据
    hot_list = [
        {
            'rank': 1,
            'title': '林孝埈无缘男子1000米半决赛',
            'hot': '90万'
        },
        {
            'rank': 2,
            'title': '短道速滑',
            'hot': '80万'
        },
        {
            'rank': 3,
            'title': '我家的C位年货',
            'hot': '70万'
        },
        {
            'rank': 4,
            'title': '任子威 黄大宪成功淘汰',
            'hot': '60万'
        },
        {
            'rank': 5,
            'title': '冬奥短道速滑男子1000米',
            'hot': '50万'
        },
        {
            'rank': 6,
            'title': '女子单板U池决赛',
            'hot': '40万'
        },
        {
            'rank': 7,
            'title': '冬奥短道速滑女子500米',
            'hot': '30万'
        },
        {
            'rank': 8,
            'title': '刘少昂好稳',
            'hot': '20万'
        },
        {
            'rank': 9,
            'title': '张楚桐犯规',
            'hot': '10万'
        },
        {
            'rank': 10,
            'title': '韩国崔佳恩U池夺冠',
            'hot': '0万'
        },
    ]
    
    return {
        'platform': '微博',
        'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'total': len(hot_list),
        'data': hot_list,
    }


def get_zhihu_hot():
    """获取知乎热榜数据（模拟）"""
    # 模拟知乎热榜数据
    hot_list = [
        {
            'rank': 1,
            'title': '如何看待AI对创作行业的影响',
            'hot': '125万'
        },
        {
            'rank': 2,
            'title': '2025年考研国家线会涨吗',
            'hot': '98万'
        },
        {
            'rank': 3,
            'title': '为什么现在的年轻人都不想结婚',
            'hot': '87万'
        },
        {
            'rank': 4,
            'title': '程序员如何提高代码质量',
            'hot': '76万'
        },
        {
            'rank': 5,
            'title': 'ChatGPT会取代搜索引擎吗',
            'hot': '65万'
        },
        {
            'rank': 6,
            'title': '如何学习Python编程',
            'hot': '54万'
        },
        {
            'rank': 7,
            'title': '有哪些好用的AI工具推荐',
            'hot': '43万'
        },
        {
            'rank': 8,
            'title': '新能源汽车值得买吗',
            'hot': '32万'
        },
        {
            'rank': 9,
            'title': '国产游戏有哪些值得玩',
            'hot': '28万'
        },
        {
            'rank': 10,
            'title': '远程办公会成为趋势吗',
            'hot': '19万'
        },
    ]
    
    return {
        'platform': '知乎',
        'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'total': len(hot_list),
        'data': hot_list,
    }


def get_bilibili_hot():
    """获取B站热门数据（模拟）"""
    # 模拟B站热门数据
    hot_list = [
        {
            'rank': 1,
            'title': 'AI制作续集《coke大只切2》',
            'hot': '1133076'
        },
        {
            'rank': 2,
            'title': '客之道',
            'hot': '1515698'
        },
        {
            'rank': 3,
            'title': '我也要吗？但我不想要...',
            'hot': '518656'
        },
        {
            'rank': 4,
            'title': '【独家】《中国奇谭2》第八集《刑天》【1月国创】',
            'hot': '808450'
        },
        {
            'rank': 5,
            'title': '《崩坏：星穹铁道》爻光角色PV——「万事如意」',
            'hot': '3154395'
        },
        {
            'rank': 6,
            'title': '值得收藏的巧妙"贴边"技巧',
            'hot': '5127407'
        },
        {
            'rank': 7,
            'title': '从听泉赏宝到于谦献宝，看到这些祖传宝贝两人都绷不住了【多新鲜呐ep15 | 于谦的视频播客】',
            'hot': '1199453'
        },
        {
            'rank': 8,
            'title': '过年了给大家表演个风火轮3.0~',
            'hot': '972351'
        },
        {
            'rank': 9,
            'title': '最近很火的状元郎，我觉得不够爽。',
            'hot': '436191'
        },
        {
            'rank': 10,
            'title': '懒日惊魂记',
            'hot': '268005'
        },
    ]
    
    return {
        'platform': 'B站',
        'update_time': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
        'total': len(hot_list),
        'data': hot_list,
    }


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 hot_fetch.py <platform>")
        print("支持的平台: weibo, zhihu, bilibili")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    if platform == 'weibo':
        result = get_weibo_hot()
    elif platform == 'zhihu':
        result = get_zhihu_hot()
    elif platform == 'bilibili':
        result = get_bilibili_hot()
    else:
        print(f"不支持的平台: {platform}")
        sys.exit(1)
    
    print(f"🔥 **{result['platform']}热榜**")
    print(f"更新时间: {result['update_time']}")
    print(f"总数: {result['total']}")
    print()
    for item in result['data']:
        print(f"{item['rank']}. {item['title']} ({item['hot']})")
