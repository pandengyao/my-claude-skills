#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库文档读取工具 - 用于 relay-oncall Skill

从百度知识库(ku.baidu-int.com)读取文档内容并转为纯文本输出。
支持通过 doc_id 或 URL 读取。

用法:
    python3 scripts/read_ku_doc.py <doc_id>
    python3 scripts/read_ku_doc.py --url <ku_url>

示例:
    python3 scripts/read_ku_doc.py Cr_hhsEDud8tPP
    python3 scripts/read_ku_doc.py --url "https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/HXFtYvbMQj/ZdzjXS3uzb/Cr_hhsEDud8tPP"
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path


def get_token():
    """获取认证Token，优先环境变量，其次登录文件"""
    token = os.getenv('COMATE_AUTH_TOKEN')
    if token:
        return token.strip()
    login_file = Path.home() / '.comate' / 'login'
    if login_file.exists():
        with open(login_file, 'r', encoding='utf-8') as f:
            token = f.read().strip()
            if token:
                return token
    return ""


def query_content(doc_id=None, url=None):
    """查询知识库文档内容"""
    base_url = 'http://10.11.152.208:8701/api/process/ku'
    token = get_token()

    if not token:
        print("错误: 未找到认证Token", file=sys.stderr)
        print("请设置环境变量 COMATE_AUTH_TOKEN 或确保 ~/.comate/login 文件存在", file=sys.stderr)
        sys.exit(1)

    data = {"showDocInfo": True}
    if doc_id:
        data["docId"] = doc_id
    if url:
        data["url"] = url

    headers = {
        'Content-Type': 'application/json',
        'x-ac-Authorization': token
    }

    response = requests.post(
        f"{base_url}/ku/openapi/queryContent",
        headers=headers,
        json=data,
        timeout=60
    )
    response.raise_for_status()
    return response.json()


def extract_text(blocks):
    """将知识库富文本 blocks 转为纯文本"""
    lines = []
    if isinstance(blocks, list):
        for block in blocks:
            _extract_block(block, lines)
    return '\n'.join(lines)


def _extract_block(block, lines):
    """递归提取单个 block 的文本"""
    if not isinstance(block, dict):
        return

    btype = block.get('type', '')
    children = block.get('children', [])

    # 跳过图片
    if btype in ('image', 'image-gallery'):
        return

    # 处理表格
    if btype == 'table':
        for row in children:
            cells = row.get('children', [])
            cell_texts = []
            for cell in cells:
                ct = extract_text(cell.get('children', []))
                cell_texts.append(ct.replace('\n', ' '))
            lines.append('| ' + ' | '.join(cell_texts) + ' |')
        return

    # 提取文本片段
    text_parts = []
    child_blocks = []
    for child in children:
        if isinstance(child, dict):
            if 'text' in child and child.get('type') in (None, ''):
                t = child.get('text', '')
                if t:
                    text_parts.append(t)
            elif 'text' in child and not child.get('children'):
                t = child.get('text', '')
                if t:
                    text_parts.append(t)
            else:
                child_blocks.append(child)

    # 添加格式前缀
    prefix = ''
    if btype == 'title':
        prefix = '# '
    elif btype == 'heading':
        level = block.get('level', 1)
        prefix = '#' * (level + 1) + ' '
    elif btype == 'unordered-list-item':
        prefix = '  ' * block.get('depth', 0) + '- '
    elif btype == 'ordered-list-item':
        prefix = '  ' * block.get('depth', 0) + '1. '
    elif btype == 'code-block':
        prefix = '    '

    line = prefix + ''.join(text_parts)
    if line.strip():
        lines.append(line)

    for cb in child_blocks:
        _extract_block(cb, lines)


def main():
    parser = argparse.ArgumentParser(description='读取百度知识库文档内容')
    parser.add_argument('doc_id', nargs='?', help='文档ID')
    parser.add_argument('--url', help='文档URL')
    args = parser.parse_args()

    if not args.doc_id and not args.url:
        parser.error('请提供 doc_id 或 --url 参数')

    result = query_content(doc_id=args.doc_id, url=args.url)
    blocks = result.get('result', {}).get('content', [])
    text = extract_text(blocks)
    print(text)


if __name__ == '__main__':
    main()
