"""
ProbeHub 管理器（工厂模式）
统一管理 ProbeHub 相关操作
"""

import os
from typing import Any, Dict, List, Optional

from .client import ProbeHubClient


class ProbeHubManager:
    """ProbeHub 管理器（工厂模式）"""
    
    _client: Optional[ProbeHubClient] = None
    _default_base_url = "http://10.11.153.54:8001"
    
    @classmethod
    def _ensure_client(cls, base_url: Optional[str] = None, puid: Optional[str] = None, project_id: Optional[str] = None):
        """确保客户端已初始化"""
        if cls._client is None or base_url or puid or project_id:
            cls._client = ProbeHubClient(
                base_url=base_url or os.environ.get("PROBEHUB_BASE_URL", cls._default_base_url),
                puid=puid or os.environ.get("PROBEHUB_PUID"),
                project_id=project_id or os.environ.get("PROBEHUB_PROJECT_ID")
            )
        return cls._client
    
    @classmethod
    def set_config(cls, base_url: Optional[str] = None, puid: Optional[str] = None, project_id: Optional[str] = None):
        """设置全局配置"""
        cls._client = ProbeHubClient(base_url=base_url, puid=puid, project_id=project_id)
    
    @classmethod
    def get_client(cls) -> ProbeHubClient:
        """获取客户端实例"""
        return cls._ensure_client()
    
    # ========== 健康检查 ==========
    
    @classmethod
    def health(cls, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        健康检查
        
        Args:
            base_url: ProbeHub 服务地址（可选）
            
        Returns:
            健康状态信息
        """
        client = cls._ensure_client(base_url=base_url)
        return client.health()
    
    # ========== Agent 管理 ==========
    # 注意: Agent 注册应使用 probehub_agent SDK (TaskAgent.start())
    # 此处只提供查询和管理 API
    
    @classmethod
    def list_agents(cls, **params) -> List[Dict[str, Any]]:
        """
        获取 Agent 列表
        
        Returns:
            Agent 列表
        """
        client = cls._ensure_client()
        result = client.list_agents(**params)
        return result.get("agents", result.get("data", []))
    
    @classmethod
    def heartbeat(cls, agent_id: str) -> Dict[str, Any]:
        """
        发送心跳
        
        Args:
            agent_id: Agent ID
            
        Returns:
            心跳响应
        """
        client = cls._ensure_client()
        return client.heartbeat(agent_id)
    
    @classmethod
    def delete_agent(cls, agent_id: str) -> Dict[str, Any]:
        """
        删除 Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            删除结果
        """
        client = cls._ensure_client()
        return client.delete_agent(agent_id)
    
    # ========== 任务管理 ==========
    
    @classmethod
    def trigger_task(
        cls,
        task_name: str,
        agent_id: str,
        params: Optional[Dict] = None,
        allow_alarm: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        触发任务执行
        
        Args:
            task_name: 任务名称
            agent_id: Agent ID（必填）
            params: 任务参数
            allow_alarm: 是否允许报警
            
        Returns:
            执行结果，包含 execution_id
        """
        client = cls._ensure_client()
        return client.trigger_task(task_name, agent_id, params, allow_alarm, **kwargs)
    
    @classmethod
    def batch_trigger(
        cls,
        tag: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        批量触发任务
        
        Args:
            tag: 任务标签
            params: 任务参数
            
        Returns:
            批量触发结果
        """
        client = cls._ensure_client()
        return client.batch_trigger(tag, params, **kwargs)
    
    @classmethod
    def get_task_log(cls, execution_id: str) -> Dict[str, Any]:
        """
        获取任务执行日志
        
        Args:
            executi on_id: 执行 ID
            
        Returns:
            执行日志
        """
        client = cls._ensure_client()
        return client.get_task_log(execution_id)
    
    @classmethod
    def get_task_results(cls, agent_id: str, **params) -> List[Dict[str, Any]]:
        """
        获取 Agent 的任务执行结果
        
        Args:
            agent_id: Agent ID
            
        Returns:
            任务结果列表
        """
        client = cls._ensure_client()
        result = client.get_task_results(agent_id, **params)
        return result.get("tasks", result.get("data", []))
    
    # ========== 定时任务 ==========
    
    @classmethod
    def list_schedules(cls, agent_id: str) -> List[Dict[str, Any]]:
        """
        获取 Agent 的定时任务列表
        
        Args:
            agent_id: Agent ID
            
        Returns:
            定时任务列表
        """
        client = cls._ensure_client()
        result = client.list_schedules(agent_id)
        return result.get("schedules", result.get("data", []))
    
    @classmethod
    def create_schedule(
        cls,
        agent_id: str,
        task_name: str,
        schedule_type: str = "cron",
        cron_expression: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建定时任务
        
        Args:
            agent_id: Agent ID
            task_name: 任务名称
            schedule_type: 调度类型 (cron/interval)
            cron_expression: Cron 表达式 (schedule_type=cron 时必填，如: 0 9 * * *)
            interval_seconds: 间隔秒数 (schedule_type=interval 时必填)
            params: 任务参数
            
        Returns:
            创建结果，包含 job_id
        """
        client = cls._ensure_client()
        return client.create_schedule(
            agent_id, task_name, schedule_type, cron_expression, interval_seconds, params, **kwargs
        )
    
    @classmethod
    def pause_schedule(cls, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """
        暂停定时任务
        
        Args:
            agent_id: Agent ID
            schedule_id: 定时任务 ID
            
        Returns:
            操作结果
        """
        client = cls._ensure_client()
        return client.pause_schedule(agent_id, schedule_id)
    
    @classmethod
    def resume_schedule(cls, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """
        恢复定时任务
        
        Args:
            agent_id: Agent ID
            schedule_id: 定时任务 ID
            
        Returns:
            操作结果
        """
        client = cls._ensure_client()
        return client.resume_schedule(agent_id, schedule_id)
    
    @classmethod
    def delete_schedule(cls, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """
        删除定时任务
        
        Args:
            agent_id: Agent ID
            schedule_id: 定时任务 ID
            
        Returns:
            操作结果
        """
        client = cls._ensure_client()
        return client.delete_schedule(agent_id, schedule_id)
    
    # ========== 报警管理 ==========
    
    @classmethod
    def get_alarm_config(cls) -> Dict[str, Any]:
        """获取报警配置"""
        client = cls._ensure_client()
        return client.get_alarm_config()
    
    @classmethod
    def save_alarm_config(cls, config: Dict) -> Dict[str, Any]:
        """保存报警配置"""
        client = cls._ensure_client()
        return client.save_alarm_config(config)
    
    @classmethod
    def test_alarm(cls, channel_config: Dict) -> Dict[str, Any]:
        """测试报警渠道"""
        client = cls._ensure_client()
        return client.test_alarm(channel_config)
    
    @classmethod
    def get_alarm_history(cls, **params) -> List[Dict[str, Any]]:
        """获取报警历史"""
        client = cls._ensure_client()
        result = client.get_alarm_history(**params)
        return result.get("history", result.get("data", []))
    
    @classmethod
    def get_alarm_stats(cls) -> Dict[str, Any]:
        """获取报警统计"""
        client = cls._ensure_client()
        return client.get_alarm_stats()
    
    # ========== 项目管理 ==========
    
    @classmethod
    def list_projects(cls, **params) -> List[Dict[str, Any]]:
        """获取项目列表"""
        client = cls._ensure_client()
        result = client.list_projects(**params)
        return result.get("projects", result.get("data", []))
    
    @classmethod
    def get_project(cls, project_id: str) -> Dict[str, Any]:
        """获取单个项目"""
        client = cls._ensure_client()
        return client.get_project(project_id)
    
    @classmethod
    def create_project(cls, name: str, description: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """创建新项目"""
        client = cls._ensure_client()
        data = {"name": name}
        if description:
            data["description"] = description
        data.update(kwargs)
        return client.create_project(data)
    
    @classmethod
    def update_project(cls, project_id: str, **kwargs) -> Dict[str, Any]:
        """更新项目"""
        client = cls._ensure_client()
        return client.update_project(project_id, kwargs)
    
    @classmethod
    def delete_project(cls, project_id: str) -> Dict[str, Any]:
        """删除项目"""
        client = cls._ensure_client()
        return client.delete_project(project_id)
    
    # ========== 便捷方法 ==========
    
    @classmethod
    def get_agent_status(cls, agent_id: str) -> Dict[str, Any]:
        """
        获取 Agent 完整状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            包含 Agent 信息、任务和定时任务的完整状态
        """
        client = cls._ensure_client()
        
        # 获取任务结果
        tasks = cls.get_task_results(agent_id)
        
        # 获取定时任务
        schedules = cls.list_schedules(agent_id)
        
        return {
            "agent_id": agent_id,
            "tasks": tasks,
            "schedules": schedules,
            "task_count": len(tasks),
            "schedule_count": len(schedules)
        }