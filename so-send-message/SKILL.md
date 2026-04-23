---
name: so-send-message
description: 向如流(Hi)发送群组或单人消息的技能。支持发送文本、Markdown和图片消息。当用户需要向群组或特定用户发送通知、告警、报告、更新或其他类型的消息时使用此技能。适用于运维通知、团队协作、监控告警、自动化报告等场景。（无需app Key \ app Secret , 脚本内已内置）
---

# 消息发送技能 (群组/单人)

## 概述

本技能提供向如流(Hi)发送群组消息和单人消息的能力，支持文本、Markdown和图片三种消息格式。
- **群消息**: 基于如流开放平台的机器人API实现 (`/api/v1/robot/msg/groupmsgsend`)
- **单人消息**: 基于应用消息接口实现 (`/app/message/send`)，支持通过用户名直接发送，无需查询 UserID。

> **📢 开箱即用**: 本技能已内置默认应用凭证，无需任何配置即可直接使用。只需指定 `--group-id` 或 `--user` 即可发送消息。

## 快速开始

### 安装依赖
```bash
~/py312/bin/pip install requests
```

### 基本使用

#### 发送群消息

1. **发送Markdown消息（推荐）**
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --group-id "群组ID" --content "# 标题\n\n消息内容" --type md
   ```

2. **发送文本消息**
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --group-id "群组ID" --content "普通文本消息" --type text
   ```

3. **发送图片消息**
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --group-id "群组ID" --image-url "https://example.com/image.jpg" --type image
   ```

#### 发送单人消息

1. **发送给单个用户**
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --user "zhangsan" --content "你好，这是单人消息" --type text
   ```

2. **发送给多个用户**
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --user "zhangsan|lisi" --content "# 标题\n\n重要通知" --type md
   ```

3. **发送图片给用户** (自动下载图片并转Base64发送)
   ```bash
   ~/py312/bin/python3 scripts/send_message.py --user "zhangsan" --image-url "https://example.com/image.jpg" --type image
   ```

## 核心功能

### 1. 消息类型支持

- **Markdown消息**：支持丰富的格式化文本，适合发送结构化内容
- **文本消息**：普通纯文本消息
- **图片消息**：发送网络图片到群组

### 2. 认证管理

- 自动获取和管理应用访问令牌
- Token过期自动刷新
- 支持自定义应用凭证（优先读取环境变量 `INFOFLOW_APP_KEY` 和 `INFOFLOW_APP_SECRET`）

### 3. 错误处理

- 完善的错误处理和重试机制
- 详细的日志记录
- 友好的错误提示

## 详细使用

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--group-id` | 目标群组ID（与`--user`二选一） | `--group-id "123456789"` |
| `--user` | 目标用户名，多个用\|分隔（与`--group-id`二选一） | `--user "zhangsan\|lisi"` |
| `--content` | 消息内容（text/md类型必需） | `--content "Hello World"` |
| `--type` | 消息类型：text/md/image | `--type md` |
| `--image-url` | 图片URL（image类型必需） | `--image-url "https://example.com/img.jpg"` |
| `--app-key` | 应用Key（可选，优先读取环境变量 `INFOFLOW_APP_KEY`，否则使用内置默认值） | 一般无需指定 |
| `--app-secret` | 应用Secret（可选，优先读取环境变量 `INFOFLOW_APP_SECRET`，否则使用内置默认值） | 一般无需指定 |
| `--verbose` | 详细输出模式 | `--verbose` |

### Python API使用

```python
from scripts.send_message import GroupMessageSender

# 创建发送器（已内置默认凭证，无需传入参数）
sender = GroupMessageSender()

# 1. 发送群消息
# 发送Markdown消息
result = sender.send_md_message(
    group_id="123456789",
    content="# 标题\n\n**重要通知**\n\n请查收今日报告。"
)

# 2. 发送单人/多人消息
# 发送Markdown消息给多个用户
result = sender.send_app_message(
    to_users="zhangsan|lisi",
    msg_type="markdown",
    content="# 标题\n\n**个人通知**\n\n请处理待办事项。"
)

# 发送文本消息
result = sender.send_app_message(
    to_users="zhangsan",
    msg_type="text",
    content="简单文本通知"
)

# 发送文本消息
result = sender.send_text_message(
    group_id="123456789",
    content="简单文本通知"
)

# 发送图片消息
result = sender.send_image_message(
    group_id="123456789",
    image_url="https://example.com/image.jpg"
)
```

## 使用场景

### 1. 运维通知

```bash
# 发送系统维护通知
~/py312/bin/python3 scripts/send_message.py --group-id "运维群" --type md --content """
🔄 **系统维护通知**

**系统**: 支付系统
**时间**: 今晚 22:00-24:00
**影响**: 服务将会有短暂中断
**联系人**: 张三
"""
```

### 2. 监控告警

```bash
# 发送监控告警
~/py312/bin/python3 scripts/send_message.py --group-id "监控群" --type md --content """
🔴 **监控告警**

**系统**: 数据库集群
**级别**: P1
**时间**: $(date '+%Y-%m-%d %H:%M:%S')
**内容**: CPU使用率超过90%
**建议**: 立即检查
"""
```

### 3. 自动化报告

```bash
# 发送日报
~/py312/bin/python3 scripts/send_message.py --group-id "日报群" --type md --content """
📊 **系统健康日报** - $(date '+%Y-%m-%d')

**总体状态**: ✅ 正常

**子系统状态**:
```
| 系统 | 状态 | 可用性 | 响应时间 |
|------|------|--------|----------|
| 网关 | ✅ | 99.99% | 45ms |
| 支付 | ✅ | 99.98% | 120ms |
| 用户 | ✅ | 99.97% | 85ms |
```
"""
```

### 4. 团队协作

```bash
# 发送会议通知
~/py312/bin/python3 scripts/send_message.py --group-id "项目群" --type md --content """
📅 **项目周会通知**

**时间**: 周五 14:00-15:00
**地点**: 会议室A / 如流会议
**议题**:
1. 上周工作回顾
2. 本周计划
3. 风险讨论
"""
```

## 消息模板

### 常用模板

更多模板请参考：[消息模板库](references/message_templates.md)

#### 故障通告模板
```markdown
🚨 **故障通告**

**故障等级**: P{等级}
**影响系统**: {系统名称}
**开始时间**: {开始时间}
**影响范围**: {影响范围}

**应急处理**:
1. {步骤1}
2. {步骤2}

**联系人**: {联系人}
```

#### 变更通知模板
```markdown
🔄 **变更通知**

**变更**: {变更名称}
**系统**: {系统名称}
**时间**: {变更时间}
**影响**: {影响范围}
**回滚计划**: {回滚方案}
```

#### 日报模板
```markdown
📊 **每日简报** - {日期}

**关键指标**:
```
| 指标 | 值 | 状态 |
|------|-----|------|
| 可用性 | {值} | {状态} |
| 成功率 | {值} | {状态} |
```

**今日告警**: {告警统计}
```

## 高级功能

### 1. 批量发送

```bash
#!/bin/bash
# 批量发送消息到多个群组
GROUPS=("群组ID1" "群组ID2" "群组ID3")
MESSAGE="重要通知：系统将于今晚进行维护"

for GROUP in "${GROUPS[@]}"; do
    echo "发送到群组: $GROUP"
    ~/py312/bin/python3 scripts/send_message.py --group-id "$GROUP" --content "$MESSAGE" --type md
    sleep 1  # 避免频率限制

done
```

### 2. 定时发送

使用cron定时任务：

```bash
# 每天9点发送日报
0 9 * * * cd /path/to/skill && ~/py312/bin/python3 scripts/send_message.py --group-id "日报群" --content "日报内容" --type md
```

### 3. 集成到其他系统

```python
#!/usr/bin/env python3
import subprocess
import json

# 从监控系统获取告警
alert_data = {
    "system": "数据库",
    "level": "P1",
    "message": "CPU使用率超过90%",
    "time": "2024-01-15 10:30:00"
}

# 生成Markdown消息
content = f"""
🔴 **监控告警**

**系统**: {alert_data['system']}
**级别**: {alert_data['level']}
**时间**: {alert_data['time']}
**内容**: {alert_data['message']}
"""

# 调用发送脚本
result = subprocess.run([
    "~/py312/bin/python3", "scripts/send_message.py",
    "--group-id", "监控群",
    "--type", "md",
    "--content", content
], capture_output=True, text=True)

print("发送结果:", result.stdout)
```

## 配置说明

### 群组ID获取

1. 在如流中打开目标群组
2. 点击群组设置
3. 查找群组ID（通常为一串数字）

## 错误排查

### 常见问题

1. **认证失败**
   - 检查网络连接是否正常
   - 如使用自定义凭证，请确认app_key和app_secret是否正确

2. **发送失败**
   - 确认机器人已加入目标群组
   - 检查机器人是否被禁言
   - 确认群组ID是否正确

3. **消息被过滤**
   - 检查是否包含敏感词
   - 缩短消息长度
   - 简化消息格式

### 调试模式

使用`--verbose`参数查看详细日志：

```bash
~/py312/bin/python3 scripts/send_message.py --group-id "群组ID" --content "测试" --type md --verbose
```

## API参考

详细API文档请参考：[API参考文档](references/api_reference.md)

## 限制说明

1. **频率限制**：单个机器人每分钟最多30条消息
2. **消息长度**：
   - 文本：最大2000字符
   - Markdown：最大5000字符
3. **图片限制**：最大10MB，建议尺寸不超过2000x2000像素
4. **Token有效期**：7200秒（2小时）

## 最佳实践

1. **使用Markdown格式**：提高消息可读性和信息密度
2. **添加表情图标**：快速传达消息类型和紧急程度
3. **结构化内容**：使用标题、列表、表格等格式化元素
4. **控制发送频率**：避免触发频率限制
5. **错误重试**：对临时失败进行重试
6. **日志记录**：记录所有发送操作以便审计

## 示例集合

### 完整示例脚本

```python
#!/usr/bin/env python3
"""
完整示例：发送系统健康报告
"""
import sys
sys.path.append('.')

from scripts.send_message import GroupMessageSender
from datetime import datetime

def generate_health_report():
    """生成系统健康报告"""
    systems = [
        {"name": "网关服务", "status": "✅ 正常", "availability": "99.99%", "response_time": "45ms"},
        {"name": "支付服务", "status": "✅ 正常", "availability": "99.98%", "response_time": "120ms"},
        {"name": "用户服务", "status": "⚠️ 警告", "availability": "99.95%", "response_time": "85ms"},
    ]
    
    # 生成表格
    table_rows = []
    for system in systems:
        table_rows.append(f"| {system['name']} | {system['status']} | {system['availability']} | {system['response_time']} |")
    
    table = "\n".join(table_rows)
    
    return f"""📊 **系统健康报告** - {datetime.now().strftime('%Y-%m-%d %H:%M')}

**总体状态**: ✅ 运行正常

**详细状态**:
```
| 系统 | 状态 | 可用性 | 响应时间 |
{table}
```

**告警统计**:
- P0告警: 0
- P1告警: 0
- P2告警: 1

**建议**: 检查用户服务响应时间
"""

if __name__ == "__main__":
    # 群组ID（根据实际情况修改）
    GROUP_ID = "your_group_id"
    
    # 创建发送器（已内置默认凭证，无需传入参数）
    sender = GroupMessageSender()
    
    # 生成并发送报告
    report = generate_health_report()
    result = sender.send_md_message(GROUP_ID, report)
    
    if result.get('code') == 'ok':
        print("✅ 报告发送成功")
    else:
        print(f"❌ 发送失败: {result}")
```