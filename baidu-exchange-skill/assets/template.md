<!-- ==================== EMAIL_LIST ==================== -->
<!-- TEMPLATE: email_list -->

# 📬 {folder_name}

> 共 **{total_count}** 封邮件，当前展示 **{page_count}** 封，其中未读 **{unread_count}** 封

| # | 状态 | 主题 | 发件人 | 时间 |
|:---:|:----:|------|--------|------|
{email_rows}

---

## 邮件详情

{email_details}

<!-- END: email_list -->

<!-- ==================== EMAIL_DETAIL ==================== -->
<!-- TEMPLATE: email_detail -->

# 📧 {subject}

| 字段 | 内容 |
|:----:|------|
| **发件人** | {from} |
| **收件人** | {to_recipients} |
{cc_row}| **发送时间** | {sent_time} |
| **接收时间** | {received_time} |
| **状态** | {is_read} |
| **附件** | {has_attachments} |

> 邮件ID: `{item_id}`

---

## 正文

{body}

<!-- END: email_detail -->

<!-- ==================== FOLDERS ==================== -->
<!-- TEMPLATE: folders -->

# 📁 邮箱目录

> 共 **{folder_count}** 个顶级目录

{folder_tree}

<!-- END: folders -->

<!-- ==================== COLLECTED_EMAIL_LIST ==================== -->
<!-- TEMPLATE: collected_email_list -->

# ⭐ 星标邮件

> 共 **{total_count}** 封星标邮件，当前展示 **{page_count}** 封，其中未读 **{unread_count}** 封

| # | 状态 | 主题 | 发件人 | 时间 |
|:---:|:----:|------|--------|------|
{email_rows}

---

## 邮件详情

{email_details}

<!-- END: collected_email_list -->
