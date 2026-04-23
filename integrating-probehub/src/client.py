"""
ProbeHub HTTP API 客户端
封装所有 API 调用
"""

import os
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    requests = None


class ProbeHubClient:
    """ProbeHub HTTP API 客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        puid: Optional[str] = None,
        project_id: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化客户端
        
        Args:
            base_url: ProbeHub 服务地址
            puid: 项目密钥（用于注册、触发等操作）
            project_id: 项目ID（用于查询操作）
            timeout: 请求超时时间（秒）
        """
        if requests is None:
            raise ImportError("需要安装 requests: pip install requests")
        
        self.base_url = base_url or os.environ.get(
            "PROBEHUB_BASE_URL", "http://10.11.153.54:8001"
        )
        self.puid = puid or os.environ.get("PROBEHUB_PUID")
        self.project_id = project_id or os.environ.get("PROBEHUB_PROJECT_ID")
        self.timeout = timeout
        
        # 确保 base_url 以 / 结尾
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.puid:
            headers["X-Project-Key"] = self.puid
        return headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            data: 请求体数据
            
        Returns:
            响应数据
        """
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data,
                timeout=self.timeout,
                **kwargs
            )
            
            # 检查响应状态
            if response.status_code == 401:
                raise PermissionError("认证失败，请检查 puid 是否正确")
            elif response.status_code == 404:
                raise ValueError(f"资源不存在: {endpoint}")
            elif response.status_code >= 400:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_data.get("error", error_msg))
                except Exception:
                    pass
                raise RuntimeError(f"API 错误 ({response.status_code}): {error_msg}")
            
            # 解析响应
            if response.text:
                return response.json()
            return {"status": "success"}
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时，请检查网络或增加 timeout（当前: {self.timeout}秒）")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接服务，请检查 base_url: {self.base_url}")
    
    # ========== 健康检查 ==========
    
    def health(self) -> Dict[str, Any]:
        """健康检查"""
        return self._request("GET", "/api/health")
    
    # ========== Agent 管理 ==========
    # 注意: Agent 注册应使用 probehub_agent SDK (TaskAgent.start())
    # 此处只提供查询和管理 API
    
    def list_agents(self, **params) -> Dict[str, Any]:
        """获取 Agent 列表（需要 project_id 查询参数）"""
        if self.project_id:
            params.setdefault("project_id", self.project_id)
        # 注意：puid 不能作为 project_id，它们是两个不同的概念
        return self._request("GET", "/api/agents", params=params)
    
    def heartbeat(self, agent_id: str) -> Dict[str, Any]:
        """发送心跳"""
        return self._request("POST", f"/api/agents/heartbeat/{agent_id}")
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """删除 Agent"""
        return self._request("DELETE", f"/api/agents/{agent_id}")
    
    # ========== 任务管理 ==========
    
    def trigger_task(
        self,
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
        """
        data = {
            "task_name": task_name,
            "agent_id": agent_id,
            "allow_alarm": allow_alarm,
        }
        if params:
            data["params"] = params
        data.update(kwargs)
        
        return self._request("POST", "/api/tasks/trigger", data=data)
    
    def batch_trigger(
        self,
        tag: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        批量触发任务
        
        Args:
            tag: 任务标签
            params: 任务参数
        """
        data = {
            "tag": tag,
        }
        # 服务端使用 project_id 来筛选 agent
        if self.project_id:
            data["project_id"] = self.project_id
        if params:
            data["params"] = params
        data.update(kwargs)
        
        return self._request("POST", "/api/tasks/batch_trigger", data=data)
    
    def get_task_log(self, execution_id: str) -> Dict[str, Any]:
        """获取任务执行日志"""
        return self._request("GET", f"/api/tasks/log/{execution_id}")
    
    def get_task_results(self, agent_id: str, **params) -> Dict[str, Any]:
        """获取 Agent 的任务执行结果"""
        return self._request("GET", f"/api/agents/{agent_id}/tasks", params=params)
    
    def submit_task_result(self, result_data: Dict) -> Dict[str, Any]:
        """提交任务结果"""
        return self._request("POST", "/api/tasks/results", data=result_data)
    
    def get_task_configs(self, agent_id: str) -> Dict[str, Any]:
        """获取代理的任务配置列表"""
        return self._request("GET", f"/api/tasks/configs/{agent_id}")
    
    def create_task_config(self, config_data: Dict) -> Dict[str, Any]:
        """下发任务配置"""
        return self._request("POST", "/api/tasks/config", data=config_data)
    
    def create_task(self, task_data: Dict) -> Dict[str, Any]:
        """创建新任务"""
        return self._request("POST", "/api/tasks/tasks_queue", data=task_data)
    
    # ========== 定时任务 ==========
    
    def list_schedules(self, agent_id: str) -> Dict[str, Any]:
        """获取 Agent 的定时任务列表"""
        return self._request("GET", f"/api/agents/{agent_id}/schedules")
    
    def create_schedule(
        self,
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
            cron_expression: Cron 表达式 (schedule_type=cron 时必填)
            interval_seconds: 间隔秒数 (schedule_type=interval 时必填)
            params: 任务参数
        """
        data = {
            "task_name": task_name,
            "schedule_type": schedule_type,
        }
        if schedule_type == "cron" and cron_expression:
            data["cron_expression"] = cron_expression
        if schedule_type == "interval" and interval_seconds:
            data["interval_seconds"] = interval_seconds
        if params:
            data["params"] = params
        data.update(kwargs)
        
        return self._request("POST", f"/api/agents/{agent_id}/schedules", data=data)
    
    def pause_schedule(self, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """暂停定时任务"""
        return self._request(
            "POST", f"/api/agents/{agent_id}/schedules/{schedule_id}/pause"
        )
    
    def resume_schedule(self, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """恢复定时任务"""
        return self._request(
            "POST", f"/api/agents/{agent_id}/schedules/{schedule_id}/resume"
        )
    
    def delete_schedule(self, agent_id: str, schedule_id: str) -> Dict[str, Any]:
        """删除定时任务"""
        return self._request(
            "DELETE", f"/api/agents/{agent_id}/schedules/{schedule_id}"
        )
    
    # ========== 报警管理 ==========
    
    def get_alarm_config(self, **params) -> Dict[str, Any]:
        """获取报警配置（需要 project_id 参数）"""
        # 自动填充 project_id
        if self.project_id and "project_id" not in params:
            params["project_id"] = self.project_id
        return self._request("GET", "/api/alarm/config", params=params)
    
    def save_alarm_config(self, config: Dict) -> Dict[str, Any]:
        """保存报警配置（需要在 config 中包含 project_id）"""
        # 自动填充 project_id
        if self.project_id and "project_id" not in config:
            config["project_id"] = self.project_id
        return self._request("POST", "/api/alarm/config", data=config)
    
    def test_alarm(self, channel_config: Dict) -> Dict[str, Any]:
        """测试报警渠道
        
        Args:
            channel_config: 必须包含 channel 字段 (infoflow/email/sms/baiduim)
                - infoflow: 需要 webhook, group_id(可选)
                - email: 需要 address
                - sms: 需要 phone
                - baiduim: 需要 chatId, dutyUsers
        """
        return self._request("POST", "/api/alarm/test", data=channel_config)
    
    def get_alarm_history(self, **params) -> Dict[str, Any]:
        """获取报警历史"""
        # 自动填充 project_id
        if self.project_id and "project_id" not in params:
            params["project_id"] = self.project_id
        return self._request("GET", "/api/alarm/history", params=params)
    
    def get_alarm_stats(self) -> Dict[str, Any]:
        """获取报警统计"""
        return self._request("GET", "/api/alarm/stats")
    
    def get_global_alarm_channels(self) -> Dict[str, Any]:
        """获取全局报警渠道配置"""
        return self._request("GET", "/api/alarm/global_channels")
    
    def save_global_alarm_channels(self, channels: Dict) -> Dict[str, Any]:
        """保存全局报警渠道配置"""
        return self._request("POST", "/api/alarm/global_channels", data=channels)
    
    def delete_global_alarm_channels(self) -> Dict[str, Any]:
        """删除全局报警渠道配置"""
        return self._request("DELETE", "/api/alarm/global_channels")
    
    def get_task_alarm_channels(self, task_name: str) -> Dict[str, Any]:
        """获取任务的报警渠道配置"""
        return self._request("GET", f"/api/tasks/{task_name}/alarm_channels")
    
    def save_task_alarm_channels(self, task_name: str, channels: Dict) -> Dict[str, Any]:
        """更新任务的报警渠道配置"""
        return self._request("POST", f"/api/tasks/{task_name}/alarm_channels", data=channels)
    
    # ========== 项目管理 ==========
    
    def list_projects(self, **params) -> Dict[str, Any]:
        """获取项目列表"""
        return self._request("GET", "/api/projects/", params=params)
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """获取单个项目"""
        return self._request("GET", f"/api/projects/{project_id}")
    
    def create_project(self, project_data: Dict) -> Dict[str, Any]:
        """创建新项目"""
        return self._request("POST", "/api/projects/", data=project_data)
    
    def update_project(self, project_id: str, project_data: Dict) -> Dict[str, Any]:
        """更新项目"""
        return self._request("PUT", f"/api/projects/{project_id}", data=project_data)
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """删除项目"""
        return self._request("DELETE", f"/api/projects/{project_id}")
    
    # ========== 项目成员管理 ==========
    
    def list_project_members(self, project_id: str) -> Dict[str, Any]:
        """获取项目成员列表"""
        return self._request("GET", f"/api/projects/{project_id}/members")
    
    def add_project_member(self, project_id: str, member_data: Dict) -> Dict[str, Any]:
        """添加项目成员"""
        return self._request("POST", f"/api/projects/{project_id}/members", data=member_data)
    
    def update_project_member(
        self, project_id: str, member_id: str, member_data: Dict
    ) -> Dict[str, Any]:
        """更新项目成员"""
        return self._request(
            "PUT", f"/api/projects/{project_id}/members/{member_id}", data=member_data
        )
    
    def remove_project_member(self, project_id: str, member_id: str) -> Dict[str, Any]:
        """移除项目成员"""
        return self._request("DELETE", f"/api/projects/{project_id}/members/{member_id}")
    
    # ========== 密钥管理 ==========
    
    def list_project_keys(self) -> Dict[str, Any]:
        """获取项目密钥列表"""
        return self._request("GET", "/api/projects/key")
    
    def create_project_key(self, key_data: Dict) -> Dict[str, Any]:
        """创建新的项目密钥"""
        return self._request("POST", "/api/projects/key", data=key_data)
    
    def get_project_key(self, key_id: str) -> Dict[str, Any]:
        """获取密钥详情"""
        return self._request("GET", f"/api/projects/keys/{key_id}")
    
    def update_project_key(self, key_id: str, key_data: Dict) -> Dict[str, Any]:
        """更新密钥"""
        return self._request("PUT", f"/api/projects/keys/{key_id}", data=key_data)
    
    def delete_project_key(self, key_id: str) -> Dict[str, Any]:
        """删除密钥"""
        return self._request("DELETE", f"/api/projects/keys/{key_id}")
    
    def regenerate_project_key(self, key_id: str) -> Dict[str, Any]:
        """重新生成密钥"""
        return self._request("POST", f"/api/projects/keys/{key_id}/regenerate")
    
    # ========== 激活码管理 ==========
    
    def activate_project(self, activation_code: str) -> Dict[str, Any]:
        """验证激活码并返回项目用户信息"""
        return self._request(
            "POST", "/api/projects/activate", data={"code": activation_code}
        )
    
    # ========== 最近项目 ==========
    
    def get_recent_projects(self) -> Dict[str, Any]:
        """获取最近访问的项目列表"""
        return self._request("GET", "/api/projects/recent-projects")
    
    def record_recent_project(self, project_id: str) -> Dict[str, Any]:
        """记录访问的项目"""
        return self._request(
            "POST", "/api/projects/recent-projects", data={"project_id": project_id}
        )
    
    # ========== 用户密钥 ==========
    
    def get_user_keys(self, project_id: str) -> Dict[str, Any]:
        """查询用户在指定项目下的密钥信息"""
        return self._request("GET", "/api/projects/user-keys", params={"project_id": project_id})
    
    def query_key_by_activation_code(self, code: str) -> Dict[str, Any]:
        """通过激活码查询密钥详情"""
        return self._request("POST", "/api/projects/user-keys", data={"code": code})