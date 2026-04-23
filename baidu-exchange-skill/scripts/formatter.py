#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 格式化模块

将邮件 API 响应数据格式化为 Markdown 展示。
"""

from pathlib import Path
from typing import Optional, Dict, List, Any


class MailFormatter:
    """邮件数据 Markdown 格式化器"""

    TEMPLATE_PATH = Path(__file__).parent.parent / 'assets' / 'template.md'

    def __init__(self, folder_names: Dict[str, str]):
        """
        Args:
            folder_names: 文件夹英文名到中文名的映射
        """
        self.folder_names = folder_names

    def _load_template(self, name: str) -> Optional[str]:
        """
        从 template.md 中按名称加载模板片段

        模板以 <!-- TEMPLATE: name --> 和 <!-- END: name --> 包裹

        Args:
            name: 模板名称 (email_list / email_detail / folders)

        Returns:
            模板字符串，加载失败时返回 None
        """
        try:
            content = self.TEMPLATE_PATH.read_text(encoding='utf-8')
            start_marker = f'<!-- TEMPLATE: {name} -->'
            end_marker = f'<!-- END: {name} -->'
            start = content.find(start_marker)
            end = content.find(end_marker)
            if start == -1 or end == -1:
                return None
            # 取 marker 后面的内容，去掉首尾空行
            fragment = content[start + len(start_marker):end].strip('\n')
            return fragment
        except Exception:
            return None

    def format_emails_markdown(self, result, folder: str = 'inbox') -> str:
        """
        将邮件查询结果格式化为 Markdown

        Args:
            result: get_all_emails 返回的原始响应（dict，含 itemIdList 和 total）
            folder: 文件夹名称，用于标题展示

        Returns:
            str: Markdown 格式的邮件列表
        """
        # 新版 API 返回 {"itemIdList": [...], "total": N}
        if isinstance(result, dict):
            emails = result.get('itemIdList', [])
            total = result.get('total', len(emails))
        else:
            # 兼容旧版直接返回 list 的情况
            emails = result
            total = len(emails)

        folder_cn = self.folder_names.get(folder.lower(), folder)

        # 统计
        page_count = len(emails)
        unread_count = sum(1 for e in emails if not e.get('isRead'))

        # 构建表格行
        rows = []
        for i, email in enumerate(emails, 1):
            status = '已读' if email.get('isRead') else '**未读**'
            subject = email.get('subject', '(无主题)')
            form = email.get('from', '未知')
            time = email.get('receivedTime', '未知')
            rows.append(f"| {i} | {status} | {subject} | {form} | {time} |")
        email_rows = '\n'.join(rows)

        # 构建详情区
        details = []
        for i, email in enumerate(emails, 1):
            status = '已读' if email.get('isRead') else '未读'
            subject = email.get('subject', '(无主题)')
            form = email.get('from', '未知')
            to_list = ', '.join(email.get('to', []))
            time = email.get('receivedTime', '未知')
            summary = email.get('summary') or '(无摘要)'
            item_id = email.get('itemId', '')

            detail = (
                f"### [{i}] {subject}\n"
                f"- **发件人**: {form}\n"
                f"- **收件人**: {to_list}\n"
                f"- **时间**: {time}\n"
                f"- **状态**: {status}\n"
                f"- **摘要**: {summary}\n"
                f"- **邮件ID**: `{item_id}`"
            )
            details.append(detail)
        email_details = '\n\n'.join(details)

        # 读取模板并填充
        template = self._load_template('email_list')
        if not template:
            template = (
                "# 📬 {folder_name}\n\n"
                "> 共 **{total_count}** 封邮件，"
                "当前展示 **{page_count}** 封，"
                "其中未读 **{unread_count}** 封\n\n"
                "{email_rows}\n\n---\n\n"
                "## 邮件详情\n\n{email_details}\n"
            )

        return template.format(
            folder_name=folder_cn,
            total_count=total,
            page_count=page_count,
            unread_count=unread_count,
            email_rows=email_rows,
            email_details=email_details,
        )

    def format_email_detail_markdown(self, result: Dict[str, Any]) -> str:
        """
        将邮件详情格式化为 Markdown

        Args:
            result: get_email_detail 返回的响应

        Returns:
            str: Markdown 格式的邮件详情
        """
        subject = result.get('subject', '(无主题)')
        sender = result.get('sender', '未知')
        to_recipients = ', '.join(result.get('toRecipients', []))
        cc_list = ', '.join(result.get('ccRecipients', []))
        bcc_list = ', '.join(result.get('bccRecipients', []))
        sent_time = result.get('datetimeSent', '未知')
        received_time = result.get('datetimeReceived', '未知')
        is_read = '已读' if result.get('isRead') else '未读'
        has_attachments = '有' if result.get('hasAttachments') else '无'
        body = result.get('body', '(无正文)')
        item_id = result.get('id', '')

        # 构建可选的抄送/密送行
        cc_row = ''
        if cc_list:
            cc_row += f"| **抄送** | {cc_list} |\n"
        if bcc_list:
            cc_row += f"| **密送** | {bcc_list} |\n"

        template = self._load_template('email_detail')
        if not template:
            template = (
                "# 📧 {subject}\n\n"
                "| 字段 | 内容 |\n|:----:|------|\n"
                "| **发件人** | {sender} |\n| **收件人** | {to_recipients} |\n"
                "{cc_row}| **发送时间** | {sent_time} |\n| **接收时间** | {received_time} |\n"
                "| **状态** | {is_read} |\n| **附件** | {has_attachments} |\n\n"
                "> 邮件ID: `{item_id}`\n\n---\n\n## 正文\n\n{body}"
            )

        return template.format(
            subject=subject,
            sender=sender,
            to_recipients=to_recipients,
            cc_row=cc_row,
            sent_time=sent_time,
            received_time=received_time,
            is_read=is_read,
            has_attachments=has_attachments,
            item_id=item_id,
            body=body,
        )

    def format_folders_markdown(self, folders: List[Dict[str, Any]]) -> str:
        """
        将邮箱目录列表格式化为 Markdown 树形结构

        Args:
            folders: get_all_folders 返回的目录列表

        Returns:
            str: Markdown 格式的目录树
        """
        tree_lines: List[str] = []

        def _walk(items: List[Dict[str, Any]], indent: int = 0) -> None:
            for f in items:
                name = f.get('displayName', '未知')
                folder_id = f.get('id', '')
                child_count = f.get('childFolderCount', 0)
                prefix = '  ' * indent + '-'
                suffix = f"（{child_count} 个子目录）" if child_count else ''
                tree_lines.append(f"{prefix} **{name}** `{folder_id}`{suffix}")
                children = f.get('children', [])
                if children:
                    _walk(children, indent + 1)

        _walk(folders)
        folder_tree = '\n'.join(tree_lines)

        template = self._load_template('folders')
        if not template:
            template = "# 📁 邮箱目录\n\n> 共 **{folder_count}** 个顶级目录\n\n{folder_tree}"

        return template.format(
            folder_count=len(folders),
            folder_tree=folder_tree,
        )

    def format_collected_emails_markdown(self, result) -> str:
        """
        将星标邮件查询结果格式化为 Markdown

        Args:
            result: get_collected_email 返回的原始响应（dict，含 itemIdList 和 total）

        Returns:
            str: Markdown 格式的星标邮件列表
        """
        if isinstance(result, dict):
            emails = result.get('itemIdList', [])
            total = result.get('total', len(emails))
        else:
            emails = result
            total = len(emails)

        page_count = len(emails)
        unread_count = sum(1 for e in emails if not e.get('isRead'))

        # 构建表格行
        rows = []
        for i, email in enumerate(emails, 1):
            status = '已读' if email.get('isRead') else '**未读**'
            subject = email.get('subject', '(无主题)')
            form = email.get('from', '未知')
            time = email.get('receivedTime', '未知')
            rows.append(f"| {i} | {status} | {subject} | {form} | {time} |")
        email_rows = '\n'.join(rows)

        # 构建详情区
        details = []
        for i, email in enumerate(emails, 1):
            status = '已读' if email.get('isRead') else '未读'
            subject = email.get('subject', '(无主题)')
            form = email.get('from', '未知')
            to_list = ', '.join(email.get('to', []))
            time = email.get('receivedTime', '未知')
            summary = email.get('summary') or '(无摘要)'
            item_id = email.get('itemId', '')

            detail = (
                f"### [{i}] {subject}\n"
                f"- **发件人**: {form}\n"
                f"- **收件人**: {to_list}\n"
                f"- **时间**: {time}\n"
                f"- **状态**: {status}\n"
                f"- **摘要**: {summary}\n"
                f"- **邮件ID**: `{item_id}`"
            )
            details.append(detail)
        email_details = '\n\n'.join(details)

        template = self._load_template('collected_email_list')
        if not template:
            template = (
                "# ⭐ 星标邮件\n\n"
                "> 共 **{total_count}** 封星标邮件，当前展示 **{page_count}** 封，"
                "其中未读 **{unread_count}** 封\n\n"
                "| # | 状态 | 主题 | 发件人 | 时间 |\n"
                "|:---:|:----:|------|--------|------|\n"
                "{email_rows}\n\n---\n\n"
                "## 邮件详情\n\n{email_details}\n"
            )

        return template.format(
            total_count=total,
            page_count=page_count,
            unread_count=unread_count,
            email_rows=email_rows,
            email_details=email_details,
        )
