#!/usr/bin/env python3
"""从 Bilibili 视频提取字幕数据，输出结构化 JSON 到 stdout。"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def make_request(url, sessdata=None):
    """发起 HTTP GET 请求并返回 JSON 响应。"""
    req = urllib.request.Request(url, headers=HEADERS)
    if sessdata:
        req.add_header("Cookie", f"SESSDATA={sessdata}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_bvid(input_str):
    """从 URL 或纯 BV 号中解析出 bvid，同时返回分 P 号。"""
    input_str = input_str.strip()

    # 纯 BV 号
    if re.match(r"^BV[\w]+$", input_str):
        return input_str, 1

    # URL 格式
    m = re.search(r"bilibili\.com/video/(BV[\w]+)", input_str)
    if m:
        bvid = m.group(1)
        # 解析分 P 参数
        p_match = re.search(r"[?&]p=(\d+)", input_str)
        page = int(p_match.group(1)) if p_match else 1
        return bvid, page

    return None, None


def get_video_info(bvid, sessdata=None):
    """获取视频基本信息（标题、UP主、时长、分P列表）。"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    data = make_request(url, sessdata)

    if data["code"] != 0:
        raise RuntimeError(f"获取视频信息失败: {data.get('message', '未知错误')}")

    info = data["data"]
    return {
        "title": info["title"],
        "author": info["owner"]["name"],
        "duration": info["duration"],
        "bvid": bvid,
        "pages": info.get("pages", []),
    }


def get_subtitle_list(bvid, cid, sessdata=None):
    """获取字幕列表。"""
    url = f"https://api.bilibili.com/x/player/wbi/v2?bvid={bvid}&cid={cid}"
    data = make_request(url, sessdata)

    if data["code"] != 0:
        raise RuntimeError(f"获取字幕列表失败: {data.get('message', '未知错误')}")

    subtitle_info = data["data"].get("subtitle", {})
    return subtitle_info.get("subtitles", [])


def select_subtitle(subtitles):
    """从可用字幕中选择最佳语言版本。优先级: zh-CN > zh-Hans > ai-zh > 第一个。"""
    if not subtitles:
        return None

    priority = ["zh-CN", "zh-Hans", "ai-zh", "zh"]
    for lang in priority:
        for sub in subtitles:
            if sub.get("lan", "") == lang:
                return sub

    # 匹配包含 zh 的
    for sub in subtitles:
        if "zh" in sub.get("lan", "").lower():
            return sub

    # 返回第一个
    return subtitles[0]


def download_subtitle(subtitle_url, sessdata=None):
    """下载字幕 JSON 内容。"""
    if subtitle_url.startswith("//"):
        subtitle_url = "https:" + subtitle_url
    elif not subtitle_url.startswith("http"):
        subtitle_url = "https:" + subtitle_url

    data = make_request(subtitle_url, sessdata)

    # 字幕 JSON 可能直接是列表或 {"body": [...]}
    if isinstance(data, dict):
        return data.get("body", [])
    return data


def format_time(seconds):
    """将秒数格式化为 MM:SS 或 HH:MM:SS。"""
    seconds = int(seconds)
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    else:
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"


def main():
    if len(sys.argv) < 2:
        print("用法: python extract.py <Bilibili视频URL或BV号>", file=sys.stderr)
        sys.exit(1)

    input_str = sys.argv[1]
    sessdata = os.environ.get("BILIBILI_SESSDATA", "")

    # 解析 BV 号
    bvid, page = parse_bvid(input_str)
    if not bvid:
        print(f"错误: 无法解析 BV 号，请提供有效的 Bilibili 视频 URL 或 BV 号", file=sys.stderr)
        sys.exit(1)

    # 获取视频信息
    try:
        video_info = get_video_info(bvid, sessdata)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 确定 cid（分 P）
    pages = video_info["pages"]
    if page > len(pages):
        print(f"错误: 视频只有 {len(pages)} P，无法获取第 {page} P", file=sys.stderr)
        sys.exit(1)

    cid = pages[page - 1]["cid"]
    page_title = pages[page - 1].get("part", "")

    # 获取字幕列表
    try:
        subtitles = get_subtitle_list(bvid, cid, sessdata)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    if not subtitles:
        print(json.dumps({
            "error": "no_subtitle",
            "message": "该视频无 CC 字幕。将使用 ASR 语音识别提取字幕。",
            "suggestion": "use_asr",
            "asr_steps": [
                f"1. 提取音频: yt-dlp -x --audio-format mp3 'https://www.bilibili.com/video/{bvid}' -o 'audio.%(ext)s'",
                "2. 三引擎转写: python3 ~/.claude/skills/bilibili-subtitle-extractor/scripts/asr.py audio.mp3",
            ],
            "title": video_info["title"],
            "author": video_info["author"],
            "duration": video_info["duration"],
            "bvid": bvid,
            "url": f"https://www.bilibili.com/video/{bvid}",
        }, ensure_ascii=False))
        sys.exit(0)

    # 选择字幕
    selected = select_subtitle(subtitles)
    if not selected:
        print(json.dumps({
            "error": "no_chinese_subtitle",
            "message": "未找到中文字幕",
            "available_languages": [s.get("lan_doc", s.get("lan", "")) for s in subtitles],
        }, ensure_ascii=False))
        sys.exit(0)

    # 下载字幕内容
    try:
        subtitle_body = download_subtitle(selected["subtitle_url"], sessdata)
    except Exception as e:
        print(f"错误: 下载字幕失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 构建输出
    result = {
        "title": video_info["title"],
        "page_title": page_title if len(pages) > 1 else "",
        "author": video_info["author"],
        "duration": video_info["duration"],
        "bvid": bvid,
        "page": page,
        "url": f"https://www.bilibili.com/video/{bvid}" + (f"?p={page}" if page > 1 else ""),
        "subtitle_language": selected.get("lan_doc", selected.get("lan", "")),
        "subtitles": [
            {
                "from": item.get("from", 0),
                "to": item.get("to", 0),
                "content": item.get("content", ""),
            }
            for item in subtitle_body
        ],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
