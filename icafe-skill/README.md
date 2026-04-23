# iCafe Skill - Python SDK for iCafe Card Operations

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.1-orange.svg)](setup.py)

> 一个功能完整的 Python SDK，用于与百度 iCafe 卡片管理系统进行交互。支持卡片查询、创建、修改、评论管理等全生命周期操作，并提供智能字段验证、状态转换检测和辅助填写功能。

---

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [可执行脚本](#可执行脚本)
- [项目结构](#项目结构)
- [测试](#测试)
- [注意事项](#注意事项)
- [相关链接](#相关链接)

---

## 特性

### 核心能力
| 功能 | 描述 | 状态 |
|------|------|------|
| 卡片查询 | 单卡片查询、批量查询、IQL 表达式、研发数据链查询 | ✅ |
| 卡片创建 | 批量创建卡片，支持字段验证和智能提示 | ✅ |
| 卡片修改 | 更新字段、状态流转，支持 dry-run 预览 | ✅ |
| 评论管理 | 查询、创建、更新卡片评论 | ✅ |
| 字段验证 | 自动获取类型配置，验证必填字段 | ✅ |
| 辅助填写 | 智能提示必填字段和可选值 | ✅ |
| 状态检测 | 智能检测状态转换所需的必填字段 | ✅ |

### 技术特性
- 配置文件认证 - 支持配置文件、显式传参
- 自动重试机制 - 网络错误自动重试，指数退避
- 详细日志 - 可配置的日志级别，便于调试
- 配置缓存 - 自动缓存空间配置，减少 API 调用
- 状态转换缓存 - 自动缓存状态转换必填字段信息

---

## 安装

### 方式一：从源码安装

```bash
git clone https://github.com/baidu/icafe-skill.git
cd icafe-skill
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 方式二：使用 pip 安装（开发模式）

```bash
pip install -e .
```

### 依赖要求

- Python 3.8+
- requests >= 2.31.0
- pyyaml >= 6.0
- click >= 8.1.0

---

## 快速开始

### 1. 配置认证信息

```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config/config.yaml 填入你的认证信息
```

### 2. 第一个查询

```python
from icafe_skill import init_client
from icafe_skill.query import get_card, list_cards

# 初始化客户端
client = init_client(config_file="config/config.yaml")

# 查询单张卡片
card = get_card(client, space_id="my-space", card_id="123")
print(f"{card.title}: {card.status}")

# 列出卡片
cards = list_cards(client, space_id="my-space", max_records=5)
for c in cards:
    print(f"  - [{c.full_id}] {c.title}")

client.close()
```

详细 API 使用方法请参阅 [API 文档](docs/API.md)。

---

## 可执行脚本

scripts/ 目录下提供独立可执行脚本：

### 查询卡片
```bash
# 查询卡片基本信息
python scripts/query_card.py --space my-space --id 123

# 查询卡片并获取研发数据链
python scripts/query_card.py --space my-space --id 123 --devinfo

# 查询卡片并获取评论列表
python scripts/query_card.py --space my-space --id 123 --comments

# JSON 格式输出
python scripts/query_card.py --space my-space --id 123 --format json

# 批量查询卡片列表
python scripts/query_card.py --space my-space --list

# 使用 IQL 查询卡片列表
python scripts/query_card.py --space my-space --list --iql "流程状态=新建"

# 排序查询（按最后修改时间倒序）
python scripts/query_card.py --space my-space --list --order lastModifiedTime --desc

# 显示卡片详情和关联卡片
python scripts/query_card.py --space my-space --list --detail --associations

# 显示子卡片和 OKR 信息
python scripts/query_card.py --space my-space --list --children --okr

# 限制返回数量
python scripts/query_card.py --space my-space --list --limit 50
```

### 创建卡片
```bash
# 预览创建（默认模式）
python scripts/create_card.py --space my-space --title "新任务" --type Story --creator zhangsan

# 执行创建
python scripts/create_card.py --space my-space --title "新任务" --type Story --creator zhangsan --execute

# 带更多字段创建
python scripts/create_card.py --space my-space --title "新Bug" --type Bug --creator zhangsan --assignee lisi --priority "P1-High" --execute
```

### 创建带父卡片的卡片

```python
from icafe_skill import ICafeClient, AuthConfig
from icafe_skill.create import create_cards
from icafe_skill.models import Issue

auth = AuthConfig.from_file("config/config.yaml")
client = ICafeClient(auth)

# 创建带父卡片的卡片
issue = Issue.create(
    title="子任务",
    detail="父任务的子任务",
    type="Task",
    creator="username",
    parent="12345"  # 父卡片序号
)

result = create_cards(client, "my-space", [issue], dry_run=False)
```

### 创建跨空间父卡片的子卡片

```python
# 父卡片在其他空间
issue = Issue.create(
    title="跨空间子任务",
    detail="父卡片在另一个空间",
    type="Task",
    creator="username",
    parent="67890",
    parent_space_prefix_code="parent-space"  # 父卡片所属空间
)

result = create_cards(client, "my-space", [issue], dry_run=False)
```

### 创建带关联卡片的卡片

```python
# 关联到其他卡片（可批量关联）
issue = Issue.create(
    title="相关任务",
    detail="关联到其他卡片",
    type="Task",
    creator="username",
    rel_issue_space_pre_seq="space1-123,space2-456"  # 空间标识-卡片序号
)

result = create_cards(client, "my-space", [issue], dry_run=False)
```

### 更新卡片
```bash
# 预览更新（不执行）
python scripts/update_card.py --space my-space --id 123 --status "开发中" --preview

# 执行更新
python scripts/update_card.py --space my-space --id 123 --status "开发中" --execute

# 更新多个字段
python scripts/update_card.py --space my-space --id 123 --status "已修复" \
  --field "Bug分析结论" "需专业线修复" --field "Bug问题原因" "代码逻辑问题" --execute

# 状态转换缺少必填字段时，会显示详细提示
python scripts/update_card.py --space edc-scrum --id 352568 --status "已验证待上线-云端" --execute
```

### 检测必填字段

使用 `detect_required_fields.py` 智能检测状态转换所需的必填字段：

```bash
# 检测流转到目标状态需要的必填字段
python scripts/detect_required_fields.py --space my-space --id 123 --status "已修复"

# 增加样本卡片数量以提高准确性
python scripts/detect_required_fields.py --space my-space --id 123 --status "已修复" --max-samples 5

# 应用建议的字段值并更新卡片（交互式）
python scripts/detect_required_fields.py --space my-space --id 123 --status "已修复" --apply
```

### 工作流验证

`check_workflow.py` 读取 `config/config.yaml` 中的 workflow 配置，验证状态转换规则：

```bash
# 验证 Bug 类型的状态转换（默认）
python scripts/check_workflow.py --from "新建" --to "已分配"

# 验证指定类型的状态转换
python scripts/check_workflow.py --type Story --from "新建" --to "开发中"

# 查看当前状态可流转的所有下个状态
python scripts/check_workflow.py --from "新建"

# 列出当前类型的所有状态节点
python scripts/check_workflow.py --list-nodes

# 显示当前类型的完整流转规则
python scripts/check_workflow.py --show-rules
```

### 字段配置管理

`field_config.py` 脚本用于查询和验证 iCafe 空间的字段配置：

```bash
# 查询空间的问题类型列表
python scripts/field_config.py types --space my-space

# 查询指定类型的字段配置
python scripts/field_config.py fields --space my-space --type Bug

# 验证字段数据
python scripts/field_config.py validate --space my-space --type Bug \
  --fields '{"Bug分析结论": "需专业线修复"}'

# 强制刷新缓存
python scripts/field_config.py fields --space my-space --type Bug --refresh
```

### 批量操作
```bash
# 使用 IQL 批量查询卡片
python scripts/batch_operations.py --space my-space --iql "优先级=P0"

# 批量查询并限制数量
python scripts/batch_operations.py --space my-space --iql "流程状态=新建" --limit 50

# 按排序字段查询
python scripts/batch_operations.py --space my-space --order lastModifiedTime

# 显示状态统计摘要
python scripts/batch_operations.py --space my-space --status-summary

# JSON 格式输出
python scripts/batch_operations.py --space my-space --status-summary --format json
```

### 规划状态流转
```bash
# 一次性获取完整的状态流转计划
python scripts/plan_transition.py --space my-space --id 123 --to "已修复"

# JSON 格式输出
python scripts/plan_transition.py --space my-space --id 123 --to "已修复" --format json

# 增加样本数量提高建议准确性
python scripts/plan_transition.py --space my-space --id 123 --to "已修复" --max-samples 5
```

该脚本会返回：
- 流转路径（可能需要多步）
- 每步的必填字段和建议值
- 可直接执行的命令

### 脚本参数说明

| 脚本 | 常用参数 | 说明 |
|------|---------|------|
| `query_card.py` | `--space`, `--id`, `--list`, `--iql`, `--order`, `--desc`, `--detail`, `--associations`, `--children`, `--okr`, `--accumulate`, `--limit`, `--devinfo`, `--comments`, `--format` | 查询单个卡片或卡片列表 |
| `create_card.py` | `--space`, `--title`, `--type`, `--creator`, `--execute` | 创建卡片，默认 dry-run |
| `update_card.py` | `--space`, `--id`, `--status`, `--field`, `--preview`, `--execute` | 更新卡片 |
| `detect_required_fields.py` | `--space`, `--id`, `--status`, `--apply`, `--format` | 检测必填字段 |
| `check_workflow.py` | `--from`, `--to`, `--type`, `--list-nodes`, `--show-rules` | 验证工作流 |
| `field_config.py` | `types`, `fields`, `validate`, `--format`, `--refresh` | 字段配置管理 |
| `plan_transition.py` | `--space`, `--id`, `--to`, `--max-samples`, `--format` | 规划状态流转 |
| `batch_operations.py` | `--space`, `--iql`, `--limit`, `--order`, `--status-summary`, `--format` | 批量查询和状态统计 |

---

## 项目结构

```
icafe-skill/
├── icafe_skill/              # 核心包
│   ├── __init__.py          # 包初始化和导出
│   ├── auth.py              # 认证管理
│   ├── client.py            # HTTP 客户端
│   ├── models.py            # 数据模型
│   ├── exceptions.py        # 自定义异常
│   ├── query.py             # 查询模块
│   ├── create.py            # 创建模块
│   ├── update.py            # 修改模块
│   ├── utils.py             # 工具函数
│   ├── field_config.py      # 字段配置管理
│   └── helpers.py           # 辅助创建函数
├── scripts/                 # 可执行脚本
│   ├── query_card.py        # 查询卡片
│   ├── create_card.py       # 创建卡片
│   ├── update_card.py       # 更新卡片
│   ├── detect_required_fields.py  # 检测必填字段
│   ├── field_config.py      # 字段配置管理
│   ├── check_workflow.py    # 工作流验证
│   ├── plan_transition.py   # 规划状态流转
│   └── batch_operations.py  # 批量操作
├── tests/                   # 测试目录
├── config/
│   ├── config.yaml.example  # 配置模板
│   └── config.yaml          # 配置文件
├── docs/
│   └── API.md               # 详细 API 文档
├── references/              # 参考文档
│   ├── general-guide.md     # 通用指南
│   ├── transition-to-fixed.md   # 流转到修复状态
│   └── transition-to-nonbug.md  # 流转到非Bug状态
├── requirements.txt         # 依赖列表
├── setup.py                 # 安装配置
├── README.md                # 项目说明
└── SKILL.md                 # 技能使用文档
```

---

## 测试

### 运行所有测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 基础功能测试
python test_query_basic.py

# 完整功能测试
python test_all_features.py

# 字段验证测试
python test_field_validation.py
```

### 测试环境配置

```bash
# 测试空间: edc-scrum
# 测试卡片: 352568
# 测试账号: v_chenzhaojun
```

---

## 注意事项

### 使用限制

1. **禁止直接调用底层 API**：不要创建 path 直接调用 `client.get()` 函数
2. **预览模式**：所有写操作（创建、修改）建议先使用 `dry_run=True` 或 `--preview` 预览，确认无误后再执行
3. **字段验证**：建议在创建卡片前使用 `validate_card_data()` 或 `field_config.py validate` 验证字段
4. **状态流转**：某些状态切换需要填写必填字段，使用 `detect_required_fields.py` 检测所需字段
5. **字段值限制**：单选字段（radio_field）和多选字段（select_list_multiple）必须从预定义选项中选择
6. **状态转换缓存**：状态转换所需的字段信息会自动缓存到 `.cache/` 目录，避免重复 API 失败

### 测试阶段限制

1. **只读操作安全** - 所有查询功能完全可用
2. **写操作保护** - 创建、修改操作默认为 `dry_run=True`
3. **数据安全** - 测试阶段禁止修改实际卡片数据

### 错误处理

详细的异常类型和错误处理方法请参阅 [API 文档 - 异常类型](docs/API.md#异常类型)。

---

## 相关链接

- [iCafe 官方文档](https://console.cloud.baidu-int.com/devops/icafe)
- [详细 API 文档](docs/API.md)
- [状态流转指南](references/)

---

<div align="center">

**Made by iCafe Team**

</div>
