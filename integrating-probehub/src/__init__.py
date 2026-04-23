"""
ProbeHub Agent Integration
提供 ProbeHub 接入、Agent 管理、任务调度等功能
"""

from .client import ProbeHubClient
from .manager import ProbeHubManager

__all__ = [
    "ProbeHubClient",
    "ProbeHubManager",
]

# 便捷函数
# 注意: Agent 注册应使用 probehub_agent SDK (TaskAgent.start())

def health(base_url=None):
    """健康检查"""
    return ProbeHubManager.health(base_url)

def list_agents(**params):
    """获取 Agent 列表"""
    return ProbeHubManager.list_agents(**params)

def trigger_task(task_name, agent_id, params=None, allow_alarm=True, **kwargs):
    """触发任务
    
    Args:
        task_name: 任务名称
        agent_id: Agent ID（必填）
        params: 任务参数
        allow_alarm: 是否允许报警
    """
    return ProbeHubManager.trigger_task(task_name, agent_id, params, allow_alarm, **kwargs)

def batch_trigger(tag, params=None, **kwargs):
    """批量触发任务"""
    return ProbeHubManager.batch_trigger(tag, params, **kwargs)

def create_schedule(agent_id, task_name, schedule_type='cron', cron_expression=None, interval_seconds=None, params=None, **kwargs):
    """创建定时任务
    
    Args:
        agent_id: Agent ID
        task_name: 任务名称
        schedule_type: 调度类型 (cron/interval)
        cron_expression: Cron 表达式 (schedule_type=cron 时使用)
        interval_seconds: 间隔秒数 (schedule_type=interval 时使用)
        params: 任务参数
    """
    return ProbeHubManager.create_schedule(
        agent_id, task_name, schedule_type, cron_expression, interval_seconds, params, **kwargs
    )