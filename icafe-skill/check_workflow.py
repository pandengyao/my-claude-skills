#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 工作流状态验证脚本

用于验证状态转换规则，检查当前状态是否可以流转到目标状态，
以及显示当前状态可流转的所有下个状态。

使用示例:
    # 验证状态转换
    python scripts/check_workflow.py --from "新建" --to "已分配"

    # 查看当前状态可流转的所有下个状态
    python scripts/check_workflow.py --from "新建"

    # 列出所有状态节点
    python scripts/check_workflow.py --list-nodes

    # 显示完整的工作流规则
    python scripts/check_workflow.py --show-rules

    # 使用 JSON 格式输出
    python scripts/check_workflow.py --from "新建" --to "已分配" --format json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class WorkflowConfig:
    """工作流配置管理类"""

    def __init__(self, config_path: str | None = None, issue_type: str | None = None):
        """
        初始化工作流配置

        Args:
            config_path: 配置文件路径（默认: 相对于脚本所在目录的 config/config.yaml）
            issue_type: 卡片类型，默认使用配置中的 default_issue_type
        """
        # 默认配置路径基于脚本所在目录
        script_dir = Path(__file__).parent.parent
        default_config = script_dir / "config" / "config.yaml"
        self.config_path = config_path if config_path else str(default_config)
        self.config: dict = self._load_config()
        self.workflow: dict = self._get_workflow_config()

        # 获取 issue_type（参数优先，其次从配置读取）
        if not issue_type:
            issue_type = str(self.workflow.get("default_issue_type", "Bug"))
        self.issue_type = issue_type
        self.type_config = self._get_type_config()

    def _load_config(self) -> dict[str, object]:
        """加载配置文件"""
        from icafe_skill.auth import load_config_file
        try:
            return load_config_file(self.config_path)
        except Exception as e:
            print(f"错误: 无法加载配置文件 {self.config_path}: {e}", file=sys.stderr)
            sys.exit(1)

    def _get_workflow_config(self) -> dict[str, object]:
        """获取工作流配置"""
        workflow = self.config.get("workflow")
        if not isinstance(workflow, dict):
            print("错误: 配置文件中未找到 workflow 字段", file=sys.stderr)
            sys.exit(1)
        return workflow

    def _get_type_config(self) -> dict[str, object]:
        """获取指定 issue_type 的工作流配置"""
        issue_types_dict = self.workflow.get("issue_types")
        if not isinstance(issue_types_dict, dict):
            print("错误: workflow 配置中未找到 issue_types 字段", file=sys.stderr)
            sys.exit(1)

        type_config = issue_types_dict.get(self.issue_type)
        if not isinstance(type_config, dict):
            available_types = ", ".join(issue_types_dict.keys())
            print(f"错误: 未找到卡片类型 '{self.issue_type}' 的配置", file=sys.stderr)
            if available_types:
                print(f"可用的卡片类型: {available_types}", file=sys.stderr)
            else:
                print("配置文件中未找到任何 issue_types 配置", file=sys.stderr)
            sys.exit(1)

        return type_config

    @property
    def space(self) -> str:
        """获取工作流所属空间"""
        return str(self.workflow.get("space", ""))

    @property
    def available_issue_types(self) -> list[str]:
        """获取所有配置的 issue_type"""
        issue_types = self.workflow.get("issue_types")
        if isinstance(issue_types, dict):
            return list(issue_types.keys())
        return []

    @property
    def status_nodes(self) -> list[str]:
        """获取当前 issue_type 的所有状态节点"""
        nodes = self.type_config.get("status_nodes")
        if isinstance(nodes, list):
            return [str(n) for n in nodes]
        return []

    @property
    def transition_rules(self) -> dict[str, list[str]]:
        """获取当前 issue_type 的状态流转规则"""
        rules = self.type_config.get("transition_rules")
        if isinstance(rules, dict):
            return {str(k): [str(v) for v in vals] if isinstance(vals, list) else []
                    for k, vals in rules.items()}
        return {}

    @property
    def transition_features(self) -> list[str]:
        """获取当前 issue_type 的流转特性说明"""
        features = self.type_config.get("transition_features")
        if isinstance(features, list):
            return [str(f) for f in features]
        return []

    def get_next_states(self, current_status: str) -> list[str]:
        """
        获取当前状态可流转的所有下个状态

        Args:
            current_status: 当前状态

        Returns:
            可流转的状态列表（不包含自身回环）
        """
        return self.transition_rules.get(current_status, [])

    def get_all_allowed_transitions(self, current_status: str) -> list[str]:
        """
        获取当前状态所有允许的流转（包含自身回环）

        Args:
            current_status: 当前状态

        Returns:
            允许流转的状态列表（包含自身）
        """
        next_states = self.get_next_states(current_status)
        if current_status in next_states:
            return next_states
        # 根据配置说明，所有状态支持自身回环操作
        return [current_status] + next_states

    def is_valid_transition(self, current_status: str, target_status: str) -> bool:
        """
        验证状态转换是否合法

        Args:
            current_status: 当前状态
            target_status: 目标状态

        Returns:
            True 表示可以转换，False 表示不可以
        """
        return target_status in self.get_all_allowed_transitions(current_status)

    def validate_status(self, status: str) -> bool:
        """
        验证状态是否存在于工作流中

        Args:
            status: 状态名称

        Returns:
            True 表示状态存在，False 表示不存在
        """
        return status in self.status_nodes

    def get_transition_path(self, from_status: str, to_status: str) -> list[str] | None:
        """
        查找从起始状态到目标状态的最短路径（如果需要多步流转）

        Args:
            from_status: 起始状态
            to_status: 目标状态

        Returns:
            状态路径列表（包含起始和目标状态），如果无法到达则返回 None
        """
        if not self.validate_status(from_status) or not self.validate_status(to_status):
            return None

        if from_status == to_status:
            return [from_status]

        # BFS 寻找最短路径
        from collections import deque
        visited: set[str] = set()
        queue = deque([(from_status, [from_status])])

        while queue:
            current, path = queue.popleft()
            if current == to_status:
                return path

            if current in visited:
                continue
            visited.add(current)

            for next_state in self.get_next_states(current):
                if next_state not in visited:
                    queue.append((next_state, path + [next_state]))

        return None


def print_status_nodes(workflow: WorkflowConfig, format_type: str = 'text'):
    """打印所有状态节点"""
    nodes = workflow.status_nodes
    if format_type == 'json':
        print(json.dumps({"status_nodes": nodes}, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"工作流状态节点 (共 {len(nodes)} 个)")
        print(f"{'='*60}")
        for i, node in enumerate(nodes, 1):
            print(f"  {i}. {node}")
        print(f"{'='*60}\n")


def print_transition_rules(workflow: WorkflowConfig, format_type: str = 'text'):
    """打印流转规则"""
    rules = workflow.transition_rules
    if format_type == 'json':
        print(json.dumps({"transition_rules": rules}, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("状态流转规则")
        print(f"{'='*60}")
        for from_status, to_statuses in rules.items():
            print(f"\n{from_status} -> {', '.join(to_statuses)}")
        print(f"\n{'='*60}\n")


def print_transition_features(workflow: WorkflowConfig):
    """打印流转特性说明"""
    features = workflow.transition_features
    print(f"\n{'='*60}")
    print("流转特性说明")
    print(f"{'='*60}")
    for feature in features:
        print(f"  - {feature}")
    print(f"{'='*60}\n")


def check_transition(workflow: WorkflowConfig, current: str, target: str, format_type: str = 'text'):
    """检查状态转换"""
    # 验证状态是否存在
    if not workflow.validate_status(current):
        if format_type == 'json':
            print(json.dumps({
                "valid": False,
                "error": f"起始状态 '{current}' 不存在于工作流中"
            }, indent=2, ensure_ascii=False))
        else:
            print(f"错误: 起始状态 '{current}' 不存在于工作流中")
        return

    if target and not workflow.validate_status(target):
        if format_type == 'json':
            print(json.dumps({
                "valid": False,
                "error": f"目标状态 '{target}' 不存在于工作流中"
            }, indent=2, ensure_ascii=False))
        else:
            print(f"错误: 目标状态 '{target}' 不存在于工作流中")
        return

    # 获取可流转的状态
    next_states = workflow.get_next_states(current)
    all_allowed = workflow.get_all_allowed_transitions(current)

    if target:
        # 验证特定转换
        is_valid = workflow.is_valid_transition(current, target)

        if format_type == 'json':
            result = {
                "from_status": current,
                "to_status": target,
                "valid": is_valid,
                "available_transitions": all_allowed
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print("状态转换验证")
            print(f"{'='*60}")
            print(f"当前状态: {current}")
            print(f"目标状态: {target}")
            print(f"\n转换结果: {'✓ 允许' if is_valid else '✗ 不允许'}")

            if not is_valid:
                print(f"\n当前状态可流转到: {', '.join(all_allowed)}")
                path = workflow.get_transition_path(current, target)
                if path and len(path) > 1:
                    print(f"\n建议流转路径: {' -> '.join(path)}")
            print(f"{'='*60}\n")
    else:
        # 显示所有可流转的状态
        if format_type == 'json':
            result = {
                "current_status": current,
                "available_transitions": all_allowed
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print(f"当前状态: {current}")
            print(f"{'='*60}")
            print(f"\n可流转的状态 (共 {len(all_allowed)} 个):")
            for i, state in enumerate(all_allowed, 1):
                mark = " (当前状态)" if state == current else ""
                print(f"  {i}. {state}{mark}")
            print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='验证 iCafe 卡片工作流状态转换',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 验证 Bug 类型的状态转换
  %(prog)s --type Bug --from "新建" --to "已分配"

  # 查看 Story 类型的可流转状态（需先在配置文件中添加 Story 配置）
  %(prog)s --type Story --from "新建"

  # 列出所有状态节点
  %(prog)s --list-nodes

  # 显示完整的工作流规则
  %(prog)s --show-rules

  # 列出所有可用的卡片类型
  %(prog)s --list-types

  # 使用 JSON 格式输出
  %(prog)s --from "新建" --to "已分配" --format json
        """
    )
    parser.add_argument('--from', '-f', dest='from_status', help='当前状态')
    parser.add_argument('--to', '-t', dest='to_status', help='目标状态')
    parser.add_argument('--list-nodes', '-l', action='store_true',
                        help='列出当前卡片类型的所有状态节点')
    parser.add_argument('--list-types', action='store_true',
                        help='列出所有配置的卡片类型')
    parser.add_argument('--show-rules', '-r', action='store_true',
                        help='显示当前卡片类型的完整状态流转规则')
    parser.add_argument('--show-features', action='store_true',
                        help='显示当前卡片类型的流转特性说明')
    parser.add_argument('--format', action='store', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    parser.add_argument('--type', '-T', dest='issue_type',
                        help='卡片类型，如 Bug、Story 等（默认: 配置中的 default_issue_type）')
    parser.add_argument('--config', '-c', help='配置文件路径（默认: config/config.yaml）')

    args = parser.parse_args()

    # 加载工作流配置
    workflow = WorkflowConfig(config_path=args.config, issue_type=args.issue_type)

    # 显示空间和卡片类型信息
    if args.format == 'text':
        print(f"工作流空间: {workflow.space}")
        print(f"卡片类型: {workflow.issue_type}")

    # 执行相应操作
    if args.list_types:
        if args.format == 'json':
            print(json.dumps({"issue_types": workflow.available_issue_types},
                            indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print(f"配置的卡片类型 (共 {len(workflow.available_issue_types)} 个)")
            print(f"{'='*60}")
            for i, t in enumerate(workflow.available_issue_types, 1):
                mark = " (默认)" if t == workflow.workflow.get("default_issue_type") else ""
                print(f"  {i}. {t}{mark}")
            print(f"{'='*60}\n")
    elif args.list_nodes:
        print_status_nodes(workflow, args.format)
    elif args.show_rules:
        print_transition_rules(workflow, args.format)
        if args.format == 'text':
            print_transition_features(workflow)
    elif args.show_features:
        if args.format == 'text':
            print_transition_features(workflow)
        else:
            print(json.dumps({"transition_features": workflow.transition_features},
                            indent=2, ensure_ascii=False))
    elif args.from_status:
        check_transition(workflow, args.from_status, args.to_status, args.format)
    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
