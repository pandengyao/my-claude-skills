#!/usr/bin/env python3
"""
ProbeHub Agent 命令行工具
支持 Agent 管理、任务触发、定时任务、报警等操作

注意: Agent 注册应使用 probehub_agent SDK (TaskAgent.start())
     CLI 只提供查询、管理和本地服务启动功能

使用方式:
    # 健康检查
    python3 probehub_cli.py health
    
    # 启动本地 Agent 服务（推荐）
    python3 probehub_cli.py serve --puid "xxx" --port 8088
    
    # 触发任务
    python3 probehub_cli.py trigger --agent-id "xxx" --task-name "test_task"
    
    # 创建定时任务
    python3 probehub_cli.py create-schedule --agent-id "xxx" --task-name "task1" --cron "0 9 * * *"
"""

import sys
import os
import argparse
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import ProbeHubManager, ProbeHubClient


def cmd_health(args):
    """健康检查"""
    try:
        result = ProbeHubManager.health(args.base_url)
        print("✅ 服务健康")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return 1


def cmd_register(args):
    """注册并启动 Agent（使用 SDK）"""
    try:
        from probehub_agent import TaskAgent
    except ImportError:
        print("❌ 需要安装 probehub-agent:")
        print("   pip3 install probehub-agent -i http://pip.baidu-int.com/simple/ --trusted-host pip.baidu-int.com")
        return 1
    
    puid = args.puid or os.environ.get("PROBEHUB_PUID")
    if not puid:
        print("❌ 请提供 --puid 参数或设置环境变量 PROBEHUB_PUID")
        return 1
    
    # 获取服务地址（使用 VIP 地址）
    base_url = args.base_url or os.environ.get("PROBEHUB_BASE_URL", "http://10.11.153.54:8001")
    
    print(f"🚀 注册并启动 ProbeHub Agent...")
    print(f"   名称: {args.name}")
    print(f"   PUID: {puid[:8]}...")
    print(f"   服务: {base_url}")
    print(f"   地址: {args.host}:{args.port}")
    
    # 创建 Agent 实例，必须传入 service_url
    agent = TaskAgent(puid=puid, service_url=base_url)
    
    # 如果指定了任务模块，尝试导入
    if args.task_module:
        try:
            import importlib
            module = importlib.import_module(args.task_module)
            print(f"   任务模块: {args.task_module}")
        except ImportError as e:
            print(f"⚠️  无法导入任务模块 {args.task_module}: {e}")
    
    # 注册默认任务
    @agent.task_decorator(description="健康检查任务", tag="system")
    def health_check(params=None):
        return {"status": "healthy", "message": "Agent is running", "name": args.name}
    
    print("   已注册任务: health_check")
    print("-" * 40)
    print("   Agent 启动后会自动向 ProbeHub 注册")
    print("   按 Ctrl+C 停止服务")
    print("=" * 40)
    
    try:
        agent.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n👋 Agent 已停止")
    
    return 0


def cmd_list_agents(args):
    """获取 Agent 列表"""
    try:
        agents = ProbeHubManager.list_agents()
        
        if not agents:
            print("📋 暂无 Agent")
            return 0
        
        print(f"📋 Agent 列表 ({len(agents)} 个):")
        print("-" * 60)
        for agent in agents:
            agent_id = agent.get("id") or agent.get("agent_id")
            name = agent.get("name", "未命名")
            status = agent.get("status", "unknown")
            print(f"  {agent_id[:16]}... | {name:20s} | {status}")
        print("-" * 60)
        
        if args.verbose:
            print("\n完整数据:")
            print(json.dumps(agents, ensure_ascii=False, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ 获取列表失败: {e}")
        return 1


def cmd_heartbeat(args):
    """发送心跳"""
    try:
        result = ProbeHubManager.heartbeat(args.agent_id)
        print(f"✅ 心跳发送成功: {args.agent_id}")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 心跳发送失败: {e}")
        return 1


def cmd_delete_agent(args):
    """删除 Agent"""
    try:
        result = ProbeHubManager.delete_agent(args.agent_id)
        print(f"✅ Agent 已删除: {args.agent_id}")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return 1


def cmd_trigger(args):
    """触发任务执行"""
    try:
        params = json.loads(args.params) if args.params else None
        allow_alarm = not getattr(args, 'no_alarm', False)
        result = ProbeHubManager.trigger_task(
            task_name=args.task_name,
            agent_id=args.agent_id,
            params=params,
            allow_alarm=allow_alarm
        )
        
        execution_id = result.get("execution_id") or result.get("id")
        print("✅ 任务触发成功")
        print(f"  任务名: {args.task_name}")
        print(f"  执行 ID: {execution_id}")
        
        if args.verbose:
            print("\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0
    except json.JSONDecodeError:
        print(f"❌ 参数格式错误，请提供有效的 JSON: {args.params}")
        return 1
    except Exception as e:
        print(f"❌ 触发失败: {e}")
        return 1


def cmd_batch_trigger(args):
    """批量触发任务"""
    try:
        params = json.loads(args.params) if args.params else None
        result = ProbeHubManager.batch_trigger(tag=args.tag, params=params)
        
        triggered = result.get("triggered", result.get("tasks", []))
        success_count = len([t for t in triggered if t.get("status") == "success"]) if isinstance(triggered, list) else result.get("success", 0)
        fail_count = len(triggered) - success_count if isinstance(triggered, list) else result.get("failed", 0)
        
        print(f"✅ 批量触发完成 (tag={args.tag})")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {fail_count} 个")
        
        if args.verbose:
            print("\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0
    except json.JSONDecodeError:
        print(f"❌ 参数格式错误，请提供有效的 JSON: {args.params}")
        return 1
    except Exception as e:
        print(f"❌ 批量触发失败: {e}")
        return 1


def cmd_task_log(args):
    """获取任务执行日志"""
    try:
        result = ProbeHubManager.get_task_log(args.execution_id)
        
        log_content = result.get("log") or result.get("logs") or result.get("output", "")
        status = result.get("status", "unknown")
        
        print(f"📋 任务执行日志 (execution_id: {args.execution_id})")
        print(f"   状态: {status}")
        print("-" * 60)
        print(log_content)
        print("-" * 60)
        
        if args.verbose:
            print("\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ 获取日志失败: {e}")
        return 1


def cmd_task_results(args):
    """查询任务执行结果"""
    try:
        tasks = ProbeHubManager.get_task_results(args.agent_id)
        
        if not tasks:
            print(f"📋 Agent {args.agent_id} 暂无任务记录")
            return 0
        
        print(f"📋 任务执行结果 ({len(tasks)} 条):")
        print("-" * 70)
        for task in tasks[:20]:  # 最多显示20条
            name = task.get("task_name", task.get("name", "未知"))
            status = task.get("status", "unknown")
            exec_id = task.get("execution_id", task.get("id", ""))[:16]
            print(f"  {exec_id}... | {name:25s} | {status}")
        
        if len(tasks) > 20:
            print(f"  ... 还有 {len(tasks) - 20} 条记录")
        print("-" * 70)
        
        if args.verbose:
            print("\n完整数据:")
            print(json.dumps(tasks, ensure_ascii=False, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        return 1


def cmd_list_schedules(args):
    """获取定时任务列表"""
    try:
        schedules = ProbeHubManager.list_schedules(args.agent_id)
        
        if not schedules:
            print(f"📅 Agent {args.agent_id} 暂无定时任务")
            return 0
        
        print(f"📅 定时任务列表 ({len(schedules)} 个):")
        print("-" * 80)
        for sch in schedules:
            sch_id = str(sch.get("id") or sch.get("schedule_id") or sch.get("job_id", ""))
            task_name = sch.get("task_name", "未知")
            cron = sch.get("cron_expression") or sch.get("cron", "")
            status = sch.get("status", "unknown")
            print(f"  {sch_id:16s} | {task_name:20s} | {cron:15s} | {status}")
        print("-" * 80)
        
        if args.verbose:
            print("\n完整数据:")
            print(json.dumps(schedules, ensure_ascii=False, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ 获取列表失败: {e}")
        return 1


def cmd_create_schedule(args):
    """创建定时任务"""
    try:
        params = json.loads(args.params) if args.params else None
        
        # 根据参数确定调度类型
        schedule_type = args.schedule_type or "cron"
        cron_expression = args.cron if schedule_type == "cron" else None
        interval_seconds = args.interval if schedule_type == "interval" else None
        
        result = ProbeHubManager.create_schedule(
            agent_id=args.agent_id,
            task_name=args.task_name,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            params=params
        )
        
        job_id = result.get("job_id") or result.get("id")
        print("✅ 定时任务创建成功")
        print(f"  Job ID: {job_id}")
        print(f"  任务名: {args.task_name}")
        print(f"  调度类型: {schedule_type}")
        if cron_expression:
            print(f"  Cron: {cron_expression}")
        if interval_seconds:
            print(f"  间隔: {interval_seconds} 秒")
        
        if args.verbose:
            print("\n完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0
    except json.JSONDecodeError:
        print(f"❌ 参数格式错误，请提供有效的 JSON: {args.params}")
        return 1
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return 1


def cmd_pause_schedule(args):
    """暂停定时任务"""
    try:
        result = ProbeHubManager.pause_schedule(args.agent_id, args.schedule_id)
        print(f"✅ 定时任务已暂停: {args.schedule_id}")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 暂停失败: {e}")
        return 1


def cmd_resume_schedule(args):
    """恢复定时任务"""
    try:
        result = ProbeHubManager.resume_schedule(args.agent_id, args.schedule_id)
        print(f"✅ 定时任务已恢复: {args.schedule_id}")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 恢复失败: {e}")
        return 1


def cmd_delete_schedule(args):
    """删除定时任务"""
    try:
        result = ProbeHubManager.delete_schedule(args.agent_id, args.schedule_id)
        print(f"✅ 定时任务已删除: {args.schedule_id}")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        return 1


def cmd_alarm_config(args):
    """获取/设置报警配置"""
    try:
        if args.set_config:
            config = json.loads(args.set_config)
            result = ProbeHubManager.save_alarm_config(config)
            print("✅ 报警配置已保存")
        else:
            result = ProbeHubManager.get_alarm_config()
            print("📢 报警配置:")
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except json.JSONDecodeError:
        print(f"❌ 配置格式错误，请提供有效的 JSON")
        return 1
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return 1


def cmd_alarm_test(args):
    """测试报警渠道"""
    try:
        channel_config = json.loads(args.channel) if args.channel else {"type": "default"}
        result = ProbeHubManager.test_alarm(channel_config)
        print("✅ 报警测试已发送")
        if args.verbose:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except json.JSONDecodeError:
        print(f"❌ 渠道配置格式错误，请提供有效的 JSON")
        return 1
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1


def cmd_alarm_history(args):
    """获取报警历史"""
    try:
        history = ProbeHubManager.get_alarm_history()
        
        if not history:
            print("📢 暂无报警记录")
            return 0
        
        print(f"📢 报警历史 ({len(history)} 条):")
        print("-" * 70)
        for item in history[:20]:
            time = item.get("time", item.get("created_at", ""))[:19]
            level = item.get("level", "info")
            msg = item.get("message", "")[:40]
            print(f"  {time} | {level:8s} | {msg}")
        
        if len(history) > 20:
            print(f"  ... 还有 {len(history) - 20} 条记录")
        print("-" * 70)
        
        if args.verbose:
            print("\n完整数据:")
            print(json.dumps(history, ensure_ascii=False, indent=2))
        
        return 0
    except Exception as e:
        print(f"❌ 获取历史失败: {e}")
        return 1


def cmd_serve(args):
    """启动本地 Agent 服务"""
    try:
        from probehub_agent import TaskAgent
    except ImportError:
        print("❌ 需要安装 probehub-agent:")
        print("   pip3 install probehub-agent -i http://pip.baidu-int.com/simple/ --trusted-host pip.baidu-int.com")
        return 1
    
    puid = args.puid or os.environ.get("PROBEHUB_PUID")
    if not puid:
        print("❌ 请提供 --puid 参数或设置环境变量 PROBEHUB_PUID")
        return 1
    
    # 获取服务地址（使用 VIP 地址）
    base_url = args.base_url or os.environ.get("PROBEHUB_BASE_URL", "http://10.11.153.54:8001")
    
    print(f"🚀 启动 ProbeHub Agent...")
    print(f"   PUID: {puid[:8]}...")
    print(f"   服务: {base_url}")
    print(f"   地址: {args.host}:{args.port}")
    
    # 创建 Agent 实例，必须传入 service_url
    agent = TaskAgent(puid=puid, service_url=base_url)
    
    # 如果指定了任务模块，尝试导入
    if args.task_module:
        try:
            import importlib
            module = importlib.import_module(args.task_module)
            print(f"   任务模块: {args.task_module}")
        except ImportError as e:
            print(f"⚠️  无法导入任务模块 {args.task_module}: {e}")
    
    # 注册示例任务
    @agent.task_decorator(description="健康检查任务", tag="system")
    def health_check():
        return {"status": "healthy", "message": "Agent is running"}
    
    print("   已注册任务: health_check")
    print("-" * 40)
    
    try:
        agent.start(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n👋 Agent 已停止")
    
    return 0


def cmd_generate_template(args):
    """生成 Agent 代码模板"""
    template = '''#!/usr/bin/env python3
"""
ProbeHub Agent 示例
自动生成于 probehub_cli.py

使用方式:
  1. 修改 PUID 为你的项目密钥
  2. 修改 SERVICE_URL 为 ProbeHub 服务地址
  3. 添加你的任务函数
  4. 运行: python3 my_agent.py
"""
import os
from probehub_agent import TaskAgent

# 配置（从环境变量获取或直接填写）
PUID = os.environ.get("PROBEHUB_PUID", "your-puid-here")
SERVICE_URL = os.environ.get("PROBEHUB_BASE_URL", "http://10.11.153.54:8001")

# 创建 Agent 实例（必须传入 service_url）
agent = TaskAgent(puid=PUID, service_url=SERVICE_URL)


# 方式 1: 装饰器注册任务
@agent.task_decorator(description="示例任务1", tag="example")
def task_example_1(params=None):
    """
    示例任务1
    
    Args:
        params: 任务参数（字典）
    
    Returns:
        任务结果
    """
    print(f"执行任务1，参数: {params}")
    # 在这里编写你的业务逻辑
    return {"status": "success", "data": "task1 completed"}


@agent.task_decorator(description="示例任务2", tag="example")
def task_example_2(params=None):
    """示例任务2"""
    print(f"执行任务2，参数: {params}")
    return {"status": "success", "data": "task2 completed"}


# 方式 2: 注册已有函数
def existing_function(params=None):
    """已有的函数"""
    return {"status": "success"}

# agent.task_decorator(existing_function, description="已有函数", tag="legacy")


if __name__ == "__main__":
    print("🚀 启动 ProbeHub Agent...")
    print(f"   PUID: {PUID[:8]}...")
    print(f"   服务: {SERVICE_URL}")
    
    # 启动 Agent，监听指定端口
    # Agent 启动后会自动向 ProbeHub 注册
    agent.start(host="0.0.0.0", port=8088)
'''
    
    output_path = args.output or "my_agent.py"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"✅ Agent 模板已生成: {output_path}")
    print("\n使用方式:")
    print(f"  1. 编辑 {output_path}，添加你的任务")
    print(f"  2. 设置环境变量: export PROBEHUB_PUID='your-puid'")
    print(f"  3. 运行: python3 {output_path}")
    
    return 0


def main():
    # 创建主解析器
    parser = argparse.ArgumentParser(
        description='ProbeHub Agent 命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 健康检查
  python3 probehub_cli.py health
  
  # 启动本地 Agent（推荐）
  python3 probehub_cli.py serve --puid "xxx" --port 8088
  
  # 触发任务
  python3 probehub_cli.py trigger --agent-id "xxx" --task-name "test"
  
  # 创建定时任务
  python3 probehub_cli.py create-schedule --agent-id "xxx" --task-name "task1" --cron "0 9 * * *"
  
  # 生成 Agent 模板
  python3 probehub_cli.py generate-template --output my_agent.py

环境变量:
  PROBEHUB_PUID      项目密钥
  PROBEHUB_BASE_URL  服务地址 (默认: http://10.11.153.54:8001)
        """
    )
    
    # 全局参数
    parser.add_argument('--base-url', help='ProbeHub 服务地址')
    parser.add_argument('--puid', help='项目密钥（用于注册、触发等操作）')
    parser.add_argument('--project-id', help='项目ID（用于查询操作）')
    parser.add_argument('--timeout', type=int, default=30, help='请求超时（秒）')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # health 命令
    p_health = subparsers.add_parser('health', help='健康检查')
    p_health.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # register 命令 - 使用 SDK 注册并启动 Agent
    p_register = subparsers.add_parser('register', help='注册并启动 Agent（使用 SDK）')
    p_register.add_argument('--name', '-n', required=True, help='Agent 名称')
    p_register.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    p_register.add_argument('--port', type=int, default=8088, help='监听端口 (默认: 8088)')
    p_register.add_argument('--task-module', help='任务模块路径（可选）')
    p_register.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # list-agents 命令
    p_list_agents = subparsers.add_parser('list-agents', help='获取 Agent 列表')
    p_list_agents.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # heartbeat 命令
    p_heartbeat = subparsers.add_parser('heartbeat', help='发送心跳')
    p_heartbeat.add_argument('--agent-id', required=True, help='Agent ID')
    p_heartbeat.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # delete-agent 命令
    p_delete_agent = subparsers.add_parser('delete-agent', help='删除 Agent')
    p_delete_agent.add_argument('--agent-id', required=True, help='Agent ID')
    p_delete_agent.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # trigger 命令
    p_trigger = subparsers.add_parser('trigger', help='触发任务执行')
    p_trigger.add_argument('--task-name', required=True, help='任务名称')
    p_trigger.add_argument('--agent-id', required=True, help='Agent ID（必填）')
    p_trigger.add_argument('--params', '-p', help='任务参数（JSON 格式）')
    p_trigger.add_argument('--no-alarm', action='store_true', help='禁用报警')
    p_trigger.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # batch-trigger 命令
    p_batch_trigger = subparsers.add_parser('batch-trigger', help='批量触发任务')
    p_batch_trigger.add_argument('--tag', required=True, help='任务标签')
    p_batch_trigger.add_argument('--params', '-p', help='任务参数（JSON 格式）')
    p_batch_trigger.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # task-log 命令
    p_task_log = subparsers.add_parser('task-log', help='获取任务执行日志')
    p_task_log.add_argument('--execution-id', required=True, help='执行 ID')
    p_task_log.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # task-results 命令
    p_task_results = subparsers.add_parser('task-results', help='查询任务执行结果')
    p_task_results.add_argument('--agent-id', required=True, help='Agent ID')
    p_task_results.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # list-schedules 命令
    p_list_schedules = subparsers.add_parser('list-schedules', help='获取定时任务列表')
    p_list_schedules.add_argument('--agent-id', required=True, help='Agent ID')
    p_list_schedules.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # create-schedule 命令
    p_create_schedule = subparsers.add_parser('create-schedule', help='创建定时任务')
    p_create_schedule.add_argument('--agent-id', required=True, help='Agent ID')
    p_create_schedule.add_argument('--task-name', required=True, help='任务名称')
    p_create_schedule.add_argument('--schedule-type', choices=['cron', 'interval'], default='cron', help='调度类型 (默认: cron)')
    p_create_schedule.add_argument('--cron', help='Cron 表达式 (schedule_type=cron 时使用)')
    p_create_schedule.add_argument('--interval', type=int, help='间隔秒数 (schedule_type=interval 时使用)')
    p_create_schedule.add_argument('--params', '-p', help='任务参数（JSON 格式）')
    p_create_schedule.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # pause-schedule 命令
    p_pause_schedule = subparsers.add_parser('pause-schedule', help='暂停定时任务')
    p_pause_schedule.add_argument('--agent-id', required=True, help='Agent ID')
    p_pause_schedule.add_argument('--schedule-id', required=True, help='定时任务 ID')
    p_pause_schedule.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # resume-schedule 命令
    p_resume_schedule = subparsers.add_parser('resume-schedule', help='恢复定时任务')
    p_resume_schedule.add_argument('--agent-id', required=True, help='Agent ID')
    p_resume_schedule.add_argument('--schedule-id', required=True, help='定时任务 ID')
    p_resume_schedule.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # delete-schedule 命令
    p_delete_schedule = subparsers.add_parser('delete-schedule', help='删除定时任务')
    p_delete_schedule.add_argument('--agent-id', required=True, help='Agent ID')
    p_delete_schedule.add_argument('--schedule-id', required=True, help='定时任务 ID')
    p_delete_schedule.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # alarm-config 命令
    p_alarm_config = subparsers.add_parser('alarm-config', help='获取/设置报警配置')
    p_alarm_config.add_argument('--set-config', help='设置配置（JSON 格式）')
    p_alarm_config.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # alarm-test 命令
    p_alarm_test = subparsers.add_parser('alarm-test', help='测试报警渠道')
    p_alarm_test.add_argument('--channel', help='渠道配置（JSON 格式）')
    p_alarm_test.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # alarm-history 命令
    p_alarm_history = subparsers.add_parser('alarm-history', help='获取报警历史')
    p_alarm_history.add_argument('-v', '--verbose', action='store_true', help='显示详细信息')
    
    # serve 命令
    p_serve = subparsers.add_parser('serve', help='启动本地 Agent 服务')
    p_serve.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    p_serve.add_argument('--port', type=int, default=8088, help='监听端口 (默认: 8088)')
    p_serve.add_argument('--task-module', help='任务模块路径')
    
    # generate-template 命令
    p_generate = subparsers.add_parser('generate-template', help='生成 Agent 代码模板')
    p_generate.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # 设置全局配置
    if args.base_url or args.puid or args.project_id:
        ProbeHubManager.set_config(
            base_url=args.base_url,
            puid=args.puid,
            project_id=args.project_id
        )
    
    # 执行对应命令
    commands = {
        'health': cmd_health,
        'register': cmd_register,
        'list-agents': cmd_list_agents,
        'heartbeat': cmd_heartbeat,
        'delete-agent': cmd_delete_agent,
        'trigger': cmd_trigger,
        'batch-trigger': cmd_batch_trigger,
        'task-log': cmd_task_log,
        'task-results': cmd_task_results,
        'list-schedules': cmd_list_schedules,
        'create-schedule': cmd_create_schedule,
        'pause-schedule': cmd_pause_schedule,
        'resume-schedule': cmd_resume_schedule,
        'delete-schedule': cmd_delete_schedule,
        'alarm-config': cmd_alarm_config,
        'alarm-test': cmd_alarm_test,
        'alarm-history': cmd_alarm_history,
        'serve': cmd_serve,
        'generate-template': cmd_generate_template,
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())