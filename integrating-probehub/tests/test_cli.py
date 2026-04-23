#!/usr/bin/env python3
"""
ProbeHub CLI 完整测试脚本
测试所有命令和参数组合
"""

import subprocess
import sys
import os
import json
import tempfile
from pathlib import Path

# 测试配置
CLI_PATH = Path(__file__).parent.parent / "scripts" / "probehub_cli.py"
PYTHON = sys.executable

# 测试结果统计
results = {
    "passed": [],
    "failed": [],
    "skipped": []
}


def run_cli(*args, expect_success=True, timeout=10):
    """运行 CLI 命令并返回结果"""
    cmd = [PYTHON, str(CLI_PATH)] + list(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": (result.returncode == 0) == expect_success
        }
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": "Timeout",
            "success": False
        }
    except Exception as e:
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }


def test_case(name, *args, expect_success=True, check_output=None, **kwargs):
    """执行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"命令: python3 probehub_cli.py {' '.join(args)}")
    print("-" * 60)
    
    result = run_cli(*args, expect_success=expect_success, **kwargs)
    
    # 输出结果
    if result["stdout"]:
        print("STDOUT:")
        for line in result["stdout"].split('\n')[:20]:
            print(f"  {line}")
        if len(result["stdout"].split('\n')) > 20:
            print(f"  ... (省略 {len(result['stdout'].split(chr(10))) - 20} 行)")
    
    if result["stderr"] and "NotOpenSSLWarning" not in result["stderr"]:
        print("STDERR:")
        for line in result["stderr"].split('\n')[:10]:
            if line.strip():
                print(f"  {line}")
    
    # 检查输出内容
    output_check_passed = True
    if check_output and result["success"]:
        for pattern in check_output:
            if pattern not in result["stdout"]:
                print(f"⚠️  未找到预期输出: {pattern}")
                output_check_passed = False
    
    # 记录结果
    passed = result["success"] and output_check_passed
    if passed:
        print(f"✅ 测试通过 (返回码: {result['returncode']})")
        results["passed"].append(name)
    else:
        print(f"❌ 测试失败 (返回码: {result['returncode']})")
        results["failed"].append(name)
    
    return result


def test_help_commands():
    """测试帮助命令"""
    print("\n" + "=" * 70)
    print("📋 测试组: 帮助命令")
    print("=" * 70)
    
    # 主帮助
    test_case(
        "主帮助 (--help)",
        "--help",
        check_output=["ProbeHub Agent", "子命令"]
    )
    
    # 各子命令帮助
    subcommands = [
        "health", "register", "list-agents", "heartbeat", "delete-agent",
        "trigger", "batch-trigger", "task-log", "task-results",
        "list-schedules", "create-schedule", "pause-schedule", 
        "resume-schedule", "delete-schedule",
        "alarm-config", "alarm-test", "alarm-history",
        "serve", "generate-template"
    ]
    
    for cmd in subcommands:
        test_case(
            f"子命令帮助 ({cmd} --help)",
            cmd, "--help",
            check_output=["--"]  # 至少有参数说明
        )


def test_local_commands():
    """测试本地命令（不需要网络）"""
    print("\n" + "=" * 70)
    print("📋 测试组: 本地命令")
    print("=" * 70)
    
    # generate-template 命令
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        temp_path = f.name
    
    try:
        test_case(
            "生成模板 (generate-template)",
            "generate-template", "--output", temp_path,
            check_output=["✅", "Agent 模板已生成"]
        )
        
        # 验证生成的文件
        if os.path.exists(temp_path):
            with open(temp_path, 'r') as f:
                content = f.read()
            if "TaskAgent" in content and "task_decorator" in content:
                print("  ✅ 模板内容正确")
            else:
                print("  ❌ 模板内容不完整")
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    # generate-template 默认路径
    test_case(
        "生成模板 (默认路径)",
        "generate-template",
        check_output=["✅"]
    )
    # 清理
    if os.path.exists("my_agent.py"):
        os.unlink("my_agent.py")


def test_parameter_validation():
    """测试参数验证"""
    print("\n" + "=" * 70)
    print("📋 测试组: 参数验证")
    print("=" * 70)
    
    # 缺少必需参数
    test_case(
        "register 缺少 --name",
        "register",
        expect_success=False
    )
    
    test_case(
        "trigger 缺少 --task-name",
        "trigger",
        expect_success=False
    )
    
    test_case(
        "create-schedule 缺少参数",
        "create-schedule",
        expect_success=False
    )
    
    test_case(
        "heartbeat 缺少 --agent-id",
        "heartbeat",
        expect_success=False
    )
    
    test_case(
        "delete-agent 缺少 --agent-id",
        "delete-agent",
        expect_success=False
    )
    
    test_case(
        "task-log 缺少 --execution-id",
        "task-log",
        expect_success=False
    )
    
    test_case(
        "task-results 缺少 --agent-id",
        "task-results",
        expect_success=False
    )
    
    test_case(
        "list-schedules 缺少 --agent-id",
        "list-schedules",
        expect_success=False
    )


def test_json_parameter_parsing():
    """测试 JSON 参数解析"""
    print("\n" + "=" * 70)
    print("📋 测试组: JSON 参数解析")
    print("=" * 70)
    
    # 有效 JSON
    test_case(
        "trigger 有效 JSON 参数",
        "trigger", "--task-name", "test", "--params", '{"key": "value"}',
        timeout=5
    )
    
    # 无效 JSON (应该给出友好错误)
    result = test_case(
        "trigger 无效 JSON 参数",
        "trigger", "--task-name", "test", "--params", '{invalid json}',
        expect_success=False
    )
    # 检查是否有友好的错误提示
    if "JSON" in result.get("stdout", "") or "格式" in result.get("stdout", ""):
        print("  ✅ 提供了友好的 JSON 错误提示")


def test_network_commands():
    """测试网络命令（可能因网络问题失败）"""
    print("\n" + "=" * 70)
    print("📋 测试组: 网络命令 (可能因网络问题失败)")
    print("=" * 70)
    
    # 健康检查
    result = test_case(
        "健康检查 (health)",
        "health",
        timeout=10
    )
    
    network_ok = result["returncode"] == 0
    
    if not network_ok:
        print("\n⚠️  网络不可达，跳过后续网络测试")
        results["skipped"].extend([
            "register", "list-agents", "trigger", "batch-trigger",
            "alarm-config", "alarm-history"
        ])
        return
    
    # 健康检查 verbose
    test_case(
        "健康检查 verbose (health -v)",
        "health", "-v",
        timeout=10
    )
    
    # 列出 Agents
    test_case(
        "列出 Agents (list-agents)",
        "list-agents",
        timeout=10
    )
    
    # 列出 Agents verbose
    test_case(
        "列出 Agents verbose (list-agents -v)",
        "list-agents", "-v",
        timeout=10
    )
    
    # 注册 Agent
    result = test_case(
        "注册 Agent (register)",
        "register", "--name", "test-cli-agent", "--description", "CLI测试Agent",
        timeout=10
    )
    
    # 注册 Agent with tags
    test_case(
        "注册 Agent with tags",
        "register", "--name", "test-cli-agent-tags", "--tags", "test,cli,dev",
        timeout=10
    )
    
    # 报警配置
    test_case(
        "获取报警配置 (alarm-config)",
        "alarm-config",
        timeout=10
    )
    
    # 报警历史
    test_case(
        "获取报警历史 (alarm-history)",
        "alarm-history",
        timeout=10
    )


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 70)
    print("📋 测试组: 错误处理")
    print("=" * 70)
    
    # 无效的 base-url
    test_case(
        "无效 base-url",
        "--base-url", "http://invalid-host-12345.local:9999",
        "health",
        expect_success=False,
        timeout=5
    )
    
    # 不存在的 Agent ID
    test_case(
        "不存在的 Agent ID (heartbeat)",
        "heartbeat", "--agent-id", "non-existent-agent-id-12345",
        expect_success=False,
        timeout=10
    )
    
    # 不存在的 execution ID
    test_case(
        "不存在的 execution ID (task-log)",
        "task-log", "--execution-id", "non-existent-exec-id-12345",
        expect_success=False,
        timeout=10
    )


def test_verbose_mode():
    """测试详细模式"""
    print("\n" + "=" * 70)
    print("📋 测试组: 详细模式 (-v/--verbose)")
    print("=" * 70)
    
    # 各命令的 verbose 模式
    commands_with_verbose = [
        ("health", ["-v"]),
        ("list-agents", ["-v"]),
        ("alarm-history", ["-v"]),
    ]
    
    for cmd, args in commands_with_verbose:
        test_case(
            f"{cmd} verbose 模式",
            cmd, *args,
            timeout=10
        )


def print_summary():
    """打印测试摘要"""
    print("\n" + "=" * 70)
    print("📊 测试摘要")
    print("=" * 70)
    
    total = len(results["passed"]) + len(results["failed"]) + len(results["skipped"])
    
    print(f"\n总计: {total} 个测试")
    print(f"  ✅ 通过: {len(results['passed'])} 个")
    print(f"  ❌ 失败: {len(results['failed'])} 个")
    print(f"  ⏭️  跳过: {len(results['skipped'])} 个")
    
    if results["failed"]:
        print(f"\n❌ 失败的测试:")
        for name in results["failed"]:
            print(f"    - {name}")
    
    if results["skipped"]:
        print(f"\n⏭️  跳过的测试:")
        for name in results["skipped"]:
            print(f"    - {name}")
    
    print("\n" + "=" * 70)
    
    # 返回退出码
    return 0 if not results["failed"] else 1


def main():
    """主函数"""
    print("🚀 ProbeHub CLI 完整测试")
    print(f"CLI 路径: {CLI_PATH}")
    print(f"Python: {PYTHON}")
    
    # 运行测试组
    test_help_commands()
    test_local_commands()
    test_parameter_validation()
    test_json_parameter_parsing()
    test_network_commands()
    test_error_handling()
    test_verbose_mode()
    
    # 打印摘要
    return print_summary()


if __name__ == "__main__":
    sys.exit(main())