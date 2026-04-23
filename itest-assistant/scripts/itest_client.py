"""
iTest API Client - 提测准出操作助手

提供 iTest 平台提测、准出相关的 API 接口封装。
"""

import os
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ITestConfig:
    """iTest API 配置"""
    base_url: str = "http://itest-api.baidu-int.com"
    timeout: int = 30
    # 默认鉴权配置（可通过环境变量覆盖）
    access_token: str = "your_token"
    platform: str = "your_platform"

    @staticmethod
    def _get_access_token() -> Optional[str]:
        """获取访问 token

        优先从环境变量 ITEST_ACCESS_TOKEN 读取，
        如果没有则从 ~/.comate/itest_login 文件读取

        Returns:
            访问 token 字符串，如果都未找到则返回 None
        """
        # 优先从环境变量读取
        token = os.environ.get("ITEST_ACCESS_TOKEN")
        if token:
            return token

        # 从登录文件读取
        login_file = Path.home() / ".comate" / "itest_login"
        if login_file.exists():
            try:
                content = login_file.read_text().strip()
                # 文件格式：纯 token（单行）
                if content:
                    return content
            except Exception:
                pass

        return None

    @staticmethod
    def _get_platform() -> Optional[str]:
        """获取 platform 参数

        优先从环境变量 ITEST_PLATFORM 读取

        Returns:
            platform 字符串，未找到则返回 None
        """
        return os.environ.get("ITEST_PLATFORM")


class ITestClient:
    """iTest API 客户端"""

    def __init__(self, config: Optional[ITestConfig] = None):
        self.config = config or ITestConfig()
        self.session = requests.Session()

        # 设置默认 headers
        self.session.headers.update({
            "Content-Type": "application/json"
        })

        # 获取访问 token 和 platform（优先使用环境变量/文件，否则使用配置中的默认值）
        self.access_token = self.config._get_access_token() or self.config.access_token
        self.platform = self.config._get_platform() or self.config.platform

    def _get_params(self, extra_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取通用请求参数

        Args:
            extra_params: 额外的查询参数

        Returns:
            合并后的查询参数
        """
        params = {}
        if self.access_token:
            params['accessToken'] = self.access_token
        if self.platform:
            params['platform'] = self.platform
        if extra_params:
            params.update(extra_params)
        return params

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """通用请求方法

        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            **kwargs: 其他请求参数

        Returns:
            响应数据字典

        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = f"{self.config.base_url}{endpoint}"
        # 添加 User-Agent
        headers = kwargs.get('headers', {})
        headers['User-Agent'] = 'iTestClient/1.0.0'
        kwargs['headers'] = headers

        response = self.session.request(
            method,
            url,
            timeout=self.config.timeout,
            **kwargs
        )
        response.raise_for_status()
        return response.json()

    # ========================================
    # 1. 查询用户有权限的空间列表
    # ========================================
    def get_accessible_spaces(self, username: str,
                               page_num: Optional[int] = None,
                               page_size: Optional[int] = None) -> Dict[str, Any]:
        """查询指定用户有权限的空间列表

        对应 API: GET /api/thirdparty/space/accessible

        Args:
            username: 用户名（必填）
            page_num: 页码（可选）
            page_size: 每页条目数（可选）

        Returns:
            空间列表

        Raises:
            ValueError: 当 username 为空时
            requests.RequestException: 请求失败时
        """
        if not username:
            raise ValueError("username 不能为空")

        params = self._get_params({
            'username': username
        })
        if page_num:
            params['pageNum'] = page_num
        if page_size:
            params['pageSize'] = page_size

        return self._request(
            "GET",
            "/api/thirdparty/space/accessible",
            params=params
        )

    # ========================================
    # 2. 根据空间获取提测详情
    # ========================================
    def get_space_test_details(self, space_code: str,
                                is_req_succ: Optional[bool] = None,
                                is_permit_out: Optional[bool] = None,
                                page_num: Optional[int] = None,
                                page_size: Optional[int] = None) -> Dict[str, Any]:
        """根据 spaceCode 获得空间指定条件下提测

        对应 API: GET /api/thirdparty/requestTest/{spaceCode}/detail

        Args:
            space_code: itest 空间编号（必填）
            is_req_succ: 是否成功确认提测（可选）
            is_permit_out: 是否准出（可选）
            page_num: 页码，默认为 1（可选）
            page_size: 每页条目数，默认为 10（可选）

        Returns:
            提测列表和总数

        Raises:
            ValueError: 当 space_code 为空时
            requests.RequestException: 请求失败时
        """
        if not space_code:
            raise ValueError("space_code 不能为空")

        params = self._get_params()
        if is_req_succ is not None:
            params['isReqSucc'] = is_req_succ
        if is_permit_out is not None:
            params['isPermitOut'] = is_permit_out
        if page_num:
            params['pageNum'] = page_num
        if page_size:
            params['pageSize'] = page_size

        return self._request(
            "GET",
            f"/api/thirdparty/requestTest/{space_code}/detail",
            params=params
        )

    # ========================================
    # 3. 获取未完成的提测
    # ========================================
    def get_unfinished_tests(self, module: Optional[str] = None,
                            branch: Optional[str] = None,
                            pipeline_build_id: Optional[int] = None) -> Dict[str, Any]:
        """获取未完成的提测

        对应 API: GET /api/thirdparty/requestTest/getUnfinishedTestByModuleBranch

        Args:
            module: 模块名（可选）
            branch: 分支名（可选）
            pipeline_build_id: 流水线构建 id（可选）

        Returns:
            未完成的提测列表

        Raises:
            ValueError: 当参数无效时
            requests.RequestException: 请求失败时

        Note:
            pipelineBuildId 不填时，module 和 branch 必传；module 和 branch 需同时传或同时不传
        """
        # pipelineBuildId 不填时，module 和 branch 必传
        if not pipeline_build_id and (not module or not branch):
            raise ValueError("pipeline_build_id 不填时，module 和 branch 必传")

        params = self._get_params()
        if module:
            params['module'] = module
        if branch:
            params['branch'] = branch
        if pipeline_build_id:
            params['pipelineBuildId'] = pipeline_build_id

        return self._request(
            "GET",
            "/api/thirdparty/requestTest/getUnfinishedTestByModuleBranch",
            params=params
        )

    # ========================================
    # 4. 发起提测
    # ========================================
    def create_test_request(self, name: str, test_plan_id: int,
                            test_users: List[str], modules: List[Dict[str, str]],
                            issues: List[Dict[str, str]], operator: str,
                            test_note: Optional[str] = None) -> Dict[str, Any]:
        """发起提测

        对应 API: POST /api/thirdparty/requestTest/start

        Args:
            name: 提测名称（必填）
            test_plan_id: 测试计划 ID（必填）
            test_users: 测试人员列表（必填）
            modules: 提测模块列表，每个元素包含 module 和 branch（必填）
            issues: 关联的卡片列表，每个元素包含 issueId 和 issueType（必填）
            operator: 操作人标识（必填）
            test_note: 测试要点说明（可选）

        Returns:
            创建的提测记录详情

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not name or not test_plan_id or not test_users or not modules or not issues or not operator:
            raise ValueError("name, test_plan_id, test_users, modules, issues, operator 不能为空")

        data = {
            'name': name,
            'testPlanId': test_plan_id,
            'testUsers': test_users,
            'modules': modules,
            'issues': issues,
            'operator': operator
        }
        if test_note:
            data['testNote'] = test_note

        return self._request(
            "POST",
            "/api/thirdparty/requestTest/start",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 5. 获取待确认的提测
    # ========================================
    def get_unconfirmed_tests(self, username: str,
                              issues: Optional[str] = None,
                              keyword: Optional[str] = None,
                              modules: Optional[str] = None,
                              create_test_user: Optional[str] = None) -> Dict[str, Any]:
        """获取某人待确认的提测

        对应 API: GET /api/thirdparty/requestTest/unconfirmed

        Args:
            username: 用户邮箱前缀（必填）
            issues: 需求标识，多个用英文逗号连接（可选）
            keyword: 标题模糊搜索关键字（可选）
            modules: 提测模块，多个用英文逗号连接（可选）
            create_test_user: 发起提测人（可选）

        Returns:
            待确认的提测列表

        Raises:
            ValueError: 当 username 为空时
            requests.RequestException: 请求失败时
        """
        if not username:
            raise ValueError("username 不能为空")

        params = self._get_params({
            'username': username
        })
        if issues:
            params['issues'] = issues
        if keyword:
            params['keyword'] = keyword
        if modules:
            params['modules'] = modules
        if create_test_user:
            params['createTestUser'] = create_test_user

        return self._request(
            "GET",
            "/api/thirdparty/requestTest/unconfirmed",
            params=params
        )

    # ========================================
    # 6. 确认提测
    # ========================================
    def confirm_test_request(self, request_test_id: int, result: bool,
                             confirm_user: str,
                             test_plan_id: Optional[int] = None,
                             test_plan_name: Optional[str] = None,
                             space_code: Optional[str] = None) -> Dict[str, Any]:
        """确认提测

        对应 API: POST /api/thirdparty/requestTest/confirm

        Args:
            request_test_id: 提测 id（必填）
            result: 结果，true - 接受，false - 驳回（必填）
            confirm_user: 确认人（必填）
            test_plan_id: 测试计划 id（可选）
            test_plan_name: 测试计划名称（可选）
            space_code: 空间标识（可选）

        Returns:
            操作结果

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not request_test_id or result is None or not confirm_user:
            raise ValueError("request_test_id, result, confirm_user 不能为空")

        data = {
            'requestTestId': request_test_id,
            'result': result,
            'confirmUser': confirm_user
        }
        if test_plan_id:
            data['testPlanId'] = test_plan_id
        if test_plan_name:
            data['testPlanName'] = test_plan_name
        if space_code:
            data['spaceCode'] = space_code

        return self._request(
            "POST",
            "/api/thirdparty/requestTest/confirm",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 7. 获取未准出的提测（根据用户或模块）
    # ========================================
    def get_not_permit_out_tests(self,
                                   username: Optional[str] = None,
                                   modules: Optional[List[Dict[str, str]]] = None,
                                   start_time: Optional[int] = None,
                                   end_time: Optional[int] = None) -> Dict[str, Any]:
        """根据用户或模块获取未准出的提测

        对应 API: POST /api/thirdparty/requestTest/notPermitOut

        Args:
            username: 用户邮箱前缀（可选）
            modules: 提测模块列表，每个元素包含 module 和 branch（可选）
            start_time: 开始时间（确认提测时间），毫秒时间戳（可选）
            end_time: 结束时间（确认提测时间），毫秒时间戳（可选）

        Returns:
            未准出的提测列表

        Raises:
            ValueError: 当参数无效时
            requests.RequestException: 请求失败时

        Note:
            需要提供 username 或 modules 中的一个
        """
        data = {}
        if username:
            data['username'] = username
        if modules:
            data['modules'] = modules
        if start_time:
            data['startTime'] = start_time
        if end_time:
            data['endTime'] = end_time

        return self._request(
            "POST",
            "/api/thirdparty/requestTest/notPermitOut",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 8. 发起准出
    # ========================================
    def create_permit_out(self, request_test_id: int, operator: str,
                           permit_out_users: List[str]) -> Dict[str, Any]:
        """发起准出

        对应 API: POST /api/thirdparty/permitOut/start

        Args:
            request_test_id: 提测 id（必填）
            operator: 发起人（必填）
            permit_out_users: 准出人员列表（必填）

        Returns:
            操作结果

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not request_test_id or not operator or not permit_out_users:
            raise ValueError("request_test_id, operator, permit_out_users 不能为空")

        data = {
            'requestTestId': request_test_id,
            'operator': operator,
            'permitOutUsers': permit_out_users
        }

        return self._request(
            "POST",
            "/api/thirdparty/permitOut/start",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 9. 确认准出
    # ========================================
    def confirm_permit_out(self, permit_out_id: int, result: bool,
                            confirm_user: str,
                            desc_note: Optional[str] = None,
                            inform_users: Optional[List[str]] = None) -> Dict[str, Any]:
        """确认准出

        对应 API: POST /api/thirdparty/permitOut/confirm

        Args:
            permit_out_id: 准出 id（必填）
            result: true - 接受 / false - 驳回（必填）
            confirm_user: 确认人（必填）
            desc_note: 准出描述（可选）
            inform_users: 准出通知人（可选）

        Returns:
            操作结果

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not permit_out_id or result is None or not confirm_user:
            raise ValueError("permit_out_id, result, confirm_user 不能为空")

        data = {
            'permitOutId': permit_out_id,
            'result': result,
            'confirmUser': confirm_user
        }
        if desc_note:
            data['descNote'] = desc_note
        if inform_users:
            data['informUsers'] = inform_users

        return self._request(
            "POST",
            "/api/thirdparty/permitOut/confirm",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 10. 批量确认准出（一键准出）
    # ========================================
    def batch_confirm_permit_out(self, permit_out_ids: List[int], result: bool,
                                  confirm_user: str) -> Dict[str, Any]:
        """批量确认准出（一键准出）

        对应 API: POST /api/thirdparty/permitOut/confirm/batch

        Args:
            permit_out_ids: 准出 id 列表（必填）
            result: true - 接受 / false - 驳回（必填）
            confirm_user: 确认人（必填）

        Returns:
            操作结果

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not permit_out_ids or result is None or not confirm_user:
            raise ValueError("permit_out_ids, result, confirm_user 不能为空")

        data = {
            'permitOutIds': permit_out_ids,
            'result': result,
            'confirmUser': confirm_user
        }

        return self._request(
            "POST",
            "/api/thirdparty/permitOut/confirm/batch",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 11. 从 Bot 发起提测
    # ========================================
    def create_test_request_from_bot(self, operator: str, test_users: List[str],
                                     modules: List[Dict[str, str]],
                                     is_pipeline: bool = False,
                                     pipeline_conf_id: Optional[int] = None,
                                     issue_ids: Optional[List[str]] = None,
                                     test_note: Optional[str] = None,
                                     name: Optional[str] = None) -> Dict[str, Any]:
        """从 Bot 发起提测

        对应 API: POST /api/thirdparty/requestTest/startFromBot

        Args:
            operator: 操作人（必填）
            test_users: 测试人员列表（必填）
            modules: 提测模块列表，每个元素包含 module 和 branch（必填）
            is_pipeline: 是否流水线提测（可选）
            pipeline_conf_id: 流水线配置 ID（可选）
            issue_ids: 卡片列表（可选）
            test_note: 测试备注（可选）
            name: 任务名（可选）

        Returns:
            操作结果

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时

        Note:
            从 Bot 发起提测，确认提测需要选择测试计划
        """
        if not operator or not test_users or not modules:
            raise ValueError("operator, test_users, modules 不能为空")

        data = {
            'operator': operator,
            'testUsers': test_users,
            'modules': modules
        }
        if is_pipeline:
            data['isPipeline'] = is_pipeline
        if pipeline_conf_id:
            data['pipelineConfId'] = pipeline_conf_id
        if issue_ids:
            data['issueIds'] = issue_ids
        if test_note:
            data['testNote'] = test_note
        if name:
            data['name'] = name

        return self._request(
            "POST",
            "/api/thirdparty/requestTest/startFromBot",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 12. 创建测试计划
    # ========================================
    def create_test_plan(self, name: str, space_code: str, creator: str,
                          test_owners: List[str]) -> Dict[str, Any]:
        """创建测试计划

        对应 API: POST /api/thirdparty/testPlan/create

        Args:
            name: 计划名称（必填）
            space_code: 空间标识（必填）
            creator: 创建人（必填）
            test_owners: 测试人员列表（必填）

        Returns:
            创建的测试计划

        Raises:
            ValueError: 当缺少必需参数时
            requests.RequestException: 请求失败时
        """
        if not name or not space_code or not creator or not test_owners:
            raise ValueError("name, space_code, creator, test_owners 不能为空")

        data = {
            'name': name,
            'spaceCode': space_code,
            'creator': creator,
            'testOwners': test_owners
        }

        return self._request(
            "POST",
            "/api/thirdparty/testPlan/create",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 13. 根据用户获取未准出的提测
    # ========================================
    def get_not_permit_out_by_user(self, username: str,
                                     test_users: Optional[List[str]] = None,
                                     start_time: Optional[int] = None,
                                     end_time: Optional[int] = None,
                                     space_name: Optional[str] = None,
                                     modules: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """根据用户获取未准出的提测

        对应 API: POST /api/thirdparty/requestTest/getNotPermitOutRequestTestByUser

        Args:
            username: 用户邮箱前缀（必填）
            test_users: 测试人员列表（可选）
            start_time: 开始时间（确认提测时间），毫秒时间戳（可选）
            end_time: 结束时间（确认提测时间），毫秒时间戳（可选）
            space_name: 测试空间（可选）
            modules: 提测模块列表，每个元素包含 module 和 branch（可选）

        Returns:
            未准出的提测列表

        Raises:
            ValueError: 当 username 为空时
            requests.RequestException: 请求失败时
        """
        if not username:
            raise ValueError("username 不能为空")

        data = {
            'username': username
        }
        if test_users:
            data['testUsers'] = test_users
        if start_time:
            data['startTime'] = start_time
        if end_time:
            data['endTime'] = end_time
        if space_name:
            data['spaceName'] = space_name
        if modules:
            data['modules'] = modules

        return self._request(
            "POST",
            "/api/thirdparty/requestTest/getNotPermitOutRequestTestByUser",
            params=self._get_params(),
            json=data
        )

    # ========================================
    # 14. 根据提测 ID 获取提测相关信息
    # ========================================
    def get_test_by_id(self, test_id: int) -> Dict[str, Any]:
        """根据提测 ID 获取提测相关信息

        对应 API: GET /api/thirdparty/requestTest/getTestDataByTestId

        Args:
            test_id: 提测 ID（必填）

        Returns:
            提测信息，可生成访问链接：https://console.cloud.baidu-int.com/itest/#/console/test/{testId}/0

        Raises:
            ValueError: 当 test_id 为空时
            requests.RequestException: 请求失败时
        """
        if not test_id:
            raise ValueError("test_id 不能为空")

        return self._request(
            "GET",
            "/api/thirdparty/requestTest/getTestDataByTestId",
            params=self._get_params({
                'testId': test_id
            })
        )


# ========================================
# 使用示例
# ========================================
if __name__ == "__main__":
    # 使用默认配置（使用环境变量或登录文件的认证 token）
    client = ITestClient()

    # 示例：获取用户有权限的空间列表
    # spaces = client.get_accessible_spaces("your-user-id")
    # print(spaces)

    # 示例：发起提测
    # result = client.create_test_request(
    #     name="首次提测",
    #     test_plan_id=243597,
    #     test_users=["user1", "user2"],
    #     modules=[{"module": "auth-service", "branch": "feature/login"}],
    #     issues=[{"issueId": "AGILE-2", "issueType": "Story"}],
    #     operator="your-user-id"
    # )
    # print(result)
