"""
平台化需求自动管理 API 客户端

提供以下功能：
1. 创建卡片接口
2. 流转到开发中接口
3. 查询接口
4. 批量提测准出接口
"""

import requests
from typing import List, Dict, Optional


class PlatformConfig:
    """配置类"""
    def __init__(self, base_url: str = "https://wf-test.dev.weiyun.baidu.com", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout


class PlatformClient:
    """智研师需求自动管理 API 客户端"""

    def __init__(self, config: Optional[PlatformConfig] = None, cookie: Optional[str] = None):
        self.config = config or PlatformConfig()
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # 设置 Cookie
        if cookie:
            self.session.headers.update({"Cookie": cookie})

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送请求"""
        url = f"{self.config.base_url}{endpoint}"
        response = self.session.request(
            method=method,
            url=url,
            json=data,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        return response.json()

    def create_card(
        self,
        space_code: str,
        title: str,
        card_type: str,
        platform: str,
        develop_name: str,
        assignee: str = "",
        status: str = "",
        plan: str = "",
        parents: str = "",
        detail: str = ""
    ) -> Dict:
        """
        创建卡片接口

        Args:
            space_code: iCafe空间标识（必填）
            title: 卡片标题（必填）
            card_type: 卡片类型，如 Story、Task（必填）
            platform: 平台标识（必填）
            develop_name: 开发人员姓名（必填）
            assignee: 负责人（可选）
            status: 流程状态（可选）
            plan: 所属计划（可选）
            parents: 父卡片ID（可选）
            detail: 卡片详情，HTML格式（可选）

        Returns:
            创建结果
        """
        issue_data = {
            "parents": parents,
            "title": title,
            "type": card_type,
            "detail": detail,
            "fields": {
                "负责人": assignee,
                "所属计划": plan,
                "流程状态": status
            },
            "developName": develop_name
        }

        payload = {
            "spaceCode": space_code,
            "platform": platform,
            "issues": [issue_data]
        }

        return self._request("POST", "/pioneer/api/sep/requirement/create", data=payload)

    def update_status_to_dev(
        self,
        issue_id: str,
        operator: str,
        platform: str
    ) -> Dict:
        """
        流转到开发中接口

        Args:
            issue_id: 卡片完整ID，格式：space_code-card_sequence（必填）
            operator: 操作人（必填）
            platform: 平台标识（必填）

        Returns:
            流转结果
        """
        payload = {
            "issueId": issue_id,
            "operator": operator,
            "platform": platform
        }

        return self._request("POST", "/bepqa/api/itest/card/status", data=payload)

    def query_cards(
        self,
        card_ids: Optional[List[str]] = None,
        space_id: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        查询接口

        Args:
            card_ids: 卡片ID列表（与space_id二选一必填）
            space_id: 空间标识（与card_ids二选一必填）
            **kwargs: 其他查询参数

        Returns:
            查询结果
        """
        if not card_ids and not space_id:
            raise ValueError("card_ids 和 space_id 必须至少提供一个")

        payload = {
            "cardIds": card_ids,
            "spaceId": space_id,
            **kwargs
        }

        return self._request("POST", "/bepqa/api/itest/execute/batch", data=payload)

    def batch_approve(
        self,
        issue_ids: List[str],
        operator: str,
        platform: str,
        operator_type: str
    ) -> Dict:
        """
        批量提测准出接口

        Args:
            issue_ids: 卡片ID列表，如 ["joytest-1971", "joytest-1972"]（必填）
            operator: 操作人（必填）
            platform: 平台标识（必填）
            operator_type: 操作类型，如 "发起提测"、"准出"（必填）

        Returns:
            批量提测准出结果
        """
        payload = {
            "issueIds": issue_ids,
            "operator": operator,
            "platform": platform,
            "operatorType": operator_type
        }

        return self._request("POST", "/bepqa/api/itest/execute/batch", data=payload)


    def query_icafe_cards(
        self,
        icafe_space: str,
        operator: str,
        platform: str,
        iql_text: str,
        page: int = 1,
        page_size: int = 100
    ) -> Dict:
        """
        查询 iCafe 卡片接口

        Args:
            icafe_space: iCafe 空间标识（必填）
            operator: 操作人（必填）
            platform: 平台标识（必填）
            iql_text: IQL 查询表达式（必填，查询所有可使用: sequence > 0）
            page: 页码，默认为 1（可选）
            page_size: 每页数量，默认为 100（可选）

        IQL 查询规则：
            - 基本运算符：AND, OR, >, <, =, >=, <=, !=, in, not in, is empty, is not empty, ~, !~
            - 常用示例：
              - 查询 Bug 类型卡片: `类型 = Bug`
              - 查询当前用户负责的卡片: `负责人 = currentUser`
              - 查询新建状态的卡片: `状态 = 新建`
              - 查询多种类型的卡片: `类型 in (Bug, Epic, Story)`
              - 查询标题包含关键词的卡片: `标题 ~ 测试`
              - 查询流程状态在指定范围的卡片: `流程状态 <= 开发中`
              - 查询所有卡片: `sequence > 0`

        Returns:
            查询结果
        """
        if not iql_text:
            raise ValueError("iql_text 不能为空，查询所有卡片可使用: sequence > 0")

        payload = {
            "iCafeSpace": icafe_space,
            "operator": operator,
            "platform": platform,
            "iqlText": iql_text,
            "page": str(page),
            "pageSize": str(page_size)
        }

        return self._request("POST", "/bepqa/api/itest/query/icafe/cards", data=payload)

    def get_card_url(self, space_prefix_code: str, card_sequence: int) -> str:
        """
        获取卡片访问链接

        Args:
            space_prefix_code: 空间前缀代码
            card_sequence: 卡片序号

        Returns:
            卡片访问链接
        """
        return f"https://console.cloud.baidu-int.com/devops/icafe/issue/{space_prefix_code}-{card_sequence}/show"

    def get_card_url_from_response(self, response: Dict, space_code: str = None) -> str:
        """
        从创建卡片的响应中获取卡片链接

        Args:
            response: 创建卡片API的响应
            space_code: 空间代码（如果响应中未包含spacePrefixCode时使用）

        Returns:
            卡片访问链接，如果解析失败返回空字符串
        """
        try:
            card_data = response.get("data", {}).get("result", {}).get("results", [{}])[0]
            card_sequence = card_data.get("sequence")
            space_prefix_code = card_data.get("spacePrefixCode", space_code)

            if card_sequence and space_prefix_code:
                return self.get_card_url(space_prefix_code, card_sequence)
        except (IndexError, AttributeError):
            pass
        return ""


def create_client(base_url: str = None) -> PlatformClient:
    """创建客户端实例（已弃用，直接使用 PlatformClient 即可）"""
    config = PlatformConfig(base_url=base_url) if base_url else None
    return PlatformClient(config)
