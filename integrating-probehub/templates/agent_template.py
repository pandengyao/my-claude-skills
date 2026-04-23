#!/usr/bin/env python3
"""
ProbeHub Agent 模板
用于快速创建本地 Agent 服务

使用方式:
    1. 复制此文件到你的项目
    2. 修改 PUID 为你的项目密钥
    3. 添加你的任务函数
    4. 运行: python3 agent_template.py
"""
import os
import time
import json
from datetime import datetime

# 尝试导入 probehub_agent
try:
    from probehub_agent import TaskAgent
except ImportError:
    print("❌ 请先安装 probehub-agent:")
    print("   pip3 install probehub-agent -i http://pip.baidu-int.com/simple/ --trusted-host pip.baidu-int.com")
    exit(1)

# ============================================================
# 配置区域 - 请根据实际情况修改
# ============================================================

# 项目密钥（从 https://probehub.now.baidu-int.com/ 获取）
PUID = os.environ.get("PROBEHUB_PUID", "your-project-puid")

# Agent 监听配置
HOST = "0.0.0.0"
PORT = 8088

# ============================================================
# Agent 实例
# ============================================================

agent = TaskAgent(puid=PUID)

# ============================================================
# 任务定义区域 - 在这里添加你的任务
# ============================================================


@agent.task_decorator(description="健康检查", tag="system")
def health_check(params=None):
    """
    系统健康检查任务
    
    Returns:
        健康状态信息
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Agent is running normally"
    }


@agent.task_decorator(description="数据处理任务", tag="data")
def process_data(params=None):
    """
    数据处理任务示例
    
    Args:
        params: 任务参数，包含:
            - data_source: 数据来源
            - output_path: 输出路径
            - options: 处理选项
    
    Returns:
        处理结果
    """
    params = params or {}
    data_source = params.get("data_source", "default")
    
    print(f"[{datetime.now()}] 开始处理数据: {data_source}")
    
    # 模拟数据处理
    time.sleep(2)
    
    result = {
        "status": "success",
        "source": data_source,
        "processed_count": 100,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"[{datetime.now()}] 数据处理完成: {result}")
    return result


@agent.task_decorator(description="报告生成任务", tag="report")
def generate_report(params=None):
    """
    报告生成任务示例
    
    Args:
        params: 任务参数，包含:
            - report_type: 报告类型 (daily/weekly/monthly)
            - date_range: 日期范围
    
    Returns:
        报告信息
    """
    params = params or {}
    report_type = params.get("report_type", "daily")
    
    print(f"[{datetime.now()}] 生成 {report_type} 报告...")
    
    # 模拟报告生成
    time.sleep(1)
    
    report_path = f"/tmp/report_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return {
        "status": "success",
        "report_type": report_type,
        "report_path": report_path,
        "generated_at": datetime.now().isoformat()
    }


@agent.task_decorator(description="清理任务", tag="maintenance")
def cleanup(params=None):
    """
    定期清理任务
    
    Args:
        params: 任务参数，包含:
            - target: 清理目标
            - days: 保留天数
    
    Returns:
        清理结果
    """
    params = params or {}
    target = params.get("target", "temp_files")
    days = params.get("days", 7)
    
    print(f"[{datetime.now()}] 清理 {target}，保留 {days} 天...")
    
    # 模拟清理操作
    cleaned_count = 42
    freed_space = "1.2GB"
    
    return {
        "status": "success",
        "target": target,
        "cleaned_count": cleaned_count,
        "freed_space": freed_space,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================
# 启动 Agent
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ProbeHub Agent 启动中...")
    print("=" * 60)
    print(f"   PUID: {PUID[:16]}...")
    print(f"   监听: {HOST}:{PORT}")
    print("-" * 60)
    print("   已注册任务:")
    print("     • health_check (tag: system)")
    print("     • process_data (tag: data)")
    print("     • generate_report (tag: report)")
    print("     • cleanup (tag: maintenance)")
    print("-" * 60)
    print("   按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        agent.start(host=HOST, port=PORT)
    except KeyboardInterrupt:
        print("\n👋 Agent 已停止")