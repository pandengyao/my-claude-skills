#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志拉取工具
用于从远程服务器下载任务日志，或从本地目录查找最新日志文件

功能:
- 从远程服务器下载指定 job 的日志文件
- 从本地目录中查找匹配前缀的最新日志文件
- 支持多种日志布局 (worker_XX/*.log, *-log.txt)

使用方法:
    # 下载指定 job 的日志
    python log_fetcher.py --job-id job-xxx --log-dir ./nccl_logs

    # 查找本地目录中的最新日志
    python log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx --log-prefix run

    # 使用环境变量配置远程服务器
    export LOG_FETCH_URL="http://xxx/api/logs"
    python log_fetcher.py --job-id job-xxx
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 尝试导入 requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(level: int = logging.WARNING) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("log_fetcher")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# ============================================================================
# 数据类
# ============================================================================

@dataclass
class LogFetchConfig:
    """日志拉取配置"""
    job_id: str = ""
    log_dir: str = ""
    log_prefix: str = "nccl"
    # 远程日志拉取 API 地址
    trigger_url: str = ""   # 触发拉取的 URL
    status_url: str = ""    # 查询状态的 URL
    poll_interval: int = 5  # 轮询间隔（秒）
    timeout: int = 30       # 超时时间（分钟）
    max_file_size: int = 10 * 1024 * 1024  # 最大文件大小（字节）
    nccl_log_dir: str = "nccl_logs"  # NCCL 日志存储目录
    encoding: str = "utf-8"

    @classmethod
    def from_env(cls) -> "LogFetchConfig":
        """从环境变量创建配置，使用项目默认值"""
        return cls(
            trigger_url=os.getenv(
                "DIAGNOSE_LOG_TRIGGER_URL",
                "http://10.206.196.162:8557/server/pdclog/log_load"
            ),
            status_url=os.getenv(
                "DIAGNOSE_LOG_STATUS_URL",
                "http://10.206.196.162:8557/server/pdclog/log_load_stat"
            ),
            poll_interval=int(os.getenv("DIAGNOSE_POLL_INTERVAL", "5")),
            timeout=int(os.getenv("DIAGNOSE_TIMEOUT", "30")),
            max_file_size=int(os.getenv("DIAGNOSE_MAX_FILE_SIZE", "10485760")),
            nccl_log_dir=os.getenv("DIAGNOSE_NCCL_LOG_DIR", "nccl_logs"),
        )


@dataclass
class LogFetchResult:
    """日志拉取结果"""
    success: bool = False
    log_dir: str = ""
    log_files: Dict[str, str] = field(default_factory=dict)  # worker -> log_file_path
    message: str = ""
    error: str = ""


# ============================================================================
# 本地日志查找
# ============================================================================

def find_local_log_dir(base_dir: str, job_id: str) -> Optional[str]:
    """
    在本地查找 job 对应的日志目录

    Args:
        base_dir: 基础日志目录 (如 nccl_logs/)
        job_id: 任务 ID

    Returns:
        找到的日志目录路径，如果没找到则返回 None
    """
    base_path = Path(base_dir)

    # 如果基础目录不存在，自动创建
    if not base_path.exists():
        try:
            base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created log directory: {base_dir}")
        except Exception as e:
            logger.error(f"Failed to create log directory {base_dir}: {e}")
            return None

    # 首先尝试精确匹配
    exact_path = base_path / job_id
    if exact_path.is_dir():
        return str(exact_path)

    # 然后尝试前缀匹配
    for entry in base_path.iterdir():
        if entry.is_dir() and entry.name.startswith(job_id):
            return str(entry)

    return None


def find_latest_logs_with_prefix(
    log_dir: str,
    prefix: str = "nccl"
) -> Dict[str, str]:
    """
    从日志目录中查找匹配前缀的最新日志文件

    参考 Go 版本的 LatestLogsWithPrefix 函数实现

    Args:
        log_dir: 日志目录路径
        prefix: 日志文件前缀 (如 "nccl", "run")

    Returns:
        worker -> log_file_path 的映射
    """
    log_files: Dict[str, str] = {}

    log_path = Path(log_dir)
    if not log_path.exists():
        return log_files

    # 查找所有 worker_* 目录
    worker_dirs = sorted(log_path.glob("worker_*"))

    for worker_dir in worker_dirs:
        if not worker_dir.is_dir():
            continue

        worker_name = worker_dir.name
        latest_file: Optional[Path] = None
        latest_mtime: float = 0

        # 遍历目录下的所有 .log 文件
        for log_file in worker_dir.glob("*.log"):
            if log_file.is_dir():
                continue

            # 检查文件名是否匹配前缀
            if prefix and not log_file.name.startswith(prefix):
                continue

            # 按修改时间取最新的
            mtime = log_file.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = log_file

        if latest_file:
            log_files[worker_name] = str(latest_file)
            logger.debug(f"Found latest log for {worker_name}: {latest_file}")

    return log_files


def check_logs_exist(log_dir: str, prefix: str = "run") -> Tuple[bool, int]:
    """
    检查日志目录中是否存在匹配前缀的日志文件

    Returns:
        (是否存在, 文件数量)
    """
    log_files = find_latest_logs_with_prefix(log_dir, prefix)
    return len(log_files) > 0, len(log_files)


# ============================================================================
# 远程日志拉取
# ============================================================================

def trigger_log_fetch(config: LogFetchConfig) -> Optional[str]:
    """
    触发远程日志拉取

    Args:
        config: 拉取配置

    Returns:
        任务 ID 或 None
    """
    if not REQUESTS_AVAILABLE:
        logger.error("requests 库不可用，无法拉取远程日志")
        return None

    if not config.trigger_url:
        logger.error("DIAGNOSE_LOG_TRIGGER_URL 未配置")
        return None

    try:
        response = requests.post(
            config.trigger_url,
            json={"job_id": config.job_id},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Trigger response: {data}")
        return data.get("task_id") or data.get("job_id") or config.job_id
    except Exception as e:
        logger.error(f"触发日志拉取失败: {e}")
        return None


def poll_log_fetch_status(
    config: LogFetchConfig,
    task_id: str
) -> Optional[str]:
    """
    轮询日志拉取状态

    Args:
        config: 拉取配置
        task_id: 任务 ID

    Returns:
        日志目录路径或 None
    """
    if not REQUESTS_AVAILABLE:
        return None

    if not config.status_url:
        logger.error("DIAGNOSE_LOG_STATUS_URL 未配置")
        return None

    start_time = time.time()
    timeout_seconds = config.timeout * 60  # 转换为秒

    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(
                config.status_url,
                params={"job_id": task_id},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            logger.debug(f"Status response: {data}")

            status = data.get("status") or data.get("state")
            if status in ("completed", "done", "success"):
                # 返回日志目录
                log_dir = data.get("log_dir") or data.get("path")
                if log_dir:
                    return log_dir
                # 如果没有返回目录，使用默认目录
                return os.path.join(config.nccl_log_dir, config.job_id)
            elif status in ("failed", "error"):
                logger.error(f"日志拉取失败: {data.get('error') or data.get('message')}")
                return None

            logger.info(f"日志拉取状态: {status}, 等待中...")
            time.sleep(config.poll_interval)

        except Exception as e:
            logger.error(f"查询状态失败: {e}")
            time.sleep(config.poll_interval)

    logger.error("日志拉取超时")
    return None


def fetch_logs_from_remote(config: LogFetchConfig) -> LogFetchResult:
    """
    从远程服务器拉取日志

    Args:
        config: 拉取配置

    Returns:
        拉取结果
    """
    result = LogFetchResult()

    # 触发拉取
    task_id = trigger_log_fetch(config)
    if not task_id:
        result.error = "触发日志拉取失败，请检查 DIAGNOSE_LOG_TRIGGER_URL 配置"
        return result

    logger.info(f"已触发日志拉取，task_id: {task_id}")

    # 轮询状态
    log_dir = poll_log_fetch_status(config, task_id)
    if not log_dir:
        result.error = "日志拉取超时或失败"
        return result

    result.success = True
    result.log_dir = log_dir
    result.message = f"日志已拉取到 {log_dir}"

    return result


# ============================================================================
# 主函数
# ============================================================================

def fetch_logs(config: LogFetchConfig) -> LogFetchResult:
    """
    获取日志文件

    逻辑:
    1. 首先检查本地是否存在日志
    2. 如果不存在，尝试从远程拉取
    3. 返回最新的日志文件映射

    Args:
        config: 拉取配置

    Returns:
        拉取结果
    """
    result = LogFetchResult()

    # 确定日志目录
    log_dir = config.log_dir
    if not log_dir and config.job_id:
        # 尝试在配置的日志目录下查找
        log_dir = find_local_log_dir(config.nccl_log_dir, config.job_id)

    if log_dir:
        # 检查本地日志是否存在
        has_logs, count = check_logs_exist(log_dir, config.log_prefix)
        if has_logs:
            result.success = True
            result.log_dir = log_dir
            result.log_files = find_latest_logs_with_prefix(log_dir, config.log_prefix)
            result.message = f"找到 {count} 个日志文件在 {log_dir}"
            return result

    # 本地没有日志，尝试从远程拉取
    if config.trigger_url:
        logger.info(f"本地未找到日志，从远程拉取...")
        remote_result = fetch_logs_from_remote(config)
        if remote_result.success:
            result.success = True
            result.log_dir = remote_result.log_dir
            result.log_files = find_latest_logs_with_prefix(
                remote_result.log_dir,
                config.log_prefix
            )
            result.message = remote_result.message
        else:
            result.error = remote_result.error
    else:
        # 生成友好的错误提示
        suggestions = []
        if config.job_id:
            suggestions.append(f"1. 请确认 Job ID '{config.job_id}' 是否正确")
            suggestions.append(f"2. 请手动下载日志到 {config.nccl_log_dir}/{config.job_id}/ 目录")
        else:
            suggestions.append("1. 请提供 --job-id 参数")
        suggestions.append("3. 或配置以下环境变量以启用远程拉取:")
        suggestions.append("   - DIAGNOSE_LOG_TRIGGER_URL")
        suggestions.append("   - DIAGNOSE_LOG_STATUS_URL")

        result.error = "本地未找到日志文件"
        result.message = "建议:\n" + "\n".join(suggestions)

    return result


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="日志拉取工具 - 从远程服务器下载或查找本地日志",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查找本地日志
  %(prog)s --find-latest --log-dir ./nccl_logs/job-xxx --log-prefix run

  # 下载远程日志
  %(prog)s --job-id job-xxx --log-dir ./nccl_logs

  # 使用环境变量配置
  export LOG_FETCH_URL="http://xxx/api/logs"
  %(prog)s --job-id job-xxx
        """
    )

    parser.add_argument(
        '--job-id',
        help='任务 ID（以 job- 开头）'
    )

    parser.add_argument(
        '--log-dir',
        help='日志目录路径'
    )

    parser.add_argument(
        '--log-prefix',
        default='nccl',
        help='日志文件前缀，默认为 nccl'
    )

    parser.add_argument(
        '--find-latest',
        action='store_true',
        help='仅查找本地目录中的最新日志'
    )

    parser.add_argument(
        '--check-exists',
        action='store_true',
        help='检查日志是否存在'
    )

    parser.add_argument(
        '--output', '-o',
        help='输出结果到指定 JSON 文件'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='增加日志详细程度'
    )

    return parser


def main() -> int:
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 设置日志级别
    if args.verbose >= 2:
        level = logging.DEBUG
    elif args.verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    setup_logging(level)

    # 从环境变量加载配置
    config = LogFetchConfig.from_env()
    config.job_id = args.job_id or ""
    config.log_dir = args.log_dir or ""
    config.log_prefix = args.log_prefix

    # 仅检查是否存在
    if args.check_exists:
        if not args.log_dir:
            print(json.dumps({"error": "--log-dir is required for --check-exists"}))
            return 1
        has_logs, count = check_logs_exist(args.log_dir, args.log_prefix)
        result = {
            "exists": has_logs,
            "count": count,
            "log_dir": args.log_dir,
            "log_prefix": args.log_prefix
        }
        print(json.dumps(result, indent=2))
        return 0

    # 仅查找本地日志
    if args.find_latest:
        if not args.log_dir:
            print(json.dumps({"error": "--log-dir is required for --find-latest"}))
            return 1
        log_files = find_latest_logs_with_prefix(args.log_dir, args.log_prefix)
        result = {
            "success": len(log_files) > 0,
            "log_dir": args.log_dir,
            "log_files": log_files,
            "count": len(log_files)
        }
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(output, encoding='utf-8')
        else:
            print(output)
        return 0

    # 完整的日志拉取流程
    if not config.job_id and not config.log_dir:
        result = {
            "success": False,
            "error": "请提供 --job-id 或 --log-dir 参数",
            "usage": "python scripts/log_fetcher.py --job-id job-xxx"
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 1

    fetch_result = fetch_logs(config)
    output = json.dumps({
        "success": fetch_result.success,
        "log_dir": fetch_result.log_dir,
        "log_files": fetch_result.log_files,
        "count": len(fetch_result.log_files),
        "message": fetch_result.message,
        "error": fetch_result.error
    }, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
    else:
        print(output)

    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
