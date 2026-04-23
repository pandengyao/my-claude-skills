# iCafe 卡片流转通用指南

本文档提供 iCafe 卡片流转的通用最佳实践和常用命令速查。

---

## 快速开始

### 环境初始化

**重要**：在首次使用本技能前，必须完成以下环境初始化步骤：

#### Step 1: 检查配置文件

检查 `config/config.yaml` 是否存在：
- 如果存在，跳过此步骤
- 如果不存在，执行以下操作：
  1. 复制 `config/config.yaml.example` 为 `config/config.yaml`
  2. 提示用户填写必要的认证信息（username、password、default_space）

```bash
# 检查配置文件是否存在
if [ ! -f "config/config.yaml" ]; then
  cp config/config.yaml.example config/config.yaml
  echo "已创建 config/config.yaml，请填写以下配置："
  echo "  - auth.username: 你的用户名"
  echo "  - auth.password: 虚拟密码（从 https://console.cloud.baidu-int.com/api/icafe/users/virtual 获取）"
  echo "  - default_space: 默认空间 ID"
fi
```

#### Step 2: 安装依赖

执行以下命令安装 Python 依赖：

```bash
pip install -e .
```

---

## 核心工作流

### 状态流转工作流

iCafe 卡片的状态流转遵循工作流规则，不能直接跳转状态。推荐使用 `plan_transition.py` 一次性获取完整流转计划。

```bash
# 获取完整流转路径、必填字段建议、执行命令
python scripts/plan_transition.py --space <space_id> --id <card_id> --to "<目标状态>"

# 示例：流转到已修复
python scripts/plan_transition.py --space edc-scrum --id 355812 --to "已修复"
```

### 流转交互流程

`plan_transition.py` 会返回包含 `_instruction` 字段的 JSON 输出，指导 Claude 如何处理：

1. **action: "execute_commands"** - 直接执行 `commands` 中的命令
2. **action: "adjust_and_confirm_fields"** - 需要智能调整字段值并确认

**确认流程**：
1. 根据卡片信息和上下文智能调整字段值
2. 按状态分组展示调整后的字段值
3. 收集用户确认或修改
4. 根据确认值调整命令参数并执行

---

## 流转前检查清单

```bash
# 1. 查询卡片当前状态
python scripts/query_card.py --space <space_id> --id <card_id>

# 2. 验证状态转换
python scripts/check_workflow.py --type <type> --from "<当前状态>" --to "<目标状态>"

# 3. 检测必填字段（可选）
python scripts/detect_required_fields.py --space <space_id> --id <card_id> --status "<目标状态>"

# 4. 查看字段配置（如不确定字段值）
python scripts/field_config.py fields --space <space_id> --type <type>
```

---

## 常见错误及解决方法

| 错误类型         | 错误信息                   | 解决方法                              |
| ---------------- | -------------------------- | ------------------------------------- |
| 状态转换不被允许 | ValidationError            | 使用 `check_workflow.py` 验证转换规则 |
| 字段值不合法     | field value error          | 使用 `field_config.py` 查看合法选项   |
| 缺少必填字段     | MissingRequiredFieldsError | 使用 `detect_required_fields.py` 检测 |
| 认证失败         | AuthenticationError        | 检查用户名密码或配置文件              |

---

## 批量操作

### 批量查询卡片

使用 `batch_operations.py` 进行批量查询和统计：

```bash
# 基础查询
python scripts/batch_operations.py --space edc-scrum --iql "优先级=P0"

# 限制返回数量
python scripts/batch_operations.py --space edc-scrum --iql "流程状态=新建" --limit 50

# JSON 格式输出
python scripts/batch_operations.py --space edc-scrum --iql "类型=Bug" --format json
```

### 状态统计

使用 `--status-summary` 参数查看卡片状态分布：

```bash
# 统计空间内所有卡片状态
python scripts/batch_operations.py --space edc-scrum --status-summary

# 统计特定类型的卡片状态
python scripts/batch_operations.py --space edc-scrum --status-summary --iql "类型=Bug"

# JSON 格式输出统计结果
python scripts/batch_operations.py --space edc-scrum --status-summary --format json
```

输出示例：
```
📊 按状态分布:
   新建             12 ███████████████████
   已分配           45 ████████████████████████████████████████
   已分析           78 ████████████████████████████████████████████████████
   已修复           23 █████████████████████████
   已关闭           156 ███████████████████████████████████████████████████████████████████████

📋 按类型分布:
   Bug              201 ███████████████████████████████████████████████████████████████████████
   Story            85  ████████████████████████████████████████████████
   Task             28  ████████████████

👤 负责人排名 (Top 10):
   zhangsan         45  ████████████████████████████████
   lisi             38  █████████████████████████████
   wangwu           32  █████████████████████████
```

---

## 常见流转场景

### 场景 1：Bug 修复流转

将 Bug 卡片从"新建"流转到"已修复"：

```bash
# 获取流转计划
python scripts/plan_transition.py --space edc-scrum --id <card_id> --to "已修复"

# 智能推断字段值示例
# - Bug分析结论: 需专业线修复
# - Bug问题原因: 根据卡片标题和描述推断
# - Bug修复方案: 根据上下文推断
```

### 场景 2：非 Bug 关闭

将非 Bug 卡片流转到"已关闭"：

```bash
# 获取流转计划
python scripts/plan_transition.py --space edc-scrum --id <card_id> --to "已关闭"

# 非 Bug 特殊字段
# - Bug分析结论: 非Bug
# - Bug问题原因: 非Bug 或具体原因
# - Bug与用例关联: 非Bug无需测试用例
```

### 场景 3：批量流转多张卡片

对多张卡片执行相同的状态流转：

```bash
# 使用 Claude Code 的并行处理能力，为每个卡片调用 plan_transition.py
# 然后批量执行 update_card.py 命令
```

---

## 字段管理

### 查看字段配置

```bash
# 查询空间的问题类型列表
python scripts/field_config.py types --space <space_id>

# 查询指定类型的字段配置
python scripts/field_config.py fields --space <space_id> --type Bug

# 强制刷新缓存
python scripts/field_config.py fields --space <space_id> --type Bug --refresh
```

### 验证字段值

```bash
# 验证 Bug 类型的字段值
python scripts/field_config.py validate --space edc-scrum --type Bug \
  --fields '{"Bug分析结论": "需专业线修复"}'

# 批量验证多个字段
python scripts/field_config.py validate --space edc-scrum --type Bug \
  --fields '{"Bug分析结论": "非Bug", "Bug问题原因": "非Bug"}'
```

---

## 最佳实践

### 1. 优先使用 plan_transition.py

**推荐**：使用 `plan_transition.py` 获取完整流转计划
- 自动计算流转路径
- 智能推断必填字段建议值
- 生成可直接执行的命令

**不推荐**：手动逐步流转，容易遗漏必填字段

### 2. 字段值必须符合预定义选项

单选/多选字段必须从预定义选项中选择，不能随意填写。

使用 `field_config.py` 查看合法选项：
```bash
python scripts/field_config.py fields --space edc-scrum --type Bug
```

### 3. 验证状态转换

流转前验证状态转换是否合法：
```bash
python scripts/check_workflow.py --type <type> --from "<当前状态>" --to "<目标状态>"
```

### 4. 关闭状态需要评论

流转到"已关闭"状态时必须添加评论：
```bash
python scripts/update_card.py --space edc-scrum --id <card_id> \
  --status "已关闭" \
  --comment "Bug问题原因：非Bug，关闭此问题" \
  --execute
```

### 5. 利用上下文智能推断

当用户提供上下文信息时，系统可以智能推断字段值：

| 用户输入 | 智能推断 |
|---------|---------|
| "这不是bug" | Bug分析结论 = 非Bug |
| "云端泛化错误" | Bug问题原因 = 云端泛化错误 |
| "调整泛化，下发正确语音指令" | Bug修复方案 = 调整泛化，下发正确语音指令 |

---

## 关键要点

1. **状态流转必须遵循工作流规则**：不能直接跳转状态，需要按中间状态逐步流转
2. **字段值必须符合预定义选项**：单选/多选字段必须从预定义选项中选择
3. **必填字段必须填写**：使用 `detect_required_fields.py` 检测必填字段
4. **关闭状态需要评论**：流转到"已关闭"状态时必须添加评论