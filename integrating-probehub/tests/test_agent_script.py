#!/usr/bin/env python3
"""
测试 Agent 脚本 - 使用 probehub_agent SDK
用于验证完整的 Agent 启动和任务执行流程

使用方式:
  1. 设置环境变量或修改下方配置
  2. 运行: python3 tests/test_agent_script.py
  3. Agent 启动后会自动向 ProbeHub 注册
  4. 可以通过 CLI 触发任务: 
     python3 scripts/probehub_cli.py trigger --agent-id "xxx" --task-name "health_check"
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from probehub_agent import TaskAgent

# 配置（从环境变量获取或使用默认值）
PUID = os.environ.get("PROBEHUB_PUID", "6AF58-A3A32-BEA42-85AF4")
SERVICE_URL = os.environ.get("PROBEHUB_BASE_URL", "http://10.11.153.54:8001")
HOST = os.environ.get("PROBEHUB_AGENT_HOST", "0.0.0.0")
PORT = int(os.environ.get("PROBEHUB_AGENT_PORT", "18088"))

# 创建 Agent 实例（必须传入 service_url）
agent = TaskAgent(puid=PUID, service_url=SERVICE_URL)


@agent.task_decorator(description="健康检查任务", tag="test")
def health_check(params=None):
    """健康检查任务"""
    print("执行健康检查...")
    return {"status": "healthy", "message": "Agent 运行正常"}


@agent.task_decorator(description="测试任务", tag="test")
def test_task(params=None):
    """测试任务"""
    print(f"执行测试任务，参数: {params}")
    return {"status": "success", "params": params}


@agent.task_decorator(description="数据处理任务", tag="data")
def process_data(params=None):
    """数据处理任务示例"""
    data_count = params.get("count", 100) if params else 100
    print(f"处理 {data_count} 条数据...")
    return {"status": "success", "processed": data_count}


if __name__ == "__main__":
    print("🚀 启动 ProbeHub Agent...")
    print(f"   PUID: {PUID[:8]}...")
    print(f"   服务: {SERVICE_URL}")
    print(f"   地址: {HOST}:{PORT}")
    print(f"   已注册任务: health_check, test_task, process_data")
    print("-" * 40)
    
    # Agent 启动后会自动向 ProbeHub 注册
    agent.start(host=HOST, port=PORT)