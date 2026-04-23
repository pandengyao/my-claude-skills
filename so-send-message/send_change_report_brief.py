# 发送变更报告简报

import sys
import os

# 添加scripts目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from send_message import GroupMessageSender

def generate_brief():
    """生成变更报告简报"""
    content = """# 📊 2026-01-14 变更报告简报

## 📈 核心数据统计

**📊 总变更数**: 20个
**✅ 已结单**: 17个（85%）
**⚠️ 已撤回**: 3个（15%）

## ⚡ 风险分析

**🔴 高风险**: 1个（已撤回）
**⚠️ 中风险**: 6个（30%）
**✅ 低风险**: 12个（60%）

**📊 风险分布**:
- 低风险占60%：反入侵平台-策略中心变更、邮件检测接入kafka等
- 中风险占30%：容器BJDD集群Node节点状态修复、数管credential-vault服务上线等
- 高风险占5%：bjhwcm 不拦截icmp包（已撤回，无影响）

## 👥 用户影响

**🎯 用户有感变更**: 0个
**✅ 无用户影响变更**: 20个（100%）

## 🖥️ 主要系统变更

| 系统 | 变更数 | 风险 |
|------|--------|------|
| 主机安全 | 4个 | 中/低 |
| SOC平台 | 3个 | 低/中 |
| 云安全中心 | 2个 | 中/低 |
| 安全运营平台 | 2个 | 中/低 |
| 反入侵平台 | 2个 | 低 |
| 昊天镜风控 | 2个 | 低 |

## ⚠️ 重点风险项

**高风险变更（已撤回）**:
- bjhwcm 不拦截icmp包【复制】
- 类型：重大变更 | 风险等级：高风险
- 状态：已撤回（未执行）| 无实际影响

**撤回变更分析**:
- 主机安全服务端数据转发上线（中风险）
- 主机安全服务端安全引擎上线（中风险）

## 📋 变更类型分布

**日常变更**: 10个（50%）
**一般变更**: 6个（30%）
**重大变更**: 2个（10%）
**运营变更**: 2个（10%）

## 💡 总结

✅ **整体风险可控**: 95%的变更为中低风险
✅ **用户影响小**: 所有变更均无用户感知
✅ **系统状态稳定**: 无执行中变更

📅 **报告日期**: 2026-01-14
📊 **数据来源**: 变更管理系统
📝 **详细报告**: 已保存至知识库

---
*生成时间: 2026-02-11 | OpenClaw自动化报告"""
    return content

def send_brief_message():
    """发送简报消息到如流群"""
    # 群组ID
    GROUP_ID = "9835790"

    # 创建发送器
    sender = GroupMessageSender()

    # 生成简报内容
    brief_content = generate_brief()

    # 发送Markdown消息
    result = sender.send_md_message(GROUP_ID, brief_content)

    if result.get('code') == 'ok':
        print(f"✅ 简报已成功发送到群组 {GROUP_ID}")
        return True
    else:
        print(f"❌ 发送失败: {result}")
        return False

if __name__ == "__main__":
    send_brief_message()
