#!/usr/bin/env python3
"""
批量下载图片工具 - 支持从 URL 列表或文件批量下载图片

使用方法:
    # 从文件读取 URL 列表
    python download_images.py --file urls.txt --output ./images/

    # 直接传入 URL 列表
    python download_images.py --urls "url1" "url2" --output ./images/

    # 从 JSON 文件提取图片 URL
    python download_images.py --json document.json --output ./images/

功能:
    1. 支持批量下载图片
    2. 自动识别图片格式
    3. 支持自定义文件名
    4. 支持从 Markdown/JSON 文件提取图片链接
"""

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from typing import List, Tuple, Optional

# 创建 SSL 上下文（绕过证书验证）
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE
# 允许 legacy renegotiation（仅 Python 3.12+）
if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
    SSL_CONTEXT.options |= ssl.OP_LEGACY_SERVER_CONNECT


def detect_image_format(file_path: str) -> str:
    """检测图片格式"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(12)

        # PNG
        if header[:8] == b'\x89PNG\r\n\x1a\n':
            return 'png'
        # JPEG
        if header[:2] == b'\xff\xd8':
            return 'jpg'
        # GIF
        if header[:6] in (b'GIF87a', b'GIF89a'):
            return 'gif'
        # WEBP
        if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
            return 'webp'
        # BMP
        if header[:2] == b'BM':
            return 'bmp'
        return 'bin'
    except Exception:
        return 'bin'


def sanitize_filename(name: str) -> str:
    """清理文件名"""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if len(name) > 100:
        name = name[:100]
    return name or 'image'


def download_image(url: str, output_dir: str, filename: Optional[str] = None, index: int = 0) -> Tuple[bool, str]:
    """
    下载单张图片

    Args:
        url: 图片 URL
        output_dir: 输出目录
        filename: 自定义文件名（不含扩展名）
        index: 序号（用于默认文件名）

    Returns:
        (success, output_path or error_message)
    """
    try:
        # 创建临时文件
        temp_path = os.path.join(output_dir, f'_temp_download_{index}')

        # 下载
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60, context=SSL_CONTEXT) as response:
            with open(temp_path, 'wb') as f:
                f.write(response.read())

        # 检测格式
        ext = detect_image_format(temp_path)

        # 确定文件名
        if filename:
            base_name = sanitize_filename(filename)
        else:
            base_name = f'image_{index + 1:02d}'

        # 重命名
        final_path = os.path.join(output_dir, f'{base_name}.{ext}')
        os.rename(temp_path, final_path)

        return True, final_path

    except Exception as e:
        return False, str(e)


def extract_urls_from_markdown(md_file: str) -> List[str]:
    """从 Markdown 文件提取图片 URL"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    matches = re.findall(pattern, content)

    # 过滤内网图片
    return [url for _, url in matches if 'weiyun.baidu.com' in url or 'rte.weiyun.baidu.com' in url]


def extract_urls_from_json(json_file: str) -> List[str]:
    """从 JSON 文件提取图片 URL"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    urls = []
    content_str = json.dumps(data)

    # 匹配 weiyun.baidu.com 图片 URL
    pattern = r'https://[^"\s\'\]<>]+weiyun\.baidu\.com[^"\s\'\]<>]*'
    urls = list(set(re.findall(pattern, content_str)))

    # 处理 HTML 实体
    urls = [url.replace('&amp;', '&') for url in urls]

    return urls


def main():
    """ 主函数 """
    parser = argparse.ArgumentParser(description='批量下载图片工具')
    parser.add_argument('--urls', nargs='+', help='图片 URL 列表')
    parser.add_argument('--file', help='URL 列表文件（每行一个 URL）')
    parser.add_argument('--json', help='从 JSON 文件提取图片 URL')
    parser.add_argument('--markdown', '--md', help='从 Markdown 文件提取图片 URL')
    parser.add_argument('--output', '-o', default='./images/', help='输出目录')
    parser.add_argument('--prefix', help='文件名前缀')

    args = parser.parse_args()

    # 收集 URL
    urls = []

    if args.urls:
        urls.extend(args.urls)

    if args.file:
        with open(args.file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)

    if args.json:
        urls.extend(extract_urls_from_json(args.json))

    if args.markdown:
        urls.extend(extract_urls_from_markdown(args.markdown))

    if not urls:
        print('❌ 错误: 请提供图片 URL (--urls) 或来源文件 (--file/--json/--markdown)')
        sys.exit(1)

    # 去重
    urls = list(dict.fromkeys(urls))

    # 创建输出目录
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    print(f'📥 开始下载 {len(urls)} 张图片到 {output_dir}')

    # 下载
    success_count = 0
    failed = []

    for i, url in enumerate(urls):
        filename = f'{args.prefix}_{i + 1:02d}' if args.prefix else None
        success, result = download_image(url, output_dir, filename, i)

        if success:
            success_count += 1
            print(f'  ✅ [{i + 1}/{len(urls)}] {os.path.basename(result)}')
        else:
            failed.append((url, result))
            print(f'  ❌ [{i + 1}/{len(urls)}] 下载失败: {result[:50]}')

    # 总结
    print(f'\n📊 下载完成: 成功 {success_count}/{len(urls)}')
    if failed:
        print('\n失败列表:')
        for url, error in failed:
            print(f'  - {url[:80]}... : {error}')


if __name__ == '__main__':
    main()