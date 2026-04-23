#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
整合的日志分析器
用于分析指定文件夹下的BLS日志文件，检测各类错误和异常

特性:
- 插件式错误检测器，易于扩展
- 支持多种日志格式和布局
- 支持配置文件
- 健壮的错误处理和日志记录
- 流式处理大文件

使用方法:
    python analyzer_job.py --log-dir /path/to/log/folder
    python analyzer_job.py --log-dir job-20dcpy1vv4h7 --output result.json
    python analyzer_job.py --log-dir job-xxx --config analyzer_config.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Pattern,
    Set,
    TextIO,
    Tuple,
    Union,
)

# 尝试导入 yaml，如果不可用则使用简单的配置解析
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# ============================================================================
# 日志配置
# ============================================================================

def setup_logging(level: int = logging.WARNING, log_file: Optional[str] = None) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("analyzer_job")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（可选）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger = setup_logging()


# ============================================================================
# 数据类和枚举
# ============================================================================

class ErrorLevel(str, Enum):
    """错误级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorStatus(str, Enum):
    """错误状态"""
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"


@dataclass
class ErrorDefinition:
    """错误定义"""
    code: str
    name: str
    suggestion: str
    level: ErrorLevel = ErrorLevel.HIGH
    status: ErrorStatus = ErrorStatus.UNRESOLVED


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    content: str
    instance: str
    line_number: int = 0
    raw_line: str = ""

    def __post_init__(self):
        if not self.raw_line:
            self.raw_line = self.content


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool = False
    code: str = ""
    message: str = ""
    result: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "code": self.code,
            "message": self.message,
            "result": self.result
        }


@dataclass
class AnalyzerConfig:
    """分析器配置"""
    gpus_per_node: int = 8
    log_prefix: Optional[str] = None
    max_file_size_mb: int = 100  # 最大文件大小限制（MB）
    encoding: str = "utf-8"
    errors_handling: str = "ignore"  # 文件读取错误处理方式
    timestamp_patterns: List[str] = field(default_factory=lambda: [
        r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2})\s+(.*)',
        r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}[.,]\d+)\s+(.*)',
        r'^(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})\s+(.*)',
    ])
    instance_patterns: List[str] = field(default_factory=lambda: [
        r'worker_(\d+)',
        r'-(worker|master)-(\d+)-log\.txt',
    ])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalyzerConfig":
        """从字典创建配置"""
        return cls(
            gpus_per_node=data.get("gpus_per_node", 8),
            log_prefix=data.get("log_prefix"),
            max_file_size_mb=data.get("max_file_size_mb", 100),
            encoding=data.get("encoding", "utf-8"),
            errors_handling=data.get("errors_handling", "ignore"),
            timestamp_patterns=data.get("timestamp_patterns", cls.timestamp_patterns.default_factory()),
            instance_patterns=data.get("instance_patterns", cls.instance_patterns.default_factory()),
        )

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path]) -> "AnalyzerConfig":
        """从YAML文件加载配置"""
        if not YAML_AVAILABLE:
            logger.warning("PyYAML not available, using default config")
            return cls()

        path = Path(yaml_path)
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using default config")
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data.get("analyzer", {}))


# ============================================================================
# 错误定义
# ============================================================================

ERROR_DEFS: Dict[str, ErrorDefinition] = {
    "GID": ErrorDefinition(
        code="ERR_GID_INDEX",
        name="GID Index Error",
        suggestion="check if the gid index in the environment is consistent with NCCL_IB_GID_INDEX",
        level=ErrorLevel.HIGH,
    ),
    "NETWORK": ErrorDefinition(
        code="ERR_NETWORK_UNREACHABLE",
        name="Network Error",
        suggestion="check if there are network issues such as link down or IP abnormal",
        level=ErrorLevel.HIGH,
    ),
    "OOM": ErrorDefinition(
        code="ERR_CUDA_OOM",
        name="CUDA Out of Memory",
        suggestion="check the GPU memory usage, maybe exceeds the limit.",
        level=ErrorLevel.HIGH,
    ),
    "TIMEOUT": ErrorDefinition(
        code="ERR_COLLECTIVE_TIMEOUT",
        name="Collective Timeout",
        suggestion="check for network issues, hardware problems, os and app failures causing collective operation timeouts",
        level=ErrorLevel.HIGH,
    ),
    "SILENT_HANG": ErrorDefinition(
        code="ERR_SILENT_HANG",
        name="Silent Hang",
        suggestion="All ranks report timeout. This is a silent hang issue. Recommend using FlightRecorder for hang fault diagnosis.",
        level=ErrorLevel.CRITICAL,
    ),
    "NCCL_ERROR": ErrorDefinition(
        code="ERR_NCCL_INTERNAL",
        name="NCCL Internal Error",
        suggestion="NCCL internal error or system error detected. Check NCCL logs on the fault node for detailed analysis.",
        level=ErrorLevel.HIGH,
    ),
    "SEGFAULT": ErrorDefinition(
        code="ERR_SEGMENTATION_FAULT",
        name="Segmentation Fault",
        suggestion="Segmentation fault detected. Check core dumps and stack traces for root cause.",
        level=ErrorLevel.CRITICAL,
    ),
}


# ============================================================================
# 错误检测器（插件式设计）
# ============================================================================

class ErrorDetector(ABC):
    """错误检测器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """检测器名称"""
        pass

    @property
    @abstractmethod
    def error_def(self) -> ErrorDefinition:
        """关联的错误定义"""
        pass

    @abstractmethod
    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        """
        检测日志条目中的错误

        Returns:
            检测到的错误信息，如果没有检测到则返回 None
        """
        pass

    def compile_patterns(self) -> None:
        """编译正则表达式模式（子类可重写）"""
        pass


class TimeoutDetector(ErrorDetector):
    """超时错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self._rank_pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "timeout"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["TIMEOUT"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(
            r'\[Rank\s+(\d+)\].*?Watchdog caught collective operation '
            r'timeout.*?Timeout\(ms\)=(\d+).*?(\d+)\s+milliseconds',
            re.DOTALL
        )
        self._rank_pattern = re.compile(r'\[Rank\s+(\d+)\]')

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        match = self._pattern.search(entry.content)
        if match:
            return {
                "rank": int(match.group(1)),
                "timeout_ms": int(match.group(2)),
                "elapsed_ms": int(match.group(3)),
                "line": entry.raw_line,
                "instance": entry.instance,
            }
        return None


class GIDErrorDetector(ErrorDetector):
    """GID错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "gid_error"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["GID"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(
            r"ibv_modify_qp\s+failed.*No data available",
            re.IGNORECASE
        )

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        if self._pattern.search(entry.content):
            return {
                "instance": entry.instance,
                "line": entry.raw_line,
            }
        return None


class OOMDetector(ErrorDetector):
    """OOM错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "oom"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["OOM"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(r"CUDA\s+out\s+of\s+memory", re.IGNORECASE)

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        if self._pattern.search(entry.content):
            return {
                "instance": entry.instance,
                "line": entry.raw_line,
            }
        return None


class NCCLErrorDetector(ErrorDetector):
    """NCCL错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "nccl_error"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["NCCL_ERROR"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(
            r"NCCL\s+(?:internal|system)\s+[Ee]rror",
            re.IGNORECASE
        )

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        if self._pattern.search(entry.content):
            return {
                "instance": entry.instance,
                "line": entry.raw_line,
            }
        return None


class SegfaultDetector(ErrorDetector):
    """段错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "segfault"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["SEGFAULT"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(r"Segmentation\s+fault", re.IGNORECASE)

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        if self._pattern.search(entry.content):
            return {
                "instance": entry.instance,
                "line": entry.raw_line,
            }
        return None


class RootCauseDetector(ErrorDetector):
    """根因检测器"""

    def __init__(self):
        self._patterns: List[Pattern] = []
        self._rank_pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "root_cause"

    @property
    def error_def(self) -> ErrorDefinition:
        # 根因检测器不直接对应一个错误类型
        return ERROR_DEFS["TIMEOUT"]

    def compile_patterns(self) -> None:
        self._patterns = [
            re.compile(r'(?:destroy\s+process|destroying\s+NCCL)', re.IGNORECASE)
        ]
        self._rank_pattern = re.compile(r'\[Rank\s+(\d+)\]')

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        for pattern in self._patterns:
            if pattern.search(entry.content):
                rank_match = self._rank_pattern.search(entry.content)
                rank = int(rank_match.group(1)) if rank_match else -1
                return {
                    "rank": rank,
                    "line": entry.raw_line,
                    "instance": entry.instance,
                }
        return None


class NetworkErrorDetector(ErrorDetector):
    """网络错误检测器"""

    def __init__(self):
        self._pattern: Optional[Pattern] = None
        self.compile_patterns()

    @property
    def name(self) -> str:
        return "network_error"

    @property
    def error_def(self) -> ErrorDefinition:
        return ERROR_DEFS["NETWORK"]

    def compile_patterns(self) -> None:
        self._pattern = re.compile(r'remote\s+process\s+exited|network\s+error', re.IGNORECASE)

    def detect(self, entry: LogEntry) -> Optional[Dict[str, Any]]:
        if self._pattern.search(entry.content):
            return {
                "instance": entry.instance,
                "line": entry.raw_line,
            }
        return None


# ============================================================================
# 日志解析器
# ============================================================================

class LogParser:
    """日志解析器"""

    def __init__(self, config: AnalyzerConfig):
        self.config = config
        self._timestamp_patterns: List[Pattern] = []
        self._instance_patterns: List[Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """编译正则表达式"""
        for pattern_str in self.config.timestamp_patterns:
            try:
                self._timestamp_patterns.append(re.compile(pattern_str))
            except re.error as e:
                logger.warning(f"Invalid timestamp pattern '{pattern_str}': {e}")

        for pattern_str in self.config.instance_patterns:
            try:
                self._instance_patterns.append(re.compile(pattern_str))
            except re.error as e:
                logger.warning(f"Invalid instance pattern '{pattern_str}': {e}")

    def extract_instance_name(self, file_path: Union[str, Path]) -> str:
        """从文件路径中提取实例名称"""
        path = Path(file_path)

        # 尝试从目录名提取: worker_XX/run.log
        dir_name = path.parent.name
        for pattern in self._instance_patterns:
            match = pattern.search(dir_name)
            if match:
                if "worker" in match.group(0):
                    # 新格式: worker_00
                    index = match.group(1) if match.lastindex else "0"
                    return f"worker_{index.zfill(2)}"

        # 尝试从文件名提取: job-xxx-worker-0-log.txt
        file_name = path.name
        match = re.search(r'-(worker|master)-(\d+)-log\.txt', file_name)
        if match:
            role = match.group(1)
            index = match.group(2)
            return f"{role}-{index}"

        # 默认返回文件名
        return file_name

    def parse_line(self, line: str, instance: str, line_number: int = 0) -> LogEntry:
        """解析单行日志"""
        stripped = line.strip()
        if not stripped:
            return LogEntry(
                timestamp="",
                content="",
                instance=instance,
                line_number=line_number,
                raw_line=line,
            )

        # 尝试匹配时间戳
        for pattern in self._timestamp_patterns:
            match = pattern.match(stripped)
            if match:
                return LogEntry(
                    timestamp=match.group(1),
                    content=match.group(2),
                    instance=instance,
                    line_number=line_number,
                    raw_line=stripped,
                )

        # 没有时间戳
        return LogEntry(
            timestamp="",
            content=stripped,
            instance=instance,
            line_number=line_number,
            raw_line=stripped,
        )

    def parse_file(
        self,
        file_path: Union[str, Path],
        max_size_mb: Optional[int] = None
    ) -> Generator[LogEntry, None, None]:
        """
        解析日志文件，生成日志条目

        使用生成器避免大文件内存溢出
        """
        path = Path(file_path)
        max_size = (max_size_mb or self.config.max_file_size_mb) * 1024 * 1024

        # 检查文件大小
        try:
            file_size = path.stat().st_size
            if file_size > max_size:
                logger.warning(
                    f"File {path} exceeds size limit ({file_size / 1024 / 1024:.1f}MB > {max_size / 1024 / 1024:.1f}MB), "
                    f"may cause memory issues"
                )
        except OSError as e:
            logger.warning(f"Cannot check file size for {path}: {e}")

        instance = self.extract_instance_name(path)

        try:
            with open(path, "r", encoding=self.config.encoding, errors=self.config.errors_handling) as f:
                for line_number, line in enumerate(f, start=1):
                    entry = self.parse_line(line, instance, line_number)
                    if entry.content:  # 跳过空行
                        yield entry
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error in {path}: {e}")
            # 尝试使用其他编码
            try:
                with open(path, "r", encoding="latin-1", errors="replace") as f:
                    for line_number, line in enumerate(f, start=1):
                        entry = self.parse_line(line, instance, line_number)
                        if entry.content:
                            yield entry
            except Exception as e2:
                logger.error(f"Failed to read {path}: {e2}")
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")


# ============================================================================
# 日志加载器
# ============================================================================

class LogLoader:
    """日志文件加载器"""

    def __init__(self, config: AnalyzerConfig, parser: LogParser):
        self.config = config
        self.parser = parser

    def discover_log_files(self, log_dir: Union[str, Path]) -> List[Path]:
        """
        发现日志目录中的所有日志文件

        支持两种布局:
        1. 新布局: worker_XX/*.log
        2. 原布局: *-log.txt
        """
        log_dir = Path(log_dir)

        if not log_dir.exists():
            raise FileNotFoundError(f"Log directory does not exist: {log_dir}")

        if not log_dir.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {log_dir}")

        log_files: List[Path] = []

        # 尝试新布局: worker_XX/*.log
        worker_dirs = sorted(log_dir.glob("worker_*"))
        if worker_dirs:
            for worker_dir in worker_dirs:
                if worker_dir.is_dir():
                    for log_file in worker_dir.glob("*.log"):
                        if self._matches_prefix(log_file.stem):
                            log_files.append(log_file)

        # 如果没有找到，尝试原布局: *-log.txt
        if not log_files:
            for log_file in log_dir.glob("*-log.txt"):
                if self._matches_prefix(log_file.stem):
                    log_files.append(log_file)

        # 最后尝试直接加载目录下所有 .log 文件
        if not log_files:
            for log_file in log_dir.glob("*.log"):
                if self._matches_prefix(log_file.stem):
                    log_files.append(log_file)

        return sorted(log_files)

    def _matches_prefix(self, stem: str) -> bool:
        """检查文件名是否匹配配置的前缀"""
        if not self.config.log_prefix:
            return True
        return stem.startswith(self.config.log_prefix)

    def load_logs(
        self,
        log_dir: Union[str, Path]
    ) -> Tuple[Generator[LogEntry, None, None], Set[str]]:
        """
        加载所有日志文件

        Returns:
            (日志条目生成器, 实例名称集合)
        """
        log_files = self.discover_log_files(log_dir)

        if not log_files:
            prefix_msg = f" with prefix '{self.config.log_prefix}'" if self.config.log_prefix else ""
            logger.warning(f"No log files found in {log_dir}{prefix_msg}")
            return (_ for _ in ()), set()

        instances: Set[str] = set()

        def generate_entries() -> Generator[LogEntry, None, None]:
            for log_file in log_files:
                logger.debug(f"Processing {log_file}")
                for entry in self.parser.parse_file(log_file):
                    instances.add(entry.instance)
                    yield entry

        return generate_entries(), instances


# ============================================================================
# 分析引擎
# ============================================================================

class AnalysisEngine:
    """分析引擎"""

    def __init__(
        self,
        config: AnalyzerConfig,
        detectors: Optional[List[ErrorDetector]] = None
    ):
        self.config = config
        self.detectors = detectors or self._default_detectors()
        self.parser = LogParser(config)
        self.loader = LogLoader(config, self.parser)

        # 存储检测结果
        self._detections: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._instances: Set[str] = set()

    def _default_detectors(self) -> List[ErrorDetector]:
        """默认检测器列表"""
        return [
            TimeoutDetector(),
            GIDErrorDetector(),
            OOMDetector(),
            NCCLErrorDetector(),
            SegfaultDetector(),
            RootCauseDetector(),
            NetworkErrorDetector(),
        ]

    def add_detector(self, detector: ErrorDetector) -> None:
        """添加自定义检测器"""
        self.detectors.append(detector)

    def run_detection(self, entry: LogEntry) -> None:
        """对所有检测器运行检测"""
        for detector in self.detectors:
            try:
                result = detector.detect(entry)
                if result:
                    self._detections[detector.name].append(result)
            except Exception as e:
                logger.error(f"Error in detector {detector.name}: {e}")

    def analyze(self, log_dir: Union[str, Path]) -> AnalysisResult:
        """
        分析日志目录

        Args:
            log_dir: 日志目录路径

        Returns:
            分析结果
        """
        result = AnalysisResult()

        try:
            entries_gen, instances = self.loader.load_logs(log_dir)
            self._instances = instances

            # 流式处理日志
            for entry in entries_gen:
                self.run_detection(entry)

            if not self._instances:
                result.success = True
                result.message = "No log entries to analyze"
                return result

            # 生成报告
            self._generate_report(result)
            result.success = True

        except FileNotFoundError as e:
            result.code = "ERR_LOG_DIR_NOT_FOUND"
            result.message = str(e)
            logger.error(f"Log directory not found: {e}")
        except NotADirectoryError as e:
            result.code = "ERR_NOT_A_DIRECTORY"
            result.message = str(e)
            logger.error(f"Not a directory: {e}")
        except Exception as e:
            result.code = "ERR_ANALYSIS_FAILED"
            result.message = f"Analysis failed: {e}"
            logger.error(f"Analysis failed: {e}", exc_info=True)

        return result

    def _generate_report(self, result: AnalysisResult) -> None:
        """生成分析报告"""
        # 检查是否有任何错误
        has_errors = any(self._detections.values())

        if not has_errors:
            result.message = "No error log found"
            return

        # 分析各种错误
        if "timeout" in self._detections:
            self._analyze_timeout_errors(result)

        if "network_error" in self._detections:
            self._analyze_network_errors(result)

        if "gid_error" in self._detections:
            self._analyze_gid_errors(result)

        if "oom" in self._detections:
            self._analyze_oom_errors(result)

        if "nccl_error" in self._detections:
            self._analyze_nccl_errors(result)

        if "segfault" in self._detections:
            self._analyze_segfault_errors(result)

    def _analyze_timeout_errors(self, result: AnalysisResult) -> None:
        """分析超时错误"""
        timeout_logs = self._detections["timeout"]
        root_causes = self._detections.get("root_cause", [])

        # 按 rank 分组
        timeout_by_rank: Dict[int, List[Dict]] = defaultdict(list)
        for log in timeout_logs:
            timeout_by_rank[log["rank"]].append(log)

        timeout_ranks = set(timeout_by_rank.keys())
        num_timeout_ranks = len(timeout_ranks)

        # 计算期望的总 rank 数
        total_instances = len(self._instances)
        expected_total_ranks = total_instances * self.config.gpus_per_node

        # 找出没有超时的 ranks
        all_possible_ranks = set(range(expected_total_ranks))
        no_timeout_ranks = sorted(all_possible_ranks - timeout_ranks)

        # 找出没有超时的 workers
        no_timeout_workers = self._find_no_timeout_workers(timeout_ranks, expected_total_ranks)

        # 情况1: 所有 rank 都超时 - 静默 hang
        if num_timeout_ranks == expected_total_ranks:
            result.result.append({
                "type": ERROR_DEFS["SILENT_HANG"].code,
                "level": ErrorLevel.CRITICAL.value,
                "suggestion": ERROR_DEFS["SILENT_HANG"].suggestion,
                "status": ErrorStatus.UNRESOLVED.value,
                "details": [{
                    "analysis": f"All {expected_total_ranks} ranks reported timeout. This indicates a silent hang issue.",
                    "recommendation": "Use FlightRecorder for automated hang fault diagnosis",
                    "total_ranks": expected_total_ranks,
                    "timeout_ranks": num_timeout_ranks,
                    "no_timeout_ranks": [],
                    "total_workers": total_instances,
                    "no_timeout_workers": no_timeout_workers,
                }]
            })
            return

        # 情况2: 缺少一个 rank
        if num_timeout_ranks == expected_total_ranks - 1:
            missing_ranks = no_timeout_ranks

            root_cause_details = self._format_root_causes(root_causes)

            result.result.append({
                "type": ERROR_DEFS["TIMEOUT"].code,
                "level": ErrorLevel.HIGH.value,
                "suggestion": (
                    f"Found {expected_total_ranks - 1} out of {expected_total_ranks} ranks with timeout. "
                    f"Missing rank(s): {missing_ranks}. "
                    f"Please check the PyTorch logs for missing rank(s) to find the root cause. "
                    f"If logs show 'NCCL internal Error' or 'NCCL system Error', analyze NCCL logs on the fault node."
                ),
                "status": ErrorStatus.RESOLVED.value,
                "details": [
                    {
                        "analysis": f"{num_timeout_ranks} ranks reported timeout, missing {len(missing_ranks)} rank(s)",
                        "missing_ranks": missing_ranks,
                        "no_timeout_ranks": missing_ranks,
                        "total_ranks": expected_total_ranks,
                        "timeout_ranks": num_timeout_ranks,
                        "total_workers": total_instances,
                        "no_timeout_workers": no_timeout_workers,
                        "next_step": f"Check logs for rank(s) {missing_ranks} to identify the fault cause",
                    },
                    {"root_causes": root_cause_details if root_cause_details else "没有发现故障根因日志，请手工定位"},
                ]
            })
            return

        # 情况3: 其他情况
        root_cause_details = self._format_root_causes(root_causes)

        result.result.append({
            "type": ERROR_DEFS["TIMEOUT"].code,
            "level": ErrorLevel.HIGH.value,
            "suggestion": ERROR_DEFS["TIMEOUT"].suggestion,
            "status": ErrorStatus.UNRESOLVED.value,
            "details": [
                {
                    "analysis": f"{num_timeout_ranks} out of {expected_total_ranks} ranks reported timeout",
                    "total_ranks": expected_total_ranks,
                    "timeout_ranks": num_timeout_ranks,
                    "no_timeout_ranks": no_timeout_ranks,
                    "total_workers": total_instances,
                    "no_timeout_workers": no_timeout_workers,
                },
                {"root_causes": root_cause_details if root_cause_details else "没有发现故障根因日志，请手工定位"},
            ]
        })

    def _find_no_timeout_workers(
        self,
        timeout_ranks: Set[int],
        expected_total_ranks: int
    ) -> List[str]:
        """找出没有超时的 workers"""
        no_timeout_workers: List[str] = []
        instances_list = sorted(self._instances)

        for i, instance in enumerate(instances_list):
            worker_rank_start = i * self.config.gpus_per_node
            worker_rank_end = (i + 1) * self.config.gpus_per_node
            worker_ranks = set(range(worker_rank_start, worker_rank_end))

            # 如果该 worker 有至少一个 rank 没有超时
            if not worker_ranks.issubset(timeout_ranks):
                no_timeout_workers.append(instance)

        return no_timeout_workers

    def _format_root_causes(self, root_causes: List[Dict]) -> List[Dict]:
        """格式化根因信息"""
        # 按 rank 分组
        by_rank: Dict[int, List[Dict]] = defaultdict(list)
        for cause in root_causes:
            by_rank[cause["rank"]].append(cause)

        details = []
        for rank, causes in sorted(by_rank.items()):
            details.append({
                "rank": rank,
                "message": causes[0]["line"],
            })
        return details

    def _analyze_network_errors(self, result: AnalysisResult) -> None:
        """分析网络错误"""
        network_logs = self._detections["network_error"]
        start_workers = {log["instance"] for log in network_logs}
        all_workers = self._instances

        if start_workers != all_workers:
            diff = sorted(all_workers - start_workers)
            result.result.append({
                "type": ERROR_DEFS["NETWORK"].code,
                "level": ErrorLevel.HIGH.value,
                "suggestion": ERROR_DEFS["NETWORK"].suggestion,
                "status": ErrorStatus.UNRESOLVED.value,
                "details": [{
                    "affected_workers": diff,
                    "message": f"Instances {', '.join(diff)} do not have valid log, may be fault",
                }]
            })

    def _analyze_gid_errors(self, result: AnalysisResult) -> None:
        """分析 GID 错误"""
        gid_logs = self._detections["gid_error"]
        affected_hosts = sorted({log["instance"] for log in gid_logs})

        details = []
        for log in gid_logs:
            details.append({
                "worker": log["instance"],
                "message": log["line"],
            })

        result.result.append({
            "type": ERROR_DEFS["GID"].code,
            "level": ErrorLevel.HIGH.value,
            "suggestion": ERROR_DEFS["GID"].suggestion,
            "status": ErrorStatus.UNRESOLVED.value,
            "details": details,
        })

    def _analyze_oom_errors(self, result: AnalysisResult) -> None:
        """分析 OOM 错误"""
        oom_logs = self._detections["oom"]

        details = []
        for log in oom_logs:
            details.append({
                "worker": log["instance"],
                "message": log["line"],
            })

        result.result.append({
            "type": ERROR_DEFS["OOM"].code,
            "level": ErrorLevel.HIGH.value,
            "suggestion": ERROR_DEFS["OOM"].suggestion,
            "status": ErrorStatus.UNRESOLVED.value,
            "details": details,
        })

    def _analyze_nccl_errors(self, result: AnalysisResult) -> None:
        """分析 NCCL 错误"""
        nccl_logs = self._detections["nccl_error"]

        details = []
        for log in nccl_logs:
            details.append({
                "worker": log["instance"],
                "message": log["line"],
            })

        result.result.append({
            "type": ERROR_DEFS["NCCL_ERROR"].code,
            "level": ErrorLevel.HIGH.value,
            "suggestion": ERROR_DEFS["NCCL_ERROR"].suggestion,
            "status": ErrorStatus.UNRESOLVED.value,
            "details": details,
        })

    def _analyze_segfault_errors(self, result: AnalysisResult) -> None:
        """分析段错误"""
        segfault_logs = self._detections["segfault"]

        details = []
        for log in segfault_logs:
            details.append({
                "worker": log["instance"],
                "message": log["line"],
            })

        result.result.append({
            "type": ERROR_DEFS["SEGFAULT"].code,
            "level": ErrorLevel.CRITICAL.value,
            "suggestion": ERROR_DEFS["SEGFAULT"].suggestion,
            "status": ErrorStatus.UNRESOLVED.value,
            "details": details,
        })


# ============================================================================
# 输出格式化
# ============================================================================

def compact_json_arrays(json_str: str) -> str:
    """
    压缩 JSON 中指定的数组字段到一行显示

    适用于 no_timeout_ranks, no_timeout_workers 等数组字段
    """
    patterns = [
        (r'"no_timeout_ranks":\s*\[\s*((?:\d+(?:,\s*)?)*)\s*\]', "numbers"),
        (r'"no_timeout_workers":\s*\[\s*((?:"[^"]*"(?:,\s*)?)*)\s*\]', "strings"),
        (r'"missing_ranks":\s*\[\s*((?:\d+(?:,\s*)?)*)\s*\]', "numbers"),
    ]

    for pattern_str, kind in patterns:
        pattern = re.compile(pattern_str)

        def replace_array(match: re.Match) -> str:
            items_str = match.group(1)
            if not items_str.strip():
                return match.group(0).replace(match.group(1), "").replace("\n", "").replace("  ", " ")

            if kind == "numbers":
                numbers = re.findall(r'\d+', items_str)
                return f'"{match.group(0).split(":")[0].strip()}": [{", ".join(numbers)}]'
            else:
                items = re.findall(r'"([^"]*)"', items_str)
                quoted = [f'"{item}"' for item in items]
                return f'"{match.group(0).split(":")[0].strip()}": [{", ".join(quoted)}]'

        json_str = pattern.sub(replace_array, json_str)

    return json_str


def format_output(
    result: AnalysisResult,
    pretty: bool = False,
    compact_arrays: bool = True
) -> str:
    """格式化输出结果"""
    indent = 2 if pretty else None
    json_output = json.dumps(result.to_dict(), indent=indent, ensure_ascii=False)

    if pretty and compact_arrays:
        json_output = compact_json_arrays(json_output)

    return json_output


# ============================================================================
# CLI 接口
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="BLS Log Analyzer - 分析指定文件夹下的日志文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --log-dir job-20dcpy1vv4h7
  %(prog)s --log-dir /path/to/logs --output result.json
  %(prog)s --log-dir job-20dcpy1vv4h7 --pretty
  %(prog)s --log-dir job-xxx --log-prefix run
  %(prog)s --log-dir job-xxx --config analyzer_config.yaml
  %(prog)s --log-dir job-xxx --verbose
        """
    )

    parser.add_argument(
        '--log-dir',
        required=True,
        help='日志文件夹路径，例如: job-20dcpy1vv4h7'
    )

    parser.add_argument(
        '--output', '-o',
        help='输出结果到指定JSON文件（可选）'
    )

    parser.add_argument(
        '--pretty',
        action='store_true',
        help='以美化格式输出JSON'
    )

    parser.add_argument(
        '--gpus-per-node',
        type=int,
        default=8,
        help='每个节点的GPU数量，默认为8'
    )

    parser.add_argument(
        '--log-prefix',
        default=None,
        help='日志文件前缀，如 "run" 只处理 run.log 文件（可选）'
    )

    parser.add_argument(
        '--config', '-c',
        default=None,
        help='配置文件路径（YAML格式，可选）'
    )

    parser.add_argument(
        '--max-file-size',
        type=int,
        default=100,
        help='最大文件大小限制（MB），默认为100MB'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='增加日志详细程度，-v 为 INFO，-vv 为 DEBUG'
    )

    parser.add_argument(
        '--log-file',
        default=None,
        help='日志文件路径（可选）'
    )

    return parser


def setup_verbosity(verbosity: int, log_file: Optional[str] = None) -> None:
    """根据详细程度设置日志级别"""
    global logger
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    # 移除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    logger = setup_logging(level, log_file)


def main() -> int:
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 设置日志级别
    setup_verbosity(args.verbose, args.log_file)

    try:
        # 加载配置
        if args.config:
            config = AnalyzerConfig.from_yaml(args.config)
            # 命令行参数覆盖配置文件
            if args.gpus_per_node != 8:
                config.gpus_per_node = args.gpus_per_node
            if args.log_prefix:
                config.log_prefix = args.log_prefix
            if args.max_file_size != 100:
                config.max_file_size_mb = args.max_file_size
        else:
            config = AnalyzerConfig(
                gpus_per_node=args.gpus_per_node,
                log_prefix=args.log_prefix,
                max_file_size_mb=args.max_file_size,
            )

        logger.info(f"Starting analysis with config: gpus_per_node={config.gpus_per_node}")
        logger.debug(f"Log directory: {args.log_dir}")

        # 创建分析引擎并运行
        engine = AnalysisEngine(config)
        result = engine.analyze(args.log_dir)

        # 格式化输出
        json_output = format_output(result, pretty=args.pretty)

        # 输出到文件或标准输出
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            logger.info(f"Results saved to: {args.output}")
        else:
            print(json_output)

        return 0 if result.success else 1

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        error_result = AnalysisResult(
            success=False,
            code="ERR_UNEXPECTED",
            message=str(e),
        )
        print(json.dumps(error_result.to_dict(), indent=2, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
