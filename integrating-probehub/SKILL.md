---
name: integrating-probehub
description: ProbeHub 分布式任务调度平台接入工具。支持 Agent 注册与管理、任务触发与执行、Cron 定时任务配置、报警通知设置、执行日志查看。当用户需要接入 ProbeHub、管理任务代理、配置定时任务或监控任务执行时使用。
---

# ProbeHub Agent 接入

## 概述

ProbeHub 是一个分布式任务调度和监控平台，支持：
- 🔌 **低成本接入**：一键装饰器注册，复杂配置 JSON 化
- 🔒 **数据安全**：本地数据管理，无泄漏风险
- ⚙️ **动态配置**：JSON 参数配置，灵活装备场景
- ⏰ **定时任务**：Cron 表达式，多规则支持
- 📊 **实时监控**：执行状态实时查看，日志输出
- 🏷️ **批量计算**：选择标签批量执行，环境管理

## 参数

### 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `puid` | 项目密钥 | 从 [ProbeHub 前端](https://probehub.now.baidu-int.com/) 获取 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `host` | Agent 监听地址 | `0.0.0.0` |
| `port` | Agent 监听端口 | `8088` |
| `tag` | 任务标签 | `default` |
| `timeout` | API 请求超时（秒） | `30` |

### 环境变量支持
```bash
export PROBEHUB_PUID="your-project-key"
```

### 交互流程
1. 检查是否已提供项目密钥 `puid`
2. 缺失时，一次性提示：
   ```
   检测到参数缺失：
   - puid: 请提供项目密钥（从 https://probehub.now.baidu-int.com/ 获取）
   输入 "help" 查看详细说明
   ```
3. 获取参数后，复述确认再执行

---

## 安全注意事项

> **重要**: ProbeHub 接入涉及项目密钥，请遵循以下安全规范

| 风险类型 | 说明 | 建议措施 |
|---------|------|---------|
| 🔑 密钥泄露 | PUID 可能被记录到日志 | 使用环境变量 `PROBEHUB_PUID` |
| 🌐 网络安全 | API 调用可能被拦截 | 生产环境使用 HTTPS |
| 📡 日志敏感 | 详细模式可能输出敏感数据 | 生产环境禁用 `-v` |
| 🔓 端口暴露 | Agent 端口可能被扫描 | 配置防火墙规则 |

---

## 支持的功能

### 基础命令
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `health` | 检查 ProbeHub 服务健康状态 | 无 |

### Agent 管理
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `register` | 注册并启动 Agent（使用 SDK） | `--puid`, `--name` |
| `heartbeat` | 发送心跳 | `--agent-id` |
| `list-agents` | 获取 Agent 列表 | `--project-id` |
| `delete-agent` | 删除 Agent | `--agent-id` |

### 任务管理
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `trigger` | 触发任务执行 | `--agent-id`, `--task-name` |
| `batch-trigger` | 批量触发任务 | `--tag`, `--project-id` |
| `task-log` | 获取执行日志 | `--execution-id` |
| `task-results` | 查询任务结果 | `--agent-id` |

### 定时任务
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `create-schedule` | 创建定时任务 | `--agent-id`, `--task-name`, (`--cron` 或 `--interval`) |
| `list-schedules` | 获取定时任务列表 | `--agent-id` |
| `pause-schedule` | 暂停定时任务 | `--agent-id`, `--schedule-id` |
| `resume-schedule` | 恢复定时任务 | `--agent-id`, `--schedule-id` |
| `delete-schedule` | 删除定时任务 | `--agent-id`, `--schedule-id` |

### 报警管理
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `alarm-config` | 获取/设置报警配置 | `--project-id` |
| `alarm-test` | 测试报警渠道 | `--channel` (JSON，需含 channel 字段) |
| `alarm-history` | 获取报警历史 | `--project-id`（可选） |

### 工具命令
| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `generate-template` | 生成 Agent 代码模板 | `--output` |

---

## 环境预检

```bash
# 要求: Python 3.7+
~/py312/bin/python3 --version

# 安装依赖
~/py312/bin/pip install requests
~/py312/bin/pip install probehub-agent -i http://pip.baidu-int.com/simple/ --trusted-host pip.baidu-int.com

# 验证 probehub-agent SDK 安装
~/py312/bin/python3 -c "from probehub_agent import TaskAgent; print('✅ probehub-agent SDK 已安装')"

# 验证服务连通性
~/py312/bin/python3 scripts/probehub_cli.py health
```

> **注意**: `register` 命令依赖 `probehub-agent` SDK，如未安装会提示：
> ```
> ❌ 需要安装 probehub-agent:
>    ~/py312/bin/pip install probehub-agent -i http://pip.baidu-int.com/simple/ --trusted-host pip.baidu-int.com
> ```

---

## 执行步骤

### Agent 注册流程

#### Step 1: 确认参数
确认项目密钥 `puid` 已提供
**检查点**: 参数齐全

#### Step 2: 注册并启动 Agent
```bash
~/py312/bin/python3 scripts/probehub_cli.py register \
  --puid "$PROBEHUB_PUID" \
  --name "my-agent" \
  --port 8088
```
**检查点**: Agent 启动成功并自动注册

#### Step 3: 验证注册
```bash
~/py312/bin/python3 scripts/probehub_cli.py --project-id "your-project-id" list-agents
```
**检查点**: Agent 出现在列表中

### 任务触发流程

> **说明**: 任务执行是**异步**的。调用 `trigger` 命令会立即返回 `execution_id`，然后可以用此 ID 查询执行结果。

#### Step 1: 获取 Agent ID
Agent ID 可以从以下位置获取：
- Agent 启动时的日志输出
- `list-agents` 命令返回的列表
- ProbeHub 前端页面

#### Step 2: 触发任务
```bash
~/py312/bin/python3 scripts/probehub_cli.py --puid "$PROBEHUB_PUID" trigger \
  --agent-id "$AGENT_ID" \
  --task-name "test_task" \
  --params '{"key": "value"}'
```
**检查点**: 返回 `execution_id`（立即返回，任务在后台执行）

#### Step 3: 查看执行日志
```bash
~/py312/bin/python3 scripts/probehub_cli.py task-log \
  --execution-id "$EXECUTION_ID"
```
**检查点**: 显示执行日志（任务执行完成后可查询）

> **提示**: `execution_id` 会在 `trigger` 命令的输出中返回，也可在 Agent SDK 日志或 ProbeHub 前端查看。

### 定时任务流程

#### Step 1: 创建定时任务
```bash
~/py312/bin/python3 scripts/probehub_cli.py create-schedule \
  --puid "$PROBEHUB_PUID" \
  --agent-id "$AGENT_ID" \
  --task-name "daily_task" \
  --cron "0 9 * * *"
```
**检查点**: 返回定时任务 ID

#### Step 2: 验证创建
```bash
~/py312/bin/python3 scripts/probehub_cli.py list-schedules --agent-id "$AGENT_ID"
```
**检查点**: 定时任务出现在列表中

### 本地 Agent 服务


#### 方式 1: 装饰器注册（推荐）
```python
from probehub_agent import TaskAgent

agent = TaskAgent(
    puid="xxx"
)

@agent.task_decorator(description="测试任务", tag="pre")
def test():
    print("hello")

# Agent 启动后会自动向 ProbeHub 注册
agent.start(host="0.0.0.0", port=8088)
```

#### 方式 2: 注册已有函数
```python
from probehub_agent import TaskAgent
from my_module import existing_task

agent = TaskAgent(puid="xxx")
agent.task_decorator(existing_task, description="已有任务", tag="pre")
agent.start(host="0.0.0.0", port=8088)
```

#### 方式 3: 使用模板生成
```bash
# 生成 Agent 模板
~/py312/bin/python3 scripts/probehub_cli.py generate-template --output my_agent.py

# 修改模板中的 PUID，添加任务后运行
~/py312/bin/python3 my_agent.py
```

---

## 异常处理

CLI 工具会自动捕获并显示友好的错误提示，包括参数缺失、网络超时、认证失败(401)、资源不存在(404)等常见异常。

---

## 示例

### 注册并启动 Agent
```bash
export PROBEHUB_PUID="your-project-key"
~/py312/bin/python3 scripts/probehub_cli.py register --name "my-agent" --port 8088
# 输出: 🚀 Agent 启动成功，自动向 ProbeHub 注册
```

### 创建定时任务
```bash
~/py312/bin/python3 scripts/probehub_cli.py --puid "xxx" create-schedule --agent-id "xxx" --task-name "daily_task" --cron "0 9 * * *"
```

---

## 快速命令参考

```bash
# 健康检查
~/py312/bin/python3 scripts/probehub_cli.py health

# Agent 管理（register 会启动服务并自动注册）
~/py312/bin/python3 scripts/probehub_cli.py register --puid "xxx" --name "my-agent" --port 8088
~/py312/bin/python3 scripts/probehub_cli.py --project-id "64" list-agents
~/py312/bin/python3 scripts/probehub_cli.py heartbeat --agent-id "xxx"
~/py312/bin/python3 scripts/probehub_cli.py delete-agent --agent-id "xxx"

# 任务管理
~/py312/bin/python3 scripts/probehub_cli.py --puid "xxx" trigger --agent-id "xxx" --task-name "task1" --params '{"key":"val"}'
~/py312/bin/python3 scripts/probehub_cli.py --puid "xxx" --project-id "64" batch-trigger --tag "pre"
~/py312/bin/python3 scripts/probehub_cli.py task-log --execution-id "xxx"
~/py312/bin/python3 scripts/probehub_cli.py task-results --agent-id "xxx"

# 定时任务
~/py312/bin/python3 scripts/probehub_cli.py --puid "xxx" create-schedule --agent-id "xxx" --task-name "task1" --cron "0 9 * * *"
~/py312/bin/python3 scripts/probehub_cli.py list-schedules --agent-id "xxx"
~/py312/bin/python3 scripts/probehub_cli.py pause-schedule --agent-id "xxx" --schedule-id "yyy"
~/py312/bin/python3 scripts/probehub_cli.py resume-schedule --agent-id "xxx" --schedule-id "yyy"
~/py312/bin/python3 scripts/probehub_cli.py delete-schedule --agent-id "xxx" --schedule-id "yyy"

# 报警管理
~/py312/bin/python3 scripts/probehub_cli.py --project-id "64" alarm-config
~/py312/bin/python3 scripts/probehub_cli.py alarm-test --channel '{"channel": "webhook", "url": "xxx"}'
~/py312/bin/python3 scripts/probehub_cli.py --project-id "64" alarm-history

# 生成 Agent 模板
~/py312/bin/python3 scripts/probehub_cli.py generate-template --output my_agent.py
```

---

## 项目结构

```
probehub-agent-integration/
├── SKILL.md                    # 技能定义文件
├── scripts/
│   └── probehub_cli.py         # 命令行工具入口
├── src/
│   ├── __init__.py             # 模块导出与便捷函数
│   ├── manager.py              # ProbeHubManager 工厂类
│   └── client.py               # HTTP API 客户端
├── templates/
│   └── agent_template.py       # Agent 启动模板
└── tests/
    ├── test_agent_script.py    # Agent 启动测试脚本
    ├── test_cli.py             # CLI 命令测试
    └── test_full.py            # 完整功能测试
```

---

### ProbeHub 前端
访问: https://probehub.now.baidu-int.com/
（在此页面获取项目密钥 PUID 和管理项目配置）