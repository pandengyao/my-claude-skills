#!/usr/bin/env python3
"""
ProbeHub Agent Integration 全面测试
"""
import sys
import os
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ['PROBEHUB_PUID'] = '6AF58-A3A32-BEA42-85AF4'
os.environ['PROBEHUB_PROJECT_ID'] = '64'

import inspect
from src import ProbeHubManager, ProbeHubClient
from src import health, list_agents, trigger_task, create_schedule

print("=" * 70)
print("ProbeHub Agent Integration 全面测试报告")
print("=" * 70)

issues = []

# 测试 1: 模块导入检查
print("\n### 测试 1: 模块导入检查")
print("  ✅ ProbeHubManager 导入成功")
print("  ✅ ProbeHubClient 导入成功")
print("  ✅ 便捷函数导入成功 (health, list_agents, trigger_task, create_schedule)")

# 测试 2: __init__.py 便捷函数签名对比
print("\n### 测试 2: 便捷函数签名一致性检查")

# create_schedule
init_sig = inspect.signature(create_schedule)
manager_sig = inspect.signature(ProbeHubManager.create_schedule)
print(f"  __init__.create_schedule: {init_sig}")
print(f"  Manager.create_schedule:  {manager_sig}")
if str(init_sig) != str(manager_sig):
    issues.append({
        "title": "__init__.py create_schedule 签名不匹配",
        "file": "src/__init__.py",
        "description": f"签名不匹配"
    })
    print("  ❌ 签名不匹配")
else:
    print("  ✅ 签名匹配")

# trigger_task
init_sig = inspect.signature(trigger_task)
manager_sig = inspect.signature(ProbeHubManager.trigger_task)
print(f"\n  __init__.trigger_task: {init_sig}")
print(f"  Manager.trigger_task:  {manager_sig}")
if str(init_sig) != str(manager_sig):
    issues.append({
        "title": "__init__.py trigger_task 签名不匹配",
        "file": "src/__init__.py",
        "description": f"签名不匹配"
    })
    print("  ❌ 签名不匹配")
else:
    print("  ✅ 签名匹配")

# 测试 3: API 连接测试
print("\n### 测试 3: API 连接测试")
try:
    result = health()
    print(f"  ✅ 健康检查通过")
except Exception as e:
    print(f"  ❌ 健康检查失败: {type(e).__name__}: {str(e)[:80]}")
    issues.append({"title": "API 连接失败", "description": str(e)})

# 测试 3: create_schedule 参数错误
print("\n### 测试 3: create_schedule 便捷函数参数传递")
try:
    # 这会把 '0 9 * * *' 传给 schedule_type 参数
    result = create_schedule('fake-agent', 'task1', '0 9 * * *')
    print(f"  结果: {result}")
except Exception as e:
    print(f"  create_schedule 调用: {type(e).__name__}: {str(e)[:80]}")

# 测试 4: SKILL.md 文档中的命令验证
print("\n### 测试 4: SKILL.md 文档检查")
skill_md_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'SKILL.md')
with open(skill_md_path, 'r') as f:
    skill_content = f.read()

# 检查 list-agents 命令文档
if '--project-id' in skill_content and 'list-agents' in skill_content:
    # 文档说 list-agents 需要 --project-id，但实际上是全局参数
    if 'list-agents | 获取 Agent 列表 | `--project-id`' in skill_content:
        issues.append({
            "title": "SKILL.md list-agents 参数文档错误",
            "file": "SKILL.md",
            "line": "73",
            "description": "--project-id 是全局参数，不是 list-agents 子命令的专属参数。正确用法是 `python3 probehub_cli.py --project-id 64 list-agents`",
            "fix": "更新文档说明 --project-id 是全局参数"
        })
        print("  ❌ list-agents 参数文档有误")
    else:
        print("  ✅ list-agents 文档正确")

# 检查 alarm-config 缺少 project_id 说明
if 'alarm-config' in skill_content:
    # alarm-config 需要 project_id 但文档未说明
    issues.append({
        "title": "SKILL.md alarm-config 缺少参数说明",
        "file": "SKILL.md",
        "line": "96",
        "description": "alarm-config 命令实际调用 API 时需要 project_id，但文档只说明需要 --puid",
        "fix": "添加 --project-id 参数说明，或在代码中自动传递 project_id"
    })
    print("  ⚠️  alarm-config 文档可能不完整")

# 打印问题汇总
print("\n" + "=" * 70)
print(f"### 发现的问题 ({len(issues)} 个)")
print("=" * 70)

for i, issue in enumerate(issues, 1):
    print(f"\n{i}. **{issue['title']}**")
    print(f"   - 文件: {issue['file']}")
    print(f"   - 行号: {issue['line']}")
    print(f"   - 问题描述: {issue['description']}")
    print(f"   - 修复建议: {issue['fix']}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)