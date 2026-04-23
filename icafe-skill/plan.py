#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 计划操作脚本

独立可执行的计划操作工具，支持命令行参数。

使用示例:
    # 列出所有计划
    python scripts/plan.py --space edc-scrum --list
    python scripts/plan.py --space edc-scrum --list --with-milestones

    # 查询单个计划
    python scripts/plan.py --space edc-scrum --query "Q1 2024 Plan"
    python scripts/plan.py --space edc-scrum --query "Q1 2024 Plan" --with-milestones

    # 创建新计划
    python scripts/plan.py --space edc-scrum --create \
        --name "Q2 2024 Plan" \
        --desc "Second quarter plan" \
        --start "2024-04-01" \
        --end "2024-06-30" \
        --stick

    # 更新计划时间
    python scripts/plan.py --space edc-scrum --update-date \
        --id 12345 \
        --start "2024-04-15" \
        --end "2024-07-15"
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import (
    init_client, ICafeError, AuthenticationError, ValidationError,
    get_plan, create_plan, update_plan_date, get_plans, get_plans_with_milestones,
    validate_date_format
)


def print_plan_info(plan, format_type='text'):
    """打印单个计划信息"""
    if format_type == 'json':
        output = plan.to_dict()
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"计划信息: {plan.name}")
        print(f"{'='*60}")
        print(f"计划 ID: {plan.plan_id}")
        print(f"名称: {plan.name}")
        print(f"状态: {plan.status or '未设置'}")
        print(f"描述: {plan.description or '无'}")
        print(f"开始日期: {plan.start_date or '未设置'}")
        print(f"结束日期: {plan.end_date or '未设置'}")
        if plan.is_milestone:
            print(f"类型: 里程碑")
        if plan.parent_plan_id:
            print(f"父计划 ID: {plan.parent_plan_id}")
        print(f"空间 ID: {plan.space_id}")

        # 显示子计划
        if plan.children:
            print(f"\n子计划 ({len(plan.children)}个):")
            for child in plan.children:
                print(f"  - {child.get('path')}: {child.get('status')}")

        print(f"{'='*60}\n")


def print_plans_list(plans, format_type='text'):
    """打印计划列表信息"""
    if format_type == 'json':
        output = [plan.to_dict() for plan in plans]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"计划列表 (共 {len(plans)} 条)")
        print(f"{'='*60}\n")

        for i, plan in enumerate(plans, 1):
            plan_type = "里程碑" if plan.is_milestone else "计划"
            print(f"{i:3d}. [{plan.plan_id}] {plan.name} ({plan_type})")
            print(f"     日期: {plan.start_date or '未设置'} ~ {plan.end_date or '未设置'}")
            if plan.description:
                desc_preview = plan.description[:60] + '...' if len(plan.description) > 60 else plan.description
                print(f"     描述: {desc_preview}")
            print()

        print(f"{'='*60}\n")


def print_update_result(result, format_type='text'):
    """打印更新结果"""
    if format_type == 'json':
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("计划时间更新成功")
        print(f"{'='*60}")
        for key, value in result.items():
            print(f"{key}: {value}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='iCafe 计划操作工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有计划
  %(prog)s --space edc-scrum --list
  %(prog)s --space edc-scrum --list --with-milestones
  %(prog)s --space edc-scrum --list --format json

  # 查询单个计划
  %(prog)s --space edc-scrum --query "Q1 2024 Plan"
  %(prog)s --space edc-scrum --query "Q1 2024 Plan" --format json

  # 创建新计划
  %(prog)s --space edc-scrum --create --name "Q2 2024 Plan" \
      --desc "Second quarter plan" --start "2024-04-01" --end "2024-06-30"
  %(prog)s --space edc-scrum --create --name "Q2 2024 Plan" \
      --desc "Second quarter plan" --start "2024-04-01" --end "2024-06-30" \
      --parent "Q1 2024 Plan" --stick

  # 更新计划时间
  %(prog)s --space edc-scrum --update-date --id 12345 \
      --start "2024-04-15" --end "2024-07-15"

操作说明:
  --list              列出所有计划
  --query             查询单个计划（需要提供计划名称）
  --create            创建新计划（需要提供 --name, --desc, --start, --end）
  --update-date       更新计划时间（需要提供 --id, --start, --end）
  --with-milestones   同时获取里程碑信息（仅用于 --list 或 --query）
  --stick             置顶计划（仅用于 --create）
        """
    )

    # 通用参数
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    # 操作模式参数
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--list', '-l', action='store_true', help='列出所有计划')
    mode_group.add_argument('--query', '-q', help='查询单个计划名称')
    mode_group.add_argument('--create', '-c', action='store_true', help='创建新计划')
    mode_group.add_argument('--update-date', action='store_true', help='更新计划时间')

    # 创建计划参数
    parser.add_argument('--name', '-n', help='计划名称（用于 --create）')
    parser.add_argument('--desc', '-d', help='计划描述（用于 --create）')
    parser.add_argument('--start', help='开始日期 YYYY-MM-DD（用于 --create 或 --update-date）')
    parser.add_argument('--end', help='结束日期 YYYY-MM-DD（用于 --create 或 --update-date）')
    parser.add_argument('--parent', help='父计划名称（用于 --create，可选）')
    parser.add_argument('--stick', action='store_true', help='置顶计划（用于 --create，可选）')

    # 更新计划时间参数
    parser.add_argument('--id', '-i', help='计划 ID（用于 --update-date）')

    # 附加选项
    parser.add_argument('--with-milestones', '-m', action='store_true',
                        help='同时获取里程碑信息（用于 --list 或 --query）')

    args = parser.parse_args()

    try:
        # 初始化客户端（使用配置文件，相对路径基于脚本所在目录）
        script_dir = Path(__file__).parent.parent
        default_config_path = script_dir / "config" / "config.yaml"
        config_path = args.config if args.config else str(default_config_path)
        client = init_client(config_file=config_path)

        if args.list:
            # 列出所有计划
            if args.with_milestones:
                plans = get_plans_with_milestones(client, space_id=args.space)
            else:
                plans = get_plans(client, space_id=args.space)
            print_plans_list(plans, args.format)

        elif args.query:
            # 查询单个计划
            plan = get_plan(client, space_id=args.space, plan_name=args.query)
            print_plan_info(plan, args.format)

        elif args.create:
            # 创建新计划
            # 验证必需参数
            if not args.name:
                print("错误: --name 参数是创建计划所必需的", file=sys.stderr)
                return 1
            if not args.start:
                print("错误: --start 参数是创建计划所必需的", file=sys.stderr)
                return 1
            if not args.end:
                print("错误: --end 参数是创建计划所必需的", file=sys.stderr)
                return 1

            # 验证日期格式
            try:
                validate_date_format(args.start)
                validate_date_format(args.end)
            except ValidationError as e:
                print(f"日期格式错误: {e}", file=sys.stderr)
                return 1

            plan = create_plan(
                client,
                space_id=args.space,
                name=args.name,
                desc=args.desc or "",
                start_date=args.start,
                end_date=args.end,
                parent=args.parent,
                stick="true" if args.stick else None
            )
            print_plan_info(plan, args.format)

        elif args.update_date:
            # 更新计划时间
            # 验证必需参数
            if not args.id:
                print("错误: --id 参数是更新计划时间所必需的", file=sys.stderr)
                return 1
            if not args.start:
                print("错误: --start 参数是更新计划时间所必需的", file=sys.stderr)
                return 1
            if not args.end:
                print("错误: --end 参数是更新计划时间所必需的", file=sys.stderr)
                return 1

            # 验证日期格式
            try:
                validate_date_format(args.start)
                validate_date_format(args.end)
            except ValidationError as e:
                print(f"日期格式错误: {e}", file=sys.stderr)
                return 1

            result = update_plan_date(
                client,
                space_id=args.space,
                plan_id=args.id,
                start_date=args.start,
                end_date=args.end
            )
            print_update_result(result, args.format)

        client.close()
        return 0

    except AuthenticationError as e:
        print(f"认证失败: {e}", file=sys.stderr)
        print("请确保配置文件 config/config.yaml 中包含有效的认证信息", file=sys.stderr)
        return 1
    except ICafeError as e:
        print(f"API 错误: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
