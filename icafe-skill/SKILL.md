---
name: icafe-skill
description: "百度 iCafe 项目管理系统操作工具。当用户提及 iCafe、icafe、卡片、工单、Bug流转、状态转换、研发数据链、字段值验证、edc-scrum 等空间ID时触发。支持：查询/创建/修改卡片、状态流转、评论管理、字段验证、批量处理。用户说'卡片状态''Bug分析结论''流转到已修复/已关闭'等均应使用此技能。"
metadata:
  author: "iCafe Team"
  version: "0.4.3"
  category: "tool"
  tags:
    - icafe
    - card
    - project-management
    - python
    - automation
    - plan
  create_time: "2026-01-01"
---

# iCafe Skill

iCafe 卡片管理 SDK，用于与百度 iCafe 项目管理系统进行交互。

## 核心能力

此技能支持以下操作：

| 功能     | 描述                                           |
| -------- | ---------------------------------------------- |
| 查询卡片 | 单卡片查询、批量查询、IQL 查询、研发数据链     |
| 创建卡片 | 支持字段验证、父卡片关联、跨空间配置、卡片关联 |
| 修改卡片 | 状态流转、字段更新、评论管理                   |
| 状态流转 | 遵循工作流规则的智能状态转换                   |
| 字段验证 | 验证字段值是否符合预定义选项                   |
| 批量操作 | 批量查询、状态统计                             |
| 计划管理 | 查询/创建/更新计划、里程碑查询                 |

## 环境配置

> **首次使用前检查**：确保 `config/config.yaml` 已存在。如不存在，参考 [通用指南 - 环境初始化](references/general-guide.md#环境初始化) 完成配置。

安装依赖：
```bash
~/py312/bin/pip install -e .
```

## 字段解析

从用户输入中解析 `space_id` 和 `card_id`。格式如 `edc-scrum-352568` 自动解析为：
- `space_id`: `edc-scrum`
- `card_id`: `352568`

**重要**：字段值必须符合 iCafe 系统的预定义选项

| 字段类型                      | 说明     | 格式要求                              |
| ----------------------------- | -------- | ------------------------------------- |
| `radio_field` / `select_list` | 单选字段 | 必须从预定义选项中选择                |
| `select_list_multiple`        | 多选字段 | 必须从预定义选项中选择                |
| `date_time`                   | 日期时间 | `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS` |
| `user_picker`                 | 用户选择 | 有效的用户名                          |

验证字段值：
```bash
# 查看字段的所有合法选项
~/py312/bin/python3 scripts/field_config.py fields --space edc-scrum --type Bug

# 验证字段值
~/py312/bin/python3 scripts/field_config.py validate --space edc-scrum --type Bug --fields '{"Bug分析结论": "需专业线修复"}'
```

## 典型工作流

### 工作流 1：创建卡片

```bash
# 预览模式（推荐先预览）
~/py312/bin/python3 scripts/create_card.py --space my-space --title "任务标题" --type Story

# 执行创建
~/py312/bin/python3 scripts/create_card.py --space my-space --title "任务标题" --type Story --creator username --execute

# 创建带父卡片的子卡片
~/py312/bin/python3 scripts/create_card.py --space my-space --title "子任务" --type Task \
  --creator username --parent 12345 --execute
```

详细示例请参阅 [卡片创建示例](references/card-creation-examples.md)。

### 工作流 2：状态流转

**推荐方式**：使用 `plan_transition.py` 一次性获取完整流转计划

```bash
# 获取流转路径、必填字段建议、执行命令
~/py312/bin/python3 scripts/plan_transition.py --space edc-scrum --id 354705 --to "已修复"
```

输出包含：
- 流转路径（新建 → 已分配 → 已分析 → 已修复）
- 推荐字段值（从样本卡片智能推断）
- 可直接执行的命令

### 工作流 3：查询卡片

```bash
# 基本查询
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --id 354705

# 查看自定义字段（Bug问题原因、Bug分析结论、Bug修复方案等）
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --id 354705 --fields

# 查看研发数据链
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --id 354705 --devinfo

# 查看评论
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --id 354705 --comments

# 列表查询
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --list

# 列表查询（带 IQL 条件）
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --list --iql "流程状态=新建"

# 列表查询（排序）
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --list --order lastModifiedTime --desc

# 列表查询（显示详情和关联卡片）
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --list --detail --associations
```

### 工作流 4：批量操作

```bash
# 批量查询
~/py312/bin/python3 scripts/batch_operations.py --space edc-scrum --iql "优先级=P0"

# 批量查询（排序）
~/py312/bin/python3 scripts/batch_operations.py --space edc-scrum --iql "优先级=P0" --order lastModifiedTime

# 状态统计
~/py312/bin/python3 scripts/batch_operations.py --space edc-scrum --status-summary

# 状态统计（JSON 格式）
~/py312/bin/python3 scripts/batch_operations.py --space edc-scrum --status-summary --format json
```

### 工作流 5：计划管理

```bash
# 查看空间内所有计划
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --list

# 查询单个计划（显示状态和子计划）
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --query "2024 Q1 计划"
# 输出包含：计划 ID、名称、状态、描述、时间范围、子计划列表等

# 创建新计划
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --create \
  --name "2024 Q1 计划" \
  --desc "第一季度工作计划" \
  --start "2024-01-01" \
  --end "2024-03-31"

# 创建置顶计划
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --create \
  --name "优先计划" \
  --desc "重要计划" \
  --start "2024-01-01" \
  --end "2024-12-31" \
  --stick

# 更新计划时间
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --update-date \
  --id 123 \
  --start "2024-02-01" \
  --end "2024-04-30"

# 获取计划及里程碑
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --with-milestones

# JSON 格式输出
~/py312/bin/python3 scripts/plan.py --space iCafeTestDemo --list --format json
```

## 状态流转

### 基本规则

- **必须遵循工作流**：不能直接跳转状态，需按中间状态逐步流转
- **必填字段**：状态转换时需要填写相应状态的必填字段
- **字段值验证**：所有字段值必须符合预定义选项

### 验证状态转换

```bash
# 验证转换是否允许
~/py312/bin/python3 scripts/check_workflow.py --from "新建" --to "已分配" --type Bug

# 查看当前状态可流转的所有状态
~/py312/bin/python3 scripts/check_workflow.py --from "新建"
```

### 智能字段推断

`plan_transition.py` 会根据以下信息智能推荐字段值：
- 卡片标题和描述
- 同类型样本卡片的历史数据
- 对话上下文（用户提到的需求、原因、解决方案等）

| 用户上下文     | 智能推断                   |
| -------------- | -------------------------- |
| "这不是bug"    | Bug分析结论 = 非Bug        |
| "云端泛化错误" | Bug问题原因 = 云端泛化错误 |
| "调整泛化参数" | Bug修复方案 = 调整泛化参数 |

## 常用命令速查

### 查询相关
```bash
~/py312/bin/python3 scripts/query_card.py --space <space_id> --id <card_id>           # 基本查询
~/py312/bin/python3 scripts/query_card.py --space <space_id> --id <card_id> --fields   # 显示自定义字段
~/py312/bin/python3 scripts/query_card.py --space <space_id> --id <card_id> --devinfo # 研发数据链
~/py312/bin/python3 scripts/query_card.py --space <space_id> --id <card_id> --comments # 评论列表
~/py312/bin/python3 scripts/query_card.py --space <space_id> --list                    # 列表查询
~/py312/bin/python3 scripts/query_card.py --space <space_id> --list --iql "<IQL>"        # 列表查询（带条件）
~/py312/bin/python3 scripts/query_card.py --space <space_id> --list --order lastModifiedTime --desc  # 列表查询（排序）
```

### 创建相关
```bash
~/py312/bin/python3 scripts/create_card.py --space <space_id> --title "<标题>" --type <类型>           # 预览
~/py312/bin/python3 scripts/create_card.py --space <space_id> --title "<标题>" --type <类型> --execute # 创建
```

### 更新相关
```bash
~/py312/bin/python3 scripts/update_card.py --space <space_id> --id <card_id> --status "<状态>" --preview  # 预览
~/py312/bin/python3 scripts/update_card.py --space <space_id> --id <card_id> --status "<状态>" --execute  # 执行
~/py312/bin/python3 scripts/update_card.py --space <space_id> --id <card_id> --related <空间-关联卡片ID> --rel-operation add --execute  # 添加关联
```

### 验证相关
```bash
~/py312/bin/python3 scripts/check_workflow.py --from "<当前状态>" --to "<目标状态>"           # 验证转换
~/py312/bin/python3 scripts/field_config.py fields --space <space_id> --type <type>           # 字段配置
~/py312/bin/python3 scripts/detect_required_fields.py --space <space_id> --id <card_id> --status "<目标状态>"  # 必填字段
```

### 计划操作相关
```bash
~/py312/bin/python3 scripts/plan.py --space <space_id> --list                           # 列出所有计划
~/py312/bin/python3 scripts/plan.py --space <space_id> --query "<计划名称>"              # 查询单个计划
~/py312/bin/python3 scripts/plan.py --space <space_id> --create --name "<名称>" --desc "<描述>" --start "YYYY-MM-DD" --end "YYYY-MM-DD"  # 创建计划
~/py312/bin/python3 scripts/plan.py --space <space_id> --update-date --id <plan_id> --start "YYYY-MM-DD" --end "YYYY-MM-DD"  # 更新计划时间
~/py312/bin/python3 scripts/plan.py --space <space_id> --with-milestones                 # 获取计划及里程碑
```

更多命令详情请参阅 [通用指南](references/general-guide.md)。

## 错误处理

| 错误类型         | 错误信息                   | 解决方法                               |
| ---------------- | -------------------------- | -------------------------------------- |
| 认证错误         | AuthenticationError        | 检查用户名密码或配置文件               |
| 缺少必填字段     | MissingRequiredFieldsError | 使用 `plan_transition.py` 获取字段建议 |
| 状态转换不被允许 | ValidationError            | 使用 `check_workflow.py` 验证转换规则  |
| 字段值不合法     | field value error          | 使用 `field_config.py` 查看合法选项    |
| 资源不存在       | ResourceNotFoundError      | 确认 space_id 和 card_id 是否正确      |

## 重要限制

1. **禁止直接调用底层 API**：不要创建 path 直接调用 `client.get()` 函数
2. **预览模式**：所有写操作建议先使用 `dry_run=True` 或 `--preview` 预览
3. **字段验证**：
   - `status` 字段需检测是否符合 workflow 的 status-node 规范
   - 其他字段需使用 `scripts/field_config.py` 脚本验证是否合规
4. **状态转换**：必须遵循工作流规则，不能直接跳转状态
5. **状态转换缓存**：状态转换字段信息会自动缓存到 `.cache/` 目录
6. **字段值限制**：单选字段和多选字段必须从预定义选项中选择

## 常见问题

**Q: 为什么我的字段值无法保存？**
A: 某些字段（如 `福特-版本计划`、`Bug分析结论`）是单选字段，必须从预定义选项中选择。使用以下命令查看合法选项：
```bash
~/py312/bin/python3 scripts/field_config.py fields --space edc-scrum --type Bug
```

**Q: 如何快速流转卡片到目标状态？**
A: 使用 `plan_transition.py` 获取完整流转计划并执行：
```bash
~/py312/bin/python3 scripts/plan_transition.py --space edc-scrum --id 354705 --to "已修复"
```

**Q: 状态转换失败怎么办？**
A: 首先验证状态转换是否合法：
```bash
~/py312/bin/python3 scripts/check_workflow.py --from "当前状态" --to "目标状态" --type Bug
```

**Q: 如何查看卡片当前状态？**
A: 使用查询脚本：
```bash
~/py312/bin/python3 scripts/query_card.py --space edc-scrum --id 354705
```

## 详细文档

- [通用指南](references/general-guide.md) - 环境初始化、流转前检查、常用命令速查、批量操作
- [卡片创建示例](references/card-creation-examples.md) - 创建示例、父子关联、跨空间配置
- [流转到修复状态](references/transition-to-fixed.md) - Bug 修复流程详细说明
- [流转到非Bug状态](references/transition-to-nonbug.md) - 非 Bug 关闭流程详细说明
- [如何操作计划](references/plan-examples.md) - 查询操作计划详细说明
- [IQL 查询语言](references/IQL.md) - IQL 查询语言详细说明
