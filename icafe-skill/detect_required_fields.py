#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iCafe Skill - 必填字段检测脚本

独立可执行的必填字段检测工具，用于分析将卡片流转到目标状态时需要填写的必填字段。

使用示例:
    python scripts/detect_required_fields.py --space my-space --id 123 --status "开发中"
    python scripts/detect_required_fields.py --space edc-scrum --id 352568 --status "已修复"
    python scripts/detect_required_fields.py --space my-space --id 123 --status "已修复" --max-samples 5
"""

import argparse
import json
import sys
from pathlib import Path

# 将父目录添加到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from icafe_skill import init_client, ICafeError, AuthenticationError
from icafe_skill.update import detect_required_fields, update_card


def main():
    parser = argparse.ArgumentParser(
        description='检测卡片流转到目标状态时需要填写的必填字段',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --space my-space --id 123 --status "开发中"
  %(prog)s --space edc-scrum-352568 --id 352568 --status "已修复" --format json
  %(prog)s --space my-space --id 123 --status "已修复" --max-samples 5

说明:
  该脚本会分析当前卡片与目标状态卡片之间的差异，
  识别出需要填写的必填字段，并给出建议值。
        """
    )
    parser.add_argument('--space', '-s', required=True, help='空间 ID')
    parser.add_argument('--id', '-i', required=True, help='卡片 ID')
    parser.add_argument('--status', '-t', required=True, dest='target_status', help='目标流程状态')
    parser.add_argument('--max-samples', type=int, default=3,
                        help='查询的样本卡片最大数量 (默认: 3)')
    parser.add_argument('--config', help='配置文件路径（默认: config/config.yaml）')
    parser.add_argument('--format', '-f', choices=['text', 'json'], default='text',
                        help='输出格式 (默认: text)')
    parser.add_argument('--apply', action='store_true',
                        help='应用建议的字段值并更新卡片')

    args = parser.parse_args()

    try:
        # 初始化客户端
        script_dir = Path(__file__).parent.parent
        default_config_path = script_dir / "config" / "config.yaml"
        config_path = args.config if args.config else str(default_config_path)
        client = init_client(config_file=config_path)

        # 检测必填字段
        result = detect_required_fields(
            client=client,
            space_id=args.space,
            card_id=args.id,
            target_status=args.target_status,
            max_sample_cards=args.max_samples
        )

        # 输出结果P
        if args.format == 'json':
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print("必填字段检测结果")
            print(f"{'='*60}")
            print(f"空间 ID: {result.space_id}")
            print(f"卡片 ID: {result.card_id}")
            print(f"当前状态: {result.current_status}")
            print(f"目标状态: {result.target_status}")
            print(f"卡片类型: {result.issue_type}")
            print(f"能否流转: {'是' if result.can_transition else '否'}")
            print(f"置信度: {result.confidence:.2%}")
            print()

            # 样本卡片信息
            print(f"样本卡片: {result.sample_card_count} 张")
            if result.sample_card_ids:
                print(f"样本卡片 ID: {', '.join(result.sample_card_ids)}")
            print()

            # 字段汇总
            print(f"必填字段总数: {result.total_required_fields}")
            print(f"需要填写的字段数: {result.fields_to_fill_count}")
            print()

            # 需要填写的字段
            if result.fields_needing_fill:
                print(f"\n{'─'*60}")
                print("需要填写的字段:")
                print(f"{'─'*60}")
                for field in result.fields_needing_fill:
                    print(f"\n  字段: {field.field_display} ({field.field_type})")
                    print(f"    当前值: {field.current_value}")
                    print(f"    建议值: {field.suggestion}")
                    print(f"    原因: {field.reason}")

                    # 显示样本值
                    if field.sample_values:
                        unique_samples = list(set(str(v) for v in field.sample_values if v))
                        if unique_samples:
                            print(f"    样本值: {', '.join(unique_samples[:5])}")

                    # 显示有效选项
                    if field.options:
                        print(f"    有效选项: {', '.join(field.options[:10])}")

            # 已满足的字段
            # if result.fields_unchanged:
            #     print(f"\n{'─'*60}")
            #     print("已满足的必填字段:")
            #     print(f"{'─'*60}")
            #     for field in result.fields_unchanged:
            #         print(f"  {field.field_display}: {field.current_value}")

            # 推荐字段
            if result.recommended_fields:
                print(f"\n{'─'*60}")
                print("推荐字段 (可直接用于更新):")
                print(f"{'─'*60}")
                for key, value in result.recommended_fields.items():
                    print(f"  {key}: {value}")

            # 警告信息
            if result.warnings:
                print(f"\n{'─'*60}")
                print("警告信息:")
                print(f"{'─'*60}")
                for warning in result.warnings:
                    print(f"  ⚠ {warning}")

            print()

        # 应用建议并更新卡片
        if args.apply and not result.can_transition:
            print(f"\n{'='*60}")
            print("应用建议并更新卡片")
            print(f"{'='*60}")

            suggested_fields = result.get_suggested_update_fields()
            if not suggested_fields:
                print("没有可应用的建议字段")
            else:
                print(f"\n将使用以下字段更新卡片:")
                for key, value in suggested_fields.items():
                    print(f"  {key}: {value}")

                # 添加状态字段
                suggested_fields['status'] = args.target_status

                print(f"\n  流程状态: {args.target_status}")
                print()

                confirm = input("确认更新? (yes/no): ")
                if confirm.lower() in ('yes', 'y'):
                    try:
                        update_result = update_card(
                            client=client,
                            space_id=args.space,
                            card_id=args.id,
                            fields=suggested_fields,
                            dry_run=False
                        )
                        print("\n更新成功!")
                        print(json.dumps(update_result, indent=2, ensure_ascii=False))
                    except ICafeError as e:
                        print(f"\n更新失败: {e}")
                        return 1
                else:
                    print("已取消更新")

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
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
