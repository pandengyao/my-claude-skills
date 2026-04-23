#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 状态流转规划脚本

一次性完成卡片状态流转的全流程规划，包括：
- 查询卡片当前状态
- 计算流转路径
- 检测最终状态必填字段
- 生成可执行命令

使用示例:
    python scripts/plan_transition.py --space edc-scrum --id 352568 --to "已修复"
    python scripts/plan_transition.py --space edc-scrum --id 352568 --to "已修复" --format json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any

# 将父目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.query import get_card
from icafe_skill.update import detect_required_fields
from icafe_skill.exceptions import ResourceNotFoundError
from scripts.check_workflow import WorkflowConfig


@dataclass
class TransitionPlan:
    """状态流转规划结果"""
    success: bool
    card: Dict[str, Any]
    transition: Dict[str, Any]
    required_fields: List[Dict[str, Any]]
    recommended_fields: Dict[str, str]
    can_execute: bool
    confidence: float
    commands: List[str]
    warnings: List[str] = field(default_factory=list)
    status_field_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，优化输出结构便于 Claude 识别交互流程"""
        result = asdict(self)
        # 移除冗余字段，避免 JSON 输出过于冗长
        result.pop('required_fields', None)
        result.pop('status_field_details', None)

        # 收集所有需要确认的字段（包括 needs_fill=True 和 comment）
        fields_to_confirm = []
        confirmed_fields = {}  # 用于跟踪已确认的字段值
        additional_warnings = []  # 额外的警告信息

        for status, details in self.status_field_details.items():
            # 跳过有错误的状态
            if "error" in details:
                additional_warnings.append(f"状态 '{status}' 检测失败: {details['error']}")
                continue

            for field in details.get('field_details', []):
                if field.get('needs_fill'):
                    field_info = {
                        "status": status,
                        "field_name": field['field_name'],
                        "field_type": field.get('field_type', 'string'),
                        "current_value": field.get('current_value'),
                        "suggested_value": field.get('suggested_value', ''),
                        "options": field.get('options', []),
                        "required": True
                    }
                    fields_to_confirm.append(field_info)
                    # 记录确认后的字段值
                    confirmed_fields[f"{status}:{field['field_name']}"] = field.get('suggested_value', '')

            # 关闭卡片时，comment 字段为必填，需单独处理
            if status == "已关闭":
                # 从推荐字段中获取 Bug分析结论 来推断 comment
                bug_conclusion = details.get('recommended_fields', {}).get("Bug分析结论", "")
                if bug_conclusion == "非Bug":
                    comment_value = "非Bug关闭"
                elif bug_conclusion:
                    comment_value = f"问题分析：{bug_conclusion}"
                else:
                    comment_value = "关闭卡片"

                comment_info = {
                    "status": status,
                    "field_name": "评论",
                    "field_type": "text",
                    "current_value": "",
                    "suggested_value": comment_value,
                    "options": [],
                    "required": True,
                    "description": "关闭卡片时的评论内容"
                }
                fields_to_confirm.append(comment_info)
                confirmed_fields[f"{status}:评论"] = comment_value

        has_fields_to_confirm = len(fields_to_confirm) > 0

        # 重新生成命令，确保字段值与 fields_to_confirm 一致
        commands_with_values = []
        if self.transition.get('path') and len(self.transition['path']) > 1:
            for i, to_status in enumerate(self.transition['path'][1:], start=1):
                status_details = self.status_field_details.get(to_status, {})
                status_recommended = status_details.get('recommended_fields', {})

                # 构建 command 对象，包含命令和字段值
                cmd_parts = [
                    "python scripts/update_card.py",
                    f"--space {self.card.get('space_id', '')}",
                    f"--id {self.card.get('card_id', '')}",
                    f"--status {to_status}"
                ]

                # 添加字段参数
                field_values = {}
                for field_name, field_value in status_recommended.items():
                    cmd_parts.append(f"--field {field_name} {field_value}")
                    field_values[field_name] = field_value

                # 添加评论参数（关闭卡片时）
                if to_status == "已关闭":
                    comment_key = f"{to_status}:评论"
                    comment_value = confirmed_fields.get(comment_key, "关闭卡片")
                    cmd_parts.append(f'--comment "{comment_value}"')
                    field_values["评论"] = comment_value

                cmd_parts.append("--execute")

                commands_with_values.append({
                    "status": to_status,
                    "command": " ".join(cmd_parts),
                    "field_values": field_values,
                    "step": i
                })

        # 简化 instruction，只保留关键信息
        if has_fields_to_confirm:
            instruction = {
                "action": "confirm_fields_then_execute",
                "message": "使用 AskUserQuestion 工具按目标状态分组展示所有需要确认的字段，让用户确认或修改，然后按顺序执行命令",
                "total_fields": len(fields_to_confirm),
                "total_commands": len(commands_with_values)
            }
        else:
            instruction = {
                "action": "execute_directly",
                "message": "所有必填字段已满足，直接按顺序执行命令",
                "total_commands": len(commands_with_values)
            }

        # 重新组织输出结构，合并额外的警告信息
        merged_warnings = self.warnings + additional_warnings
        ordered_result = {
            "_instruction": instruction,
            "needs_user_confirm": has_fields_to_confirm,
            "card": self.card,
            "transition": self.transition,
            "fields_to_confirm": fields_to_confirm,
            "commands": commands_with_values,
            "success": self.success,
            "can_execute": self.can_execute,
            "confidence": self.confidence,
            "warnings": merged_warnings,
        }
        return ordered_result

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


def generate_update_command(
    space_id: str,
    card_id: str,
    target_status: str,
    fields: Dict[str, str],
    comment: Optional[str] = None
) -> str:
    """
    生成 update_card.py 命令。

    Args:
        space_id: 空间 ID
        card_id: 卡片 ID
        target_status: 目标状态
        fields: 要填写的字段
        comment: 评论内容（关闭卡片时必填）

    Returns:
        可执行的命令字符串
    """
    parts = [
        "python scripts/update_card.py",
        f"--space {space_id}",
        f"--id {card_id}",
        f"--status {target_status}"
    ]

    for field_name, field_value in fields.items():
        parts.append(f"--field {field_name} {field_value}")

    # 添加评论参数（关闭卡片时必填）
    if comment:
        parts.append(f"--comment \"{comment}\"")

    parts.append("--execute")

    return " ".join(parts)


def plan_transition(
    space_id: str,
    card_id: str,
    target_status: str,
    config_path: Optional[str] = None,
    client: Optional[Any] = None,
    max_sample_cards: int = 3
) -> TransitionPlan:
    """
    规划卡片状态流转。

    Args:
        space_id: 空间 ID
        card_id: 卡片 ID
        target_status: 目标状态
        config_path: 配置文件路径（可选）
        client: 已认证的 iCafe 客户端（可选，如不提供会自动创建）
        max_sample_cards: 查询的样本卡片最大数量（默认: 3）

    Returns:
        TransitionPlan 对象，包含流转规划结果
    """
    warnings: List[str] = []

    # 获取配置文件路径
    if config_path is None:
        script_dir = Path(__file__).parent.parent
        config_path = str(script_dir / "config" / "config.yaml")

    # 初始化客户端（如果未提供）
    if client is None:
        try:
            client = init_client(config_file=config_path)
        except AuthenticationError as e:
            return TransitionPlan(
                success=False,
                card={},
                transition={},
                required_fields=[],
                recommended_fields={},
                can_execute=False,
                confidence=0.0,
                commands=[],
                warnings=[f"认证失败: {e}"]
            )

    # 1. 获取卡片信息
    try:
        card = get_card(client, space_id, card_id)
    except ResourceNotFoundError:
        return TransitionPlan(
            success=False,
            card={},
            transition={},
            required_fields=[],
            recommended_fields={},
            can_execute=False,
            confidence=0.0,
            commands=[],
            warnings=[f"卡片不存在: space_id={space_id}, card_id={card_id}"]
        )
    except ICafeError as e:
        return TransitionPlan(
            success=False,
            card={},
            transition={},
            required_fields=[],
            recommended_fields={},
            can_execute=False,
            confidence=0.0,
            commands=[],
            warnings=[f"获取卡片失败: {e}"]
        )

    current_status = card.status or ""
    issue_type = card.type or ""

    # 构建卡片信息字典
    card_info = {
        "space_id": space_id,
        "card_id": card_id,
        "current_status": current_status,
        "issue_type": issue_type,
        "title": card.title or ""
    }

    # 2. 获取流转路径
    try:
        workflow = WorkflowConfig(config_path=config_path, issue_type=issue_type)
        path = workflow.get_transition_path(current_status, target_status)
    except Exception as e:
        return TransitionPlan(
            success=False,
            card=card_info,
            transition={},
            required_fields=[],
            recommended_fields={},
            can_execute=False,
            confidence=0.0,
            commands=[],
            warnings=[f"获取工作流配置失败: {e}"]
        )

    if path is None:
        return TransitionPlan(
            success=False,
            card=card_info,
            transition={},
            required_fields=[],
            recommended_fields={},
            can_execute=False,
            confidence=0.0,
            commands=[],
            warnings=[f"无法从 '{current_status}' 流转到 '{target_status}'"]
        )

    transition_info = {
        "target_status": target_status,
        "path": path,
        "total_steps": len(path) - 1  # 步骤数 = 节点数 - 1
    }

    # 3. 循环检测每个状态的推荐字段
    all_recommended_fields: Dict[str, str] = {}
    all_required_fields: List[Dict[str, Any]] = []
    status_field_details: Dict[str, Dict[str, Any]] = {}
    all_warnings: List[str] = []
    total_confidence = 0.0
    confidence_count = 0

    # 遍历流转路径中的每个目标状态（跳过当前状态）
    for i, to_status in enumerate(path[1:], start=1):
        # 添加 1 秒延迟，避免 API 调用过快
        if i > 1:
            time.sleep(1)

        try:
            detect_result = detect_required_fields(
                client,
                space_id,
                card_id,
                to_status,
                max_sample_cards=max_sample_cards
            )

            # 收集此状态的字段详情
            # 提取 field_details 用于用户确认
            field_details = []
            for f in detect_result.required_fields:
                field_dict = f.__dict__ if hasattr(f, '__dict__') else f
                field_details.append({
                    "field_name": field_dict.get("field_name") or field_dict.get("field_display", ""),
                    "field_type": field_dict.get("field_type", "string"),
                    "current_value": field_dict.get("current_value"),
                    "suggested_value": field_dict.get("suggestion", ""),
                    "options": field_dict.get("options", []),
                    "needs_fill": field_dict.get("needs_fill", False),
                    "reason": field_dict.get("reason", "")
                })

            status_field_details[to_status] = {
                "recommended_fields": detect_result.recommended_fields,
                "can_transition": detect_result.can_transition,
                "confidence": detect_result.confidence,
                "sample_card_count": detect_result.sample_card_count,
                "step": i,
                "field_details": field_details
            }

            # 合并推荐字段（去重：相同字段名取第一个出现的值）
            for field_name, field_value in detect_result.recommended_fields.items():
                if field_name not in all_recommended_fields:
                    all_recommended_fields[field_name] = field_value

            # 收集必填字段信息（去重）
            for field in detect_result.required_fields:
                field_dict = field.__dict__ if hasattr(field, '__dict__') else field
                field_name = field_dict.get("field_name", field_dict.get("field_display", ""))
                # 检查是否已存在相同字段
                existing = False
                for existing_field in all_required_fields:
                    if existing_field.get("field_name") == field_name or existing_field.get("field_display") == field_name:
                        existing = True
                        break
                if not existing:
                    all_required_fields.append(field_dict)

            all_warnings.extend(detect_result.warnings)
            total_confidence += detect_result.confidence
            confidence_count += 1

        except Exception as e:
            all_warnings.append(f"检测状态 '{to_status}' 的必填字段失败: {e}")
            status_field_details[to_status] = {
                "error": str(e),
                "step": i
            }

    # 计算平均置信度
    avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0.0

    # 判断是否可以执行（所有字段都已填写）
    fields_needing_fill = [f for f in all_required_fields if f.get("needs_fill", False)]
    can_execute = len(fields_needing_fill) == 0

    # 4. 生成命令
    # 每个状态设置各自的推荐字段
    commands = []
    if path and len(path) > 1:
        for i, to_status in enumerate(path[1:], start=1):
            # 获取此状态的推荐字段
            status_details = status_field_details.get(to_status, {})
            status_recommended = status_details.get("recommended_fields", {})

            # 关闭卡片时，comment 字段为必填但无法自动检测，需手动添加
            comment = None
            if to_status == "已关闭":
                # 从 Bug分析结论 推断默认评论内容
                bug_conclusion = status_recommended.get("Bug分析结论", "")
                if bug_conclusion == "非Bug":
                    comment = "非Bug关闭"
                elif bug_conclusion:
                    comment = f"问题分析：{bug_conclusion}"
                else:
                    comment = "关闭卡片"

            cmd = generate_update_command(
                space_id=space_id,
                card_id=card_id,
                target_status=to_status,
                fields=status_recommended,
                comment=comment
            )
            commands.append(cmd)

    return TransitionPlan(
        success=True,
        card=card_info,
        transition=transition_info,
        required_fields=all_required_fields,
        recommended_fields=all_recommended_fields,
        can_execute=can_execute,
        confidence=avg_confidence,
        commands=commands,
        warnings=all_warnings,
        status_field_details=status_field_details
    )


def main():
    parser = argparse.ArgumentParser(
        description='规划 iCafe 卡片状态流转',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --space my-space --id 123 --to "已修复"
  %(prog)s --space my-space --id 123 --to "已修复" --format json

注意:
  此脚本需要有效的配置文件（默认: config/config.yaml）。
        """
    )
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--id', '-i', required=True, help='卡片 ID')
    parser.add_argument('--to', '-t', required=True, dest='target_status',
                        help='目标状态')
    parser.add_argument('--config', '-c', help='配置文件路径（默认: config/config.yaml）')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='json',
                        help='输出格式 (默认: json)')
    parser.add_argument('--max-samples', type=int, default=3,
                        help='查询的样本卡片最大数量 (默认: 3)')

    args = parser.parse_args()

    # 执行规划
    plan = plan_transition(
        space_id=args.space,
        card_id=args.id,
        target_status=args.target_status,
        config_path=args.config,
        max_sample_cards=args.max_samples
    )

    # 输出结果
    if args.format == 'json':
        print(plan.to_json())
    else:
        print(f"\n{'='*60}")
        print("状态流转规划结果")
        print(f"{'='*60}")

        if plan.success:
            print(f"卡片: {plan.card.get('title', 'N/A')}")
            print(f"当前状态: {plan.card.get('current_status', 'N/A')}")
            print(f"目标状态: {plan.transition.get('target_status', 'N/A')}")
            print(f"流转路径: {' -> '.join(plan.transition.get('path', []))}")
            print(f"总步骤数: {plan.transition.get('total_steps', 0)}")
            print(f"可执行: {'是' if plan.can_execute else '否'}")
            print(f"置信度: {plan.confidence:.0%}")

            # 展示每个状态的字段详情
            if plan.status_field_details:
                print(f"\n各状态字段详情:")
                for status, details in plan.status_field_details.items():
                    print(f"\n  [{status}]")
                    if "error" in details:
                        print(f"    错误: {details['error']}")
                    else:
                        print(f"    置信度: {details.get('confidence', 0):.0%}")
                        print(f"    样本数: {details.get('sample_card_count', 0)}")
                        if details.get('recommended_fields'):
                            print(f"    推荐字段:")
                            for k, v in details['recommended_fields'].items():
                                print(f"      - {k}: {v}")

            if plan.recommended_fields:
                print(f"\n汇总推荐字段值 (去重后):")
                for k, v in plan.recommended_fields.items():
                    print(f"  - {k}: {v}")

            if plan.commands:
                print(f"\n执行命令:")
                for cmd in plan.commands:
                    print(f"  {cmd}")

            if plan.warnings:
                print(f"\n警告:")
                for w in plan.warnings:
                    print(f"  - {w}")
        else:
            print("规划失败")
            for w in plan.warnings:
                print(f"  - {w}")

        print(f"{'='*60}\n")

    return 0 if plan.success else 1


if __name__ == '__main__':
    sys.exit(main())
