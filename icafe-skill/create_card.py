#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 卡片创建脚本

独立可执行的卡片创建工具，支持命令行参数和 dry-run 模式。

使用示例:
    python scripts/create_card.py --space my-space --title "新任务" --type Story
    python scripts/create_card.py --space my-space --title "Bug修复" --type Bug --priority P0-Highest
    python scripts/create_card.py --space my-space --title "任务" --type Story --execute
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.models import Issue
from icafe_skill.create import create_cards


def main():
    parser = argparse.ArgumentParser(
        description='创建 iCafe 卡片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --space my-space --title "新任务" --type Story
  %(prog)s --space my-space --title "Bug修复" --type Bug --priority P0-Highest
  %(prog)s --space my-space --title "任务" --type Story --assignee zhangsan --execute

注意:
  默认为 dry-run 模式，不会实际创建卡片。
  使用 --execute 参数可实际执行创建操作。
        """
    )
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--title', '-t', required=True, help='卡片标题')
    parser.add_argument('--type', required=True, help='卡片类型 (如 Story, Bug, Task)')
    parser.add_argument('--detail', '-d', default='', help='卡片详情描述')
    parser.add_argument('--assignee', '-a', help='负责人用户名')
    parser.add_argument('--creator', '-c', help='创建人用户名')
    parser.add_argument('--priority', '-p', default='P2-Medium',
                        help='优先级 (默认: P2-Medium)')
    parser.add_argument('--status', default='新建', help='初始状态 (默认: 新建)')
    parser.add_argument('--comment', help='初始评论')
    parser.add_argument('--notify', nargs='*', help='通知邮箱列表')
    parser.add_argument('--parent', help='父卡片序号（创建子卡片时使用）')
    parser.add_argument('--parent-space', help='父卡片所属空间前缀（跨空间父卡片时使用）')
    parser.add_argument('--related', help='关联卡片（格式：空间标识-序号,空间标识-序号）')
    parser.add_argument('--execute', action='store_true',
                        help='实际执行创建（默认为 dry-run 模式）')
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
        
        # 构建 Issue 对象
        issue_params = {
            'title': args.title,
            'detail': args.detail or f'{args.title} 的详细描述',
            'type': args.type,
            'status': args.status,
            'priority': args.priority,
        }
        
        if args.assignee:
            issue_params['assignee'] = args.assignee
        if args.creator:
            issue_params['creator'] = args.creator
        if args.comment:
            issue_params['comment'] = args.comment
        if args.notify:
            issue_params['notify_emails'] = args.notify
        if args.parent:
            issue_params['parent'] = args.parent
        if args.parent_space:
            issue_params['parent_space_prefix_code'] = args.parent_space
        if args.related:
            issue_params['rel_issue_space_pre_seq'] = args.related
        
        issue = Issue.create(**issue_params)
        
        # 执行创建
        dry_run = not args.execute
        result = create_cards(
            client,
            space_id=args.space,
            issues=[issue],
            dry_run=dry_run
        )
        
        # 输出结果
        if args.format == 'json':
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            if dry_run:
                print("卡片创建预览 (dry-run 模式)")
            else:
                print("卡片创建结果")
            print(f"{'='*60}")
            print(f"空间: {result['space_id']}")
            print(f"卡片数: {result['issues_count']}")
            print(f"端点: {result['endpoint']}")
            print(f"\n请求数据:")
            print(json.dumps(result['payload'], indent=2, ensure_ascii=False))
            
            if dry_run:
                print(f"\n⚠️  这是预览模式，卡片未实际创建")
                print(f"    添加 --execute 参数可实际创建卡片")
            print(f"{'='*60}\n")
        
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