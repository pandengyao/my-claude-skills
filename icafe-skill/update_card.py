#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 卡片更新脚本

独立可执行的卡片更新工具，支持命令行参数和 dry-run 模式。

使用示例:
    python scripts/update_card.py --space my-space --id 123 --status "开发中"
    python scripts/update_card.py --space my-space --id 123 --assignee zhangsan --comment "分配任务"
    python scripts/update_card.py --space my-space --id 123 --status "已完成" --execute
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError, MissingRequiredFieldsError,ValidationError
from icafe_skill.update import update_card, preview_update


def main():
    parser = argparse.ArgumentParser(
        description='更新 iCafe 卡片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --space my-space --id 123 --status "开发中"
  %(prog)s --space my-space --id 123 --assignee zhangsan --comment "分配任务"
  %(prog)s --space my-space --id 123 --priority P0-Highest --execute
  %(prog)s --space my-space --id 123 --related "test-1,test-2" --rel-operation add --execute
  %(prog)s --space my-space --id 123 --operator zhangsan --execute
  %(prog)s --space my-space --id 123 --status "已完成" --no-check-status --execute
  %(prog)s --space my-space --id 123 --rel-project "12345" --rel-project-operation add --execute

注意:
  默认为 dry-run 模式，不会实际修改卡片。
  使用 --execute 参数可实际执行修改操作。

关联卡片:
  --related "空间标识-序号,空间标识-序号" 指定关联卡片
  --rel-operation add 添加关联 | delete 删除关联

关联项目:
  --rel-project "项目编号" 指定关联项目
  --rel-project-operation add 添加关联 | delete 删除关联
        """
    )
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--id', '-i', required=True, help='卡片 ID')
    parser.add_argument('--status', help='更新状态')
    parser.add_argument('--assignee', '-a', help='更新负责人')
    parser.add_argument('--priority', '-p', help='更新优先级')
    parser.add_argument('--title', '-t', help='更新标题')
    parser.add_argument('--comment', '-c', help='添加评论')
    parser.add_argument('--related', '-r', help='关联卡片（格式：空间标识-序号,空间标识-序号）')
    parser.add_argument('--rel-operation', choices=['add', 'delete'], help='关联卡片操作：add 添加 / delete 删除')
    parser.add_argument('--operator', '-o', help='修改人（邮箱前缀），校验卡片权限')
    parser.add_argument('--no-check-status', action='store_true',
                        help='禁用流程状态可达检查（默认会检查）')
    parser.add_argument('--rel-project', help='关联项目编号')
    parser.add_argument('--rel-project-operation', choices=['add', 'delete'],
                        help='关联项目操作：add 添加 / delete 删除')
    parser.add_argument('--field', '-F', nargs=2, action='append', metavar=('KEY', 'VALUE'),
                        help='自定义字段 (可多次使用)')
    parser.add_argument('--preview', action='store_true',
                        help='仅预览更新内容（不需要认证）')
    parser.add_argument('--execute', action='store_true',
                        help='实际执行更新（默认为 dry-run 模式）')
    parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    
    args = parser.parse_args()
    
    # 构建字段更新
    fields = {}
    if args.status:
        fields['status'] = args.status
    if args.assignee:
        fields['assignee'] = args.assignee
    if args.priority:
        fields['priority'] = args.priority
    if args.title:
        fields['title'] = args.title
    if args.field:
        for key, value in args.field:
            fields[key] = value

    # 处理关联卡片参数（单独的参数，不放在 fields 中）
    rel_issue = None
    rel_issue_operation = None
    if args.related:
        if args.rel_operation:
            rel_issue = args.related
            rel_issue_operation = args.rel_operation
        else:
            print("错误: 使用 --related 参数时必须同时指定 --rel-operation (add/delete)", file=sys.stderr)
            return 1
    elif args.rel_operation:
        print("错误: --rel-operation 需要配合 --related 参数使用", file=sys.stderr)
        return 1

    # 处理关联项目参数
    rel_project = None
    rel_project_operation = None
    if args.rel_project:
        if args.rel_project_operation:
            rel_project = args.rel_project
            rel_project_operation = args.rel_project_operation
        else:
            print("错误: 使用 --rel-project 参数时必须同时指定 --rel-project-operation (add/delete)", file=sys.stderr)
            return 1
    elif args.rel_project_operation:
        print("错误: --rel-project-operation 需要配合 --rel-project 参数使用", file=sys.stderr)
        return 1

    # 处理 operator 和 is_check_status 参数
    operator = args.operator if args.operator else None
    is_check_status = False if args.no_check_status else None

    if not fields and not args.comment and not rel_issue and not rel_project:
        print("错误: 请至少指定一个要更新的字段、评论、关联卡片或关联项目", file=sys.stderr)
        return 1

    try:
        # 预览模式（不需要认证）
        if args.preview:
            preview = preview_update(
                space_id=args.space,
                card_id=args.id,
                fields=fields if fields else {},
                comment=args.comment,
                rel_issue=rel_issue,
                rel_issue_operation=rel_issue_operation,
                operator=operator,
                is_check_status=is_check_status,
                rel_project=rel_project,
                rel_project_operation=rel_project_operation
            )
            print(preview)
            return 0

        # 初始化客户端
        script_dir = Path(__file__).parent.parent
        default_config_path = script_dir / "config" / "config.yaml"
        config_path = args.config if args.config else str(default_config_path)
        client = init_client(config_file=config_path)

        # 执行更新
        dry_run = not args.execute
        result = update_card(
            client,
            space_id=args.space,
            card_id=args.id,
            fields=fields if fields else {},
            comment=args.comment,
            rel_issue=rel_issue,
            rel_issue_operation=rel_issue_operation,
            operator=operator,
            is_check_status=is_check_status,
            rel_project=rel_project,
            rel_project_operation=rel_project_operation,
            dry_run=dry_run,
            config_path=config_path
        )
        
        # 输出结果
        if args.format == 'json':
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            if dry_run:
                print("卡片更新预览 (dry-run 模式)")
            else:
                print("卡片更新结果")
            print(f"{'='*60}")
            print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        client.close()
        return 0
        
    except AuthenticationError as e:
        print(f"认证失败: {e} - AuthenticationError ", file=sys.stderr)
        print("请确保配置文件 config/config.yaml 中包含有效的认证信息", file=sys.stderr)
        return 1
    except ValidationError as e:
        print("提示: 卡片状态更新失败，需要通过 check_workflow.py 来识别正常流转流程", file=sys.stderr)
        return 1
    except MissingRequiredFieldsError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"状态转换失败 - 缺少必填字段 - {type(e).__name__}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"当前状态: {e.current_status}", file=sys.stderr)
        print(f"目标状态: {e.target_status}", file=sys.stderr)
        print(f"\n缺少必填字段 ({len(e.missing_fields)} 个):", file=sys.stderr)
        for i, field in enumerate(e.missing_fields, 1):
            print(f"  {i}. {field}", file=sys.stderr)
        if e.field_options:
            print(f"\n使用以下命令检测详情和获取建议值:", file=sys.stderr)
            print(f"  python scripts/detect_required_fields.py --space {args.space} --id {args.id} --status \"{e.target_status}\"")
        print(f"{'='*60}\n", file=sys.stderr)
        return 1
    except ICafeError as e:
        print(f"API 错误: {e}", file=sys.stderr)
        # 如果 response_body 里包含"流程状态"，说明需要通过 check_workflow.py 来识别正常流转流程
        if '流程状态=' in e.details.get('response_body', ''):
            print("提示: 卡片状态更新失败，需要通过 check_workflow.py 来识别正常流转流程", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
