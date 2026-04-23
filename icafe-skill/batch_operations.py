#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 批量操作脚本

独立可执行的批量操作工具，支持批量查询、状态检查等。

使用示例:
    python scripts/batch_operations.py --space my-space --iql "优先级=P0"
    python scripts/batch_operations.py --space my-space --iql "流程状态=新建" --limit 50
    python scripts/batch_operations.py --space my-space --status-summary
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.query import list_cards, get_card_status


def batch_query(client, space_id, iql=None, limit=20, order=None, format_type='text'):
    """批量查询卡片"""
    cards = list_cards(client, space_id=space_id, iql=iql, max_records=str(limit), order=order)
    
    if format_type == 'json':
        output = [
            {
                'id': c.full_id,
                'title': c.title,
                'type': c.type,
                'status': c.status,
                'assignee': c.assignee,
                'priority': c.priority,
            }
            for c in cards
        ]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"批量查询结果 (共 {len(cards)} 条)")
        if iql:
            print(f"IQL: {iql}")
        print(f"{'='*60}\n")
        
        for i, card in enumerate(cards, 1):
            print(f"{i:3d}. [{card.full_id}] {card.title}")
            print(f"     类型: {card.type} | 状态: {card.status} | 负责人: {card.assignee}")
        
        print(f"\n{'='*60}\n")
    
    return cards


def status_summary(client, space_id, iql=None, limit=100, order=None, format_type='text'):
    """统计卡片状态分布"""
    cards = list_cards(client, space_id=space_id, iql=iql, max_records=str(limit), order=order)
    
    status_counter = Counter(c.status for c in cards)
    type_counter = Counter(c.type for c in cards)
    priority_counter = Counter(c.priority for c in cards if c.priority)
    assignee_counter = Counter(c.assignee for c in cards if c.assignee)
    
    if format_type == 'json':
        output = {
            'total': len(cards),
            'by_status': dict(status_counter),
            'by_type': dict(type_counter),
            'by_priority': dict(priority_counter),
            'by_assignee': dict(assignee_counter.most_common(10)),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"卡片统计摘要 (共 {len(cards)} 条)")
        if iql:
            print(f"IQL: {iql}")
        print(f"{'='*60}")
        
        print(f"\n[状态] 按状态分布:")
        for status, count in status_counter.most_common():
            bar = '█' * min(count, 30)
            print(f"   {status:15s} {count:4d} {bar}")

        print(f"\n[类型] 按类型分布:")
        for card_type, count in type_counter.most_common():
            bar = '█' * min(count, 30)
            print(f"   {card_type:15s} {count:4d} {bar}")

        if priority_counter:
            print(f"\n[优先级] 按优先级分布:")
            for priority, count in sorted(priority_counter.items()):
                bar = '█' * min(count, 30)
                print(f"   {priority:15s} {count:4d} {bar}")

        if assignee_counter:
            print(f"\n[负责人] 负责人排名 (Top 10):")
            for assignee, count in assignee_counter.most_common(10):
                bar = '█' * min(count, 30)
                print(f"   {assignee:15s} {count:4d} {bar}")
        
        print(f"\n{'='*60}\n")
    
    return cards


def main():
    parser = argparse.ArgumentParser(
        description='iCafe 批量操作工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --space my-space --iql "优先级=P0"
  %(prog)s --space my-space --iql "流程状态=新建 AND 负责人=zhangsan" --limit 50
  %(prog)s --space my-space --iql "类型=Bug" --order lastModifiedTime
  %(prog)s --space my-space --order "自定义字段名"
  %(prog)s --space my-space --status-summary
  %(prog)s --space my-space --status-summary --iql "类型=Bug" --format json
        """
    )
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--iql', '-q', help='IQL 查询表达式')
    parser.add_argument('--limit', '-l', type=int, default=20,
                        help='最大返回数量 (默认: 20)')
    parser.add_argument('--order', '-o', default='lastModifiedTime',
                        help='排序字段，支持自定义字段 (默认: lastModifiedTime)')
    parser.add_argument('--status-summary', action='store_true',
                        help='显示状态统计摘要')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')

    args = parser.parse_args()

    try:
        # 初始化客户端（使用配置文件，相对路径基于脚本所在目录）
        script_dir = Path(__file__).parent.parent
        default_config_path = script_dir / "config" / "config.yaml"
        config_path = args.config if args.config else str(default_config_path)
        client = init_client(config_file=config_path)
        
        if args.status_summary:
            # 统计摘要模式
            status_summary(
                client,
                space_id=args.space,
                iql=args.iql,
                limit=args.limit,
                order=args.order,
                format_type=args.format
            )
        else:
            # 批量查询模式
            batch_query(
                client,
                space_id=args.space,
                iql=args.iql,
                limit=args.limit,
                order=args.order,
                format_type=args.format
            )
        
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