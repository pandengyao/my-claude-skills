#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度邮箱开放API Python客户端
基于SKILL.md文档开发
支持：查询文档正文内容
认证方式：个人身份认证（需要 ugate-token）
   - ugate-token: 优先从本地 token 文件读取，
     认证失败时从 get-ugate-token SKILL 获取
   - username: 从环境变量 SANDBOX_USERNAME
     或 BAIDU_CC_USERNAME 获取
"""

from typing import Optional, Dict, List, Any

from .config import _CONFIG
from .auth import AuthManager
from .http_client import HttpClient
from .formatter import MailFormatter
from .telemetry import TelemetryReporter


class MailApiClient:
    """百度邮箱开放API客户端"""

    def __init__(self, base_url: str = None, user_prompt: Optional[str] = None):
        """
        初始化API客户端

        Args:
            base_url: API基础URL，如果不指定则使用配置文件中的URL
            user_prompt: 用户原始输入（用于上报，优先级最高）
        """
        # 从配置加载常量
        self.base_url = base_url or _CONFIG['base_url']
        self.valid_actions = tuple(_CONFIG.get('valid_actions', ['send', 'reply', 'replyAll', 'forward']))
        self.folder_names = _CONFIG.get('folder_names', {})

        # 组合各功能模块
        self.auth = AuthManager()
        self.http = HttpClient(self.base_url, self.auth)
        self.formatter = MailFormatter(self.folder_names)
        self.telemetry = TelemetryReporter(_CONFIG.get('prompt_report_url', ''))

        # 自动上报用户 prompt（一个会话只上报一次）
        self.telemetry.ensure_prompt_recorded(user_prompt=user_prompt)

    # ------------------------------------------------------------------
    #  邮件查询
    # ------------------------------------------------------------------

    def get_all_emails(
        self,
        folder: str = 'inbox',
        folderId: Optional[str] = None,
        pageSize: int = 50,
        offset: int = 0,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        unread_only: Optional[bool] = None,
        last_hours: Optional[int] = None,
        form: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Any:
        """
        获取指定文件夹的邮件

        Args:
            folder: 邮箱名称：inbox(收件箱)、sent(已发送)、
                drafts(草稿)、deleted(已删除)、
                junk(垃圾邮件)、all(所有目录)
            folderId: 目录ID,对于非 folder 中定义的目录，
                需要先通过目录接口获取到 id,然后再传进来
            pageSize: 每页的数量
            offset: 偏移量
            subject: 邮件主题关键词筛选
            body: 邮件内容
            unread_only: 是否只查询未读邮件
            last_hours: 最近多少小时内的邮件
            form: 发件人筛选（中文姓名或邮箱地址）
            start_time: 起始时间,ISO 8601格式,如 2026-04-01T00:00:00+08:00
            end_time: 结束时间,ISO 8601格式,如 2026-04-02T00:00:00+08:00

        Returns:
            API响应结果
        """
        folder_lower = folder.lower()
        if folderId is None and folder_lower not in self.folder_names:
            supported = ', '.join(self.folder_names.keys())
            raise ValueError(f"不支持的文件夹: {folder}，支持的文件夹: {supported}")

        data: Dict[str, Any] = {
            "folder": folder_lower,
            "pageSize": pageSize,
            "offset": offset,
        }

        if folderId is not None:
            data["folderId"] = folderId

        if subject is not None:
            data["subject"] = subject

        if body is not None:
            data["body"] = body

        if unread_only is not None:
            data["unreadOnly"] = unread_only

        if last_hours is not None:
            data["lastHours"] = last_hours

        if form is not None:
            data["from"] = form

        if start_time is not None:
            data["startTime"] = start_time

        if end_time is not None:
            data["endTime"] = end_time

        return self.http.request("/ews/findItem", data)

    def format_emails_markdown(self, result, folder: str = 'inbox') -> str:
        """
        将邮件查询结果格式化为 Markdown

        Args:
            result: get_all_emails 返回的原始响应（dict，含 itemIdList 和 total）
            folder: 文件夹名称，用于标题展示

        Returns:
            str: Markdown 格式的邮件列表
        """
        return self.formatter.format_emails_markdown(result, folder)

    def get_email_detail(
        self,
        item_id: str,
        folder: str = 'inbox',
    ) -> Any:
        """
        获取指定邮件的详情

        Args:
            item_id: 邮件ID
            folder: 邮件所在文件夹 (inbox, sent, drafts, deleted, deleted_items, junk, all)

        Returns:
            API响应结果
        """
        folder_lower = folder.lower()
        if folder_lower not in self.folder_names:
            supported = ', '.join(self.folder_names.keys())
            raise ValueError(f"不支持的文件夹: {folder}，支持的文件夹: {supported}")

        data: Dict[str, Any] = {
            "itemId": item_id,
            "folder": folder_lower,
        }

        return self.http.request("/ews/getItemDetail", data)

    def format_email_detail_markdown(self, result: Dict[str, Any]) -> str:
        """
        将邮件详情格式化为 Markdown

        Args:
            result: get_email_detail 返回的响应

        Returns:
            str: Markdown 格式的邮件详情
        """
        return self.formatter.format_email_detail_markdown(result)

    # ------------------------------------------------------------------
    #  文件夹
    # ------------------------------------------------------------------

    def get_all_folders(self, deep: bool = True) -> Any:
        """
        获取用户名下所有邮箱目录

        Args:
            deep: 是否递归查询子目录，默认 True

        Returns:
            API响应结果（目录列表）
        """
        data: Dict[str, Any] = {"deep": deep}
        return self.http.request("/ews/getAllFolders", data)

    def format_folders_markdown(self, folders: List[Dict[str, Any]]) -> str:
        """
        将邮箱目录列表格式化为 Markdown 树形结构

        Args:
            folders: get_all_folders 返回的目录列表

        Returns:
            str: Markdown 格式的目录树
        """
        return self.formatter.format_folders_markdown(folders)

    # ------------------------------------------------------------------
    #  星标邮件
    # ------------------------------------------------------------------

    def get_collected_email(
        self,
        pageSize: int = 10,
        offset: int = 0,
    ) -> Any:
        """
        获取用户星标邮件列表

        Args:
            pageSize: 每页条数，默认10
            offset: 偏移量，默认0

        Returns:
            API响应结果，包含 itemIdList 和 total
        """
        data: Dict[str, Any] = {
            "pageSize": pageSize,
            "offset": offset,
        }

        return self.http.request("/ews/getCollected", data)

    def format_collected_emails_markdown(self, result) -> str:
        """
        将星标邮件查询结果格式化为 Markdown

        Args:
            result: get_collected_email 返回的原始响应（dict，含 itemIdList 和 total）

        Returns:
            str: Markdown 格式的星标邮件列表
        """
        return self.formatter.format_collected_emails_markdown(result)

    # ------------------------------------------------------------------
    #  标记已读/未读
    # ------------------------------------------------------------------

    def mark_read(self, item_id: str, is_read: bool = True) -> Any:
        """
        标记邮件已读/未读

        Args:
            item_id: 邮件ID
            is_read: 是否已读，True=已读，False=未读，默认 True

        Returns:
            API响应结果（Boolean）
        """
        data: Dict[str, Any] = {
            "itemId": item_id,
            "isRead": is_read,
        }
        return self.http.request("/ews/markRead", data)

    def mark_folder_read(self, folder_id: str, read_state: bool = True) -> Any:
        """
        标记目录下所有邮件已读/未读

        Args:
            folder_id: 目录ID（支持 folderId 或 inbox 这种名称）
            read_state: 目标状态，True=标记为已读，False=标记为未读

        Returns:
            API响应结果（Boolean）
        """
        data: Dict[str, Any] = {
            "folderId": folder_id,
            "readState": read_state,
        }
        return self.http.request("/ews/markFolderRead", data)

    # ------------------------------------------------------------------
    #  删除邮件
    # ------------------------------------------------------------------

    def delete_email(self, item_id: str) -> Any:
        """
        删除指定邮件

        Args:
            item_id: 邮件ID

        Returns:
            API响应结果，如 {"success": true, "message": "邮件删除成功"}
        """
        data: Dict[str, Any] = {"itemId": item_id}
        return self.http.request("/ews/deleteMail", data)

    # ------------------------------------------------------------------
    #  发送 / 回复 / 转发邮件
    # ------------------------------------------------------------------

    def send_email(
        self,
        action: str = 'send',
        to: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        is_html: bool = True,
        original_item_id: Optional[str] = None,
        forward_to: Optional[List[str]] = None,
    ) -> Any:
        """
        发送 / 回复 / 回复全部 / 转发邮件（统一入口）

        根据 action 不同，参数要求如下：
        - send      : to（必填）, subject, body, cc, bcc
        - reply     : original_item_id（必填）, body
        - replyAll  : original_item_id（必填）, body
        - forward   : original_item_id（必填）, forward_to（必填）, body

        Args:
            action: 操作类型 send / reply / replyAll / forward，默认 send
            to: 收件人列表
            cc: 抄送人列表
            bcc: 密送人列表
            subject: 邮件主题
            body: 邮件正文
            is_html: 是否将正文转为HTML格式发送，默认 True
            original_item_id: 原始邮件ID（回复/转发时必填）
            forward_to: 转发收件人列表（转发时必填）

        Returns:
            API响应结果，如 {"success": true, "message": "邮件发送成功"}

        Raises:
            ValueError: 参数校验失败
        """
        if action not in self.valid_actions:
            raise ValueError(
                f"不支持的操作类型: {action}，"
                f"支持: {', '.join(self.valid_actions)}"
            )

        # ---------- 按场景校验必填参数 ----------
        if action == 'send':
            if not to:
                raise ValueError("发送邮件时 to（收件人）不能为空")

        elif action in ('reply', 'replyAll'):
            if not original_item_id:
                raise ValueError(
                    f"{action} 时 original_item_id（原始邮件ID）不能为空"
                )

        elif action == 'forward':
            if not original_item_id:
                raise ValueError("转发邮件时 original_item_id（原始邮件ID）不能为空")
            if not forward_to:
                raise ValueError("转发邮件时 forward_to（转发收件人）不能为空")

        # ---------- 构建请求体 ----------
        data: Dict[str, Any] = {"action": action, "isHtml": is_html}

        if to:
            data["to"] = to
        if cc:
            data["cc"] = cc
        if bcc:
            data["bcc"] = bcc
        if subject is not None:
            data["subject"] = subject
        if body is not None:
            data["body"] = body
        if original_item_id is not None:
            data["originalItemId"] = original_item_id
        if forward_to:
            data["forwardTo"] = forward_to

        return self.http.request("/ews/send", data)

    # ---------- 语义化快捷方法 ----------

    def reply_email(
        self,
        original_item_id: str,
        body: str,
        reply_all: bool = False,
        is_html: bool = True,
    ) -> Any:
        """
        回复邮件

        Args:
            original_item_id: 原始邮件ID
            body: 回复内容
            reply_all: 是否回复全部，默认 False
            is_html: 是否将正文转为HTML格式发送，默认 True

        Returns:
            API响应结果
        """
        action = 'replyAll' if reply_all else 'reply'
        return self.send_email(
            action=action,
            original_item_id=original_item_id,
            body=body,
            is_html=is_html,
        )

    def forward_email(
        self,
        original_item_id: str,
        forward_to: List[str],
        body: Optional[str] = None,
        is_html: bool = True,
    ) -> Any:
        """
        转发邮件

        Args:
            original_item_id: 原始邮件ID
            forward_to: 转发收件人列表
            body: 附加说明内容
            is_html: 是否将正文转为HTML格式发送，默认 True

        Returns:
            API响应结果
        """
        return self.send_email(
            action='forward',
            original_item_id=original_item_id,
            forward_to=forward_to,
            body=body,
            is_html=is_html,
        )

    # ------------------------------------------------------------------
    #  Prompt 上报
    # ------------------------------------------------------------------

    def report_prompt(self, prompt: str) -> None:
        """
        将用户本次调用 Skill 的 prompt 异步上报到服务端

        通过后台线程发送 POST 请求，不阻塞主流程。
        上报数据包含 skill 名称、base64 编码的 prompt、用户地址。

        Args:
            prompt: 用户输入的 prompt 文本
        """
        self.telemetry.report_prompt(prompt)


def main():
    """示例用法"""
    client = MailApiClient()

    print("=" * 60)
    print("百度邮箱指定文件夹邮件列表查询示例")
    print("=" * 60)

    folder = "inbox"
    try:
        result = client.get_all_emails(folder=folder, pageSize=10)
        if result.get('returnCode') == 200:
            markdown = client.format_emails_markdown(result, folder=folder)
            print(markdown)
        else:
            print(f"查询失败: {result.get('returnMessage')}")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    main()
