#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 卡片查询脚本

独立可执行的卡片查询工具，支持命令行参数。

使用示例:
    # 查询单个卡片
    python scripts/query_card.py --space edc-scrum --id 352568

    # 批量查询卡片列表
    python scripts/query_card.py --space edc-scrum --list
    python scripts/query_card.py --space edc-scrum --list --iql "流程状态=新建"
    python scripts/query_card.py --space edc-scrum --list --order lastModifiedTime --desc
    python scripts/query_card.py --space edc-scrum --list --detail --associations

    # 查询卡片详情、研发数据链、评论
    python scripts/query_card.py --space edc-scrum --id 352568 --devinfo
    python scripts/query_card.py --space edc-scrum --id 352568 --comments

    # 以 JSON 格式输出所有原始字段
    python scripts/query_card.py --space edc-scrum --id 352568 --raw
    python scripts/query_card.py --space edc-scrum --list --raw
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.query import get_card, get_dev_info, get_comments, list_cards


def print_card_info(card, format_type='text', show_fields=False):
    """打印卡片信息"""
    if format_type == 'json':
        output = {
            'id': card.full_id,
            'title': card.title,
            'type': card.type,
            'status': card.status,
            'assignee': card.assignee,
            'priority': card.priority,
            'creator': card.creator,
            'detail': card.detail,
            'parent': card.parent.to_dict() if card.parent else None,
            'children': [c.to_dict() for c in card.children],
            'related_issues': [r.to_dict() for r in card.related_issues],
        }
        # 添加自定义字段到 JSON 输出
        if show_fields and card.extra_fields.get('properties'):
            output['custom_fields'] = card.extra_fields['properties']
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"卡片信息: {card.full_id}")
        print(f"{'='*60}")
        print(f"标题: {card.title}")
        print(f"类型: {card.type}")
        print(f"状态: {card.status}")
        print(f"负责人: {card.assignee}")
        print(f"优先级: {card.priority}")
        print(f"创建人: {card.creator}")
        if card.detail:
            print(f"\n详情:\n{card.detail[:500]}{'...' if len(card.detail) > 500 else ''}")

        # 显示自定义字段
        if show_fields and card.extra_fields.get('properties'):
            properties = card.extra_fields['properties']
            # 过滤关键字段（Bug 相关的）
            key_field_patterns = ['Bug', 'bug', '修复', '分析', '原因', '方案', '结论', '车型']
            key_fields = {k: v for k, v in properties.items()
                         if any(pattern in k for pattern in key_field_patterns) and v}

            if key_fields:
                print(f"\n{'='*60}")
                print("关键字段")
                print(f"{'='*60}")
                for key, value in key_fields.items():
                    print(f"{key}: {value}")

        # 显示关系信息
        if card.parent:
            print(f"\n父卡片:")
            print(f"  {card.parent.full_id}: {card.parent.title}")

        if card.children:
            print(f"\n子卡片 ({len(card.children)}个):")
            for child in card.children[:10]:  # 最多显示10个
                print(f"  - {child.full_id}: {child.title}")
            if len(card.children) > 10:
                print(f"  ... 还有 {len(card.children) - 10} 个子卡片")

        if card.related_issues:
            print(f"\n关联卡片 ({len(card.related_issues)}个):")
            for rel in card.related_issues[:10]:  # 最多显示10个
                print(f"  - {rel.full_id}: {rel.title}")
            if len(card.related_issues) > 10:
                print(f"  ... 还有 {len(card.related_issues) - 10} 个关联卡片")

        print(f"{'='*60}\n")


def print_cards_list(cards, format_type='text'):
    """打印卡片列表信息"""
    if format_type == 'json':
        output = [
            {
                'id': c.full_id,
                'title': c.title,
                'type': c.type,
                'status': c.status,
                'assignee': c.assignee,
                'priority': c.priority,
                'creator': c.creator,
                'detail': c.detail,
            }
            for c in cards
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"卡片列表 (共 {len(cards)} 条)")
        print(f"{'='*60}\n")

        for i, card in enumerate(cards, 1):
            print(f"{i:3d}. [{card.full_id}] {card.title}")
            print(f"     类型: {card.type} | 状态: {card.status} | 负责人: {card.assignee}")
            if card.detail:
                detail_preview = card.detail[:80] + '...' if len(card.detail) > 80 else card.detail
                print(f"     详情: {detail_preview}")

            # 显示关系信息
            if card.children:
                print(f"     子卡片: {len(card.children)} 个")
            if hasattr(card, 'associations') and card.associations:
                print(f"     关联卡片: {len(card.associations)} 个")

            print()

        print(f"{'='*60}\n")


def print_dev_info(dev_info, format_type='text'):
    """打印研发数据链信息"""
    if format_type == 'json':
        output = {
            'icode_reviews': len(dev_info.icode_reviews),
            'pipelines': len(dev_info.pipelines),
            'branches': len(dev_info.branches),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print("研发数据链")
        print(f"{'='*60}")
        print(f"iCode 评审数: {len(dev_info.icode_reviews)}")
        print(f"流水线数: {len(dev_info.pipelines)}")
        print(f"分支数: {len(dev_info.branches)}")
        if dev_info.icode_reviews:
            print("\n最近评审:")
            for review in dev_info.icode_reviews[:3]:
                print(f"  - {review.get('title', 'N/A')}")
        print(f"{'='*60}\n")


def print_comments(comments, format_type='text'):
    """打印评论信息"""
    if format_type == 'json':
        output = [
            {
                'author': c.author,
                'content': c.content,
                'created_at': str(c.created_at) if c.created_at else None,
            }
            for c in comments
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"评论列表 (共 {len(comments)} 条)")
        print(f"{'='*60}")
        for i, comment in enumerate(comments, 1):
            print(f"\n[{i}] {comment.author} - {comment.created_at}")
            print(f"    {comment.content[:200]}{'...' if len(comment.content) > 200 else ''}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='查询 iCafe 卡片信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询单个卡片
  %(prog)s --space edc-scrum --id 352568
  %(prog)s --space edc-scrum --id 352568 --format json

  # 查询单个卡片并获取研发数据链和评论
  %(prog)s --space edc-scrum --id 352568 --devinfo
  %(prog)s --space edc-scrum --id 352568 --comments
  %(prog)s --space edc-scrum --id 352568 --fields
  %(prog)s --space edc-scrum --id 352568 --raw

  # 批量查询卡片列表
  %(prog)s --space edc-scrum --list
  %(prog)s --space edc-scrum --list --raw
  %(prog)s --space edc-scrum --list --iql "流程状态=新建"
  %(prog)s --space edc-scrum --list --iql "流程状态=新建 AND 类型=Bug"
  %(prog)s --space edc-scrum --list --order lastModifiedTime --desc
  %(prog)s --space edc-scrum --list --detail --associations
  %(prog)s --space edc-scrum --list --children --okr
  %(prog)s --space edc-scrum --list --accumulate --limit 50

单个卡片查询参数说明:
  --fields            显示自定义字段（如Bug问题原因、Bug分析结论、Bug修复方案等）
  --raw               以 JSON 格式输出所有原始字段（包含 API 返回的完整数据）

列表查询参数说明:
  --list              启用列表查询模式
  --iql              IQL 查询表达式
  --order            排序字段 (默认: createTime)
  --desc             倒序排序
  --detail           显示卡片详情内容
  --associations     显示关联卡片信息
  --children         显示子卡片信息
  --okr              显示关联 OKR 信息
  --accumulate       显示周实际工时填报明细
  --limit            每页返回数量 (默认: 100, 最大: 100)
        """
    )

    # 通用参数
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    # 查询模式参数
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--id', '-i', help='查询指定卡片 ID')
    mode_group.add_argument('--list', '-l', action='store_true', help='批量查询卡片列表')

    # 单个卡片查询参数
    parser.add_argument('--devinfo', '-d', action='store_true',
                        help='同时获取研发数据链信息（仅用于单个卡片查询）')
    parser.add_argument('--comments', '-c', action='store_true',
                        help='同时获取评论列表（仅用于单个卡片查询）')
    parser.add_argument('--fields', '-F', action='store_true',
                        help='显示自定义字段（如Bug问题原因、Bug分析结论等）')
    parser.add_argument('--raw', '-r', action='store_true',
                        help='以 JSON 格式输出所有原始字段（包含 API 返回的完整数据）')

    # 列表查询参数
    parser.add_argument('--iql', '-q', help='IQL 查询表达式（仅用于列表查询）')
    parser.add_argument('--order', '-o', default='createTime',
                        help='排序字段（默认: createTime，仅用于列表查询）')
    parser.add_argument('--desc', action='store_true',
                        help='倒序排序（仅用于列表查询）')
    parser.add_argument('--detail', action='store_true',
                        help='显示卡片详情内容（仅用于列表查询）')
    parser.add_argument('--associations', action='store_true',
                        help='显示关联卡片信息（仅用于列表查询）')
    parser.add_argument('--children', action='store_true',
                        help='显示子卡片信息（仅用于列表查询）')
    parser.add_argument('--okr', action='store_true',
                        help='显示关联 OKR 信息（仅用于列表查询）')
    parser.add_argument('--accumulate', action='store_true',
                        help='显示周实际工时填报明细（仅用于列表查询）')
    parser.add_argument('--limit', '-n', type=str, default='100',
                        help='每页返回数量，默认 100，最大 100（仅用于列表查询）')

    args = parser.parse_args()

    try:
        # 初始化客户端（使用配置文件，相对路径基于脚本所在目录）
        script_dir = Path(__file__).parent.parent
        default_config_path = script_dir / "config" / "config.yaml"
        config_path = args.config if args.config else str(default_config_path)
        client = init_client(config_file=config_path)

        if args.id:
            # 单个卡片查询模式
            card = get_card(client, space_id=args.space, card_id=args.id)
            if args.raw:
                # 输出所有原始字段
                print(json.dumps(card.extra_fields, indent=2, ensure_ascii=False))
            else:
                print_card_info(card, args.format, show_fields=args.fields)

            # 获取研发数据链
            if args.devinfo:
                dev_info = get_dev_info(client, space_id=args.space, issue_id=args.id)
                print_dev_info(dev_info, args.format)

            # 获取评论
            if args.comments:
                comments = get_comments(client, space_id=args.space, sequence=args.id)
                print_comments(comments, args.format)

        else:
            # 列表查询模式
            cards = list_cards(
                client,
                space_id=args.space,
                iql=args.iql,
                max_records=args.limit,
                show_detail="true" if args.detail else "",
                show_associations=args.associations,
                is_desc=args.desc,
                order=args.order,
                show_children=args.children,
                show_okr=args.okr,
                show_accumulate=args.accumulate,
            )
            if args.raw:
                # 输出所有原始字段
                output = [c.extra_fields for c in cards]
                print(json.dumps(output, indent=2, ensure_ascii=False))
            else:
                print_cards_list(cards, args.format)

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
