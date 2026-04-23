#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 字段配置管理脚本

独立可执行的字段配置工具，提供字段查询和验证功能。

使用示例:
    python scripts/field_config.py types --space my-space
    python scripts/field_config.py fields --space my-space --type Bug
    python scripts/field_config.py validate --space my-space --type Bug --fields '{"优先级": "P1"}'
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.field_config import SpaceConfigCache
from icafe_skill.helpers import (
    list_available_types,
    get_required_fields_info
)
from icafe_skill.auth import load_config_file

# 获取脚本所在目录的默认配置路径
SCRIPT_DIR = Path(__file__).parent.parent
DEFAULT_CONFIG_PATH = str(SCRIPT_DIR / "config" / "config.yaml")


def cmd_types(args):
    """查询空间的问题类型列表"""
    config_path = args.config if hasattr(args, 'config') and args.config else DEFAULT_CONFIG_PATH
    cache = SpaceConfigCache(
        init_client(config_file=config_path),
        cache_ttl=args.cache_ttl if hasattr(args, 'cache_ttl') else 3600
    )

    if args.refresh:
        cache.clear_cache(space_id=args.space)

    types = list_available_types(cache.client, args.space, cache)

    if args.format == 'json':
        print(json.dumps(types, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*70}")
        print(f"可用卡片类型 - {args.space}")
        print(f"{'='*70}")
        print(f"共 {len(types)} 种类型:\n")

        for i, t in enumerate(types, 1):
            print(f"{i}. {t['name']} (ID: {t['id']})")
            if t['alias']:
                print(f"   别名: {t['alias']}")
            if t['has_children']:
                print(f"   子类型数: {t['child_count']}")
            print()

        print(f"{'='*70}\n")

    cache.client.close()
    return 0


def cmd_fields(args):
    """查询指定类型的字段配置"""
    config_path = args.config if hasattr(args, 'config') and args.config else DEFAULT_CONFIG_PATH
    cache = SpaceConfigCache(
        init_client(config_file=config_path),
        cache_ttl=args.cache_ttl if hasattr(args, 'cache_ttl') else 3600
    )

    if args.refresh:
        cache.clear_cache(space_id=args.space)

    # 获取类型信息
    types = cache.get_issue_types(args.space, force_refresh=args.refresh)
    if args.type not in types:
        print(f"错误: 问题类型 '{args.type}' 不存在", file=sys.stderr)
        print(f"可用类型: {', '.join(types.keys())}", file=sys.stderr)
        cache.client.close()
        return 1

    type_config = cache.get_type_with_fields(args.space, args.type, force_refresh=args.refresh)

    required_fields = type_config.get_required_fields()
    optional_fields = type_config.get_optional_fields()

    if args.format == 'json':
        output = {
            'space_id': args.space,
            'issue_type': args.type,
            'type_id': type_config.type_id,
            'required_fields': [
                {
                    'name': f.name,
                    'display': f.display,
                    'type': f.type,
                    'default_value': f.default_value,
                    'options': f.value_items if f.type in ['select_list', 'select_list_multiple', 'radio_field'] else None,
                    'prompt': f.get_prompt()
                }
                for f in required_fields
            ],
            'optional_fields': [
                {
                    'name': f.name,
                    'display': f.display,
                    'type': f.type,
                    'default_value': f.default_value,
                    'options': f.value_items if f.type in ['select_list', 'select_list_multiple', 'radio_field'] else None,
                    'prompt': f.get_prompt()
                }
                for f in optional_fields
            ]
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*70}")
        print(f"字段配置 - {args.type} ({args.space})")
        print(f"{'='*70}")

        # 必填字段
        print(f"\n必填字段 ({len(required_fields)} 个):")
        if required_fields:
            for field in required_fields:
                print(f"\n  • {field.display}")
                print(f"    类型: {field.type}")
                if field.type in ['select_list', 'radio_field']:
                    if len(field.value_items) <= 50:
                        print(f"    可选值: {', '.join(field.value_items)}")
                    else:
                        print(f"    可选值: {', '.join(field.value_items[:50])}... 等 {len(field.value_items)} 个")
                elif field.type == 'select_list_multiple':
                    if len(field.value_items) <= 50:
                        print(f"    可选值: {', '.join(field.value_items)}")
                    else:
                        print(f"    可选值: {', '.join(field.value_items[:50])}... 等 {len(field.value_items)} 个")
                    print(f"    (可多选)")
                elif field.type == 'user_picker':
                    print(f"    输入用户名")
                elif field.type == 'date_time':
                    print(f"    格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
                elif field.type == 'number_field':
                    print(f"    输入数字")
                if field.default_value:
                    print(f"    默认值: {field.default_value}")
        else:
            print(f"  无必填字段")

        # 可选字段
        print(f"\n可选字段 ({len(optional_fields)} 个):")
        if optional_fields:
            for field in optional_fields:
                print(f"\n  • {field.display}")
                print(f"    类型: {field.type}")
                if field.type in ['select_list', 'radio_field']:
                    if len(field.value_items) <= 50:
                        print(f"    可选值: {', '.join(field.value_items)}")
                    else:
                        print(f"    可选值: {', '.join(field.value_items[:50])}... 等 {len(field.value_items)} 个")
                elif field.type == 'select_list_multiple':
                    if len(field.value_items) <= 50:
                        print(f"    可选值: {', '.join(field.value_items)}")
                    else:
                        print(f"    可选值: {', '.join(field.value_items[:50])}... 等 {len(field.value_items)} 个")
                    print(f"    (可多选)")
                elif field.type == 'user_picker':
                    print(f"    输入用户名")
                elif field.type == 'date_time':
                    print(f"    格式: YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
                elif field.type == 'number_field':
                    print(f"    输入数字")
                if field.default_value:
                    print(f"    默认值: {field.default_value}")
        else:
            print(f"  无可选字段")

        print(f"\n{'='*70}\n")

    cache.client.close()
    return 0


def cmd_validate(args):
    """验证字段数据（仅验证字段值有效性，不检查必填字段）"""
    config_path = args.config if hasattr(args, 'config') and args.config else DEFAULT_CONFIG_PATH
    cache = SpaceConfigCache(
        init_client(config_file=config_path),
        cache_ttl=args.cache_ttl if hasattr(args, 'cache_ttl') else 3600
    )

    if args.refresh:
        cache.clear_cache(space_id=args.space)

    # 解析字段数据
    try:
        fields_data = json.loads(args.fields)
    except json.JSONDecodeError as e:
        print(f"错误: 无效的 JSON 格式 - {e}", file=sys.stderr)
        cache.client.close()
        return 1

    # 获取类型配置
    types = cache.get_issue_types(args.space, force_refresh=args.refresh)
    if args.type not in types:
        print(f"错误: 问题类型 '{args.type}' 不存在", file=sys.stderr)
        print(f"可用类型: {', '.join(types.keys())}", file=sys.stderr)
        cache.client.close()
        return 1

    type_config = cache.get_type_with_fields(args.space, args.type, force_refresh=args.refresh)

    # 准备字段数据用于验证
    validate_data = fields_data.copy()
    if args.title:
        validate_data["标题"] = args.title
    if args.detail:
        validate_data["内容"] = args.detail

    # 仅验证已提供字段的有效性（不检查必填字段）
    errors = []
    for key, value in validate_data.items():
        field = type_config.fields.get(key)
        if not field:
            errors.append(f"未知字段: {key}")
            continue

        try:
            field.validate_value(value)
        except Exception as e:
            errors.append(str(e))

    is_valid = len(errors) == 0

    if args.format == 'json':
        output = {
            'valid': is_valid,
            'errors': errors,
            'validated_fields': list(validate_data.keys())
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*70}")
        print(f"字段验证结果 - {args.type} ({args.space})")
        print(f"{'='*70}\n")

        if is_valid:
            print("✓ 验证通过！所有字段值有效。\n")
        else:
            print("✗ 验证失败！\n")

        if errors:
            print("验证错误:")
            for err in errors:
                print(f"  - {err}")
            print()

        print(f"{'='*70}\n")

    cache.client.close()
    return 0 if is_valid else 1


def main():
    parser = argparse.ArgumentParser(
        description='iCafe 字段配置管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
子命令:
  types        查询空间的问题类型列表
  fields       查询指定类型的字段配置
  validate     验证字段数据

示例:
  # 查询问题类型
  %(prog)s types --space my-space

  # 查询字段配置
  %(prog)s fields --space my-space --type Bug
  %(prog)s fields --space my-space --type Bug --format json

  # 验证字段数据
  %(prog)s validate --space my-space --type Bug --fields '{"优先级": "P1"}'

注意:
  - 字段数据必须使用 JSON 格式传入
  - 缓存默认有效期为 1 小时，使用 --refresh 可强制刷新
        """
    )

    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # types 子命令
    types_parser = subparsers.add_parser('types', help='查询空间的问题类型列表')
    types_parser.add_argument('--space', '-s', required=True, help='空间 ID')
    types_parser.add_argument('--refresh', action='store_true', help='强制刷新缓存')
    types_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                             help='输出格式 (默认: text)')
    types_parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    # fields 子命令
    fields_parser = subparsers.add_parser('fields', help='查询指定类型的字段配置')
    fields_parser.add_argument('--space', '-s', required=True, help='空间 ID')
    fields_parser.add_argument('--type', '-t', required=True, help='问题类型名称')
    fields_parser.add_argument('--refresh', action='store_true', help='强制刷新缓存')
    fields_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                              help='输出格式 (默认: text)')
    fields_parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    # validate 子命令
    validate_parser = subparsers.add_parser('validate', help='验证字段数据')
    validate_parser.add_argument('--space', '-s', required=True, help='空间 ID')
    validate_parser.add_argument('--type', '-t', required=True, help='问题类型名称')
    validate_parser.add_argument('--fields', required=True, help='字段数据 (JSON 格式)')
    validate_parser.add_argument('--title', help='卡片标题 (用于验证，默认: 测试标题)')
    validate_parser.add_argument('--detail', help='卡片详情 (用于验证，默认: 测试详情)')
    validate_parser.add_argument('--refresh', action='store_true', help='强制刷新缓存')
    validate_parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                               help='输出格式 (默认: text)')
    validate_parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == 'types':
            return cmd_types(args)
        elif args.command == 'fields':
            return cmd_fields(args)
        elif args.command == 'validate':
            return cmd_validate(args)
        else:
            parser.print_help()
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
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
