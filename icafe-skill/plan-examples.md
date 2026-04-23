# 计划操作示例

iCafe 计划管理的实际使用示例。

## 查询单个计划

### 命令行方式

```bash
python scripts/plan.py --space iCafeTestDemo --query "2021Q2"
```

输出：
```
============================================================
计划信息: 2021Q2
============================================================
计划 ID: 473098
名称: 2021Q2
状态: ACTIVE
描述: 无
开始日期: 2021-04-06
结束日期: 2021-05-30
空间 ID: iCafeTestDemo

子计划 (12个):
  - 2021Q2/04.05~04.11: ACTIVE
  - 2021Q2/04.12~04.18: ACTIVE
  ...
  - 2021Q2/06.21~06.27: ACTIVE
============================================================
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.plan import get_plan

client = init_client(config_file='config/config.yaml')

plan = get_plan(client, space_id='iCafeTestDemo', plan_name='2021Q2')
print(f"计划: {plan.name}")
print(f"状态: {plan.status}")
print(f"时间: {plan.start_date} ~ {plan.end_date}")
print(f"子计划数: {len(plan.children)}")

client.close()
```

### JSON 格式输出

```bash
python scripts/plan.py --space iCafeTestDemo --query "2021Q2" --format json
```

## 列出所有计划

### 命令行方式

```bash
python scripts/plan.py --space iCafeTestDemo --list
```

### 包含里程碑

```bash
python scripts/plan.py --space iCafeTestDemo --with-milestones
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.utils import get_plans
from icafe_skill.plan import get_plans_with_milestones

client = init_client(config_file='config/config.yaml')

# 获取所有计划（不包含里程碑）
plans = get_plans(client, space_id='iCafeTestDemo')
for plan in plans:
    print(f"[{plan.plan_id}] {plan.name}: {plan.start_date} ~ {plan.end_date}")

# 获取计划及里程碑
plans_with_milestones = get_plans_with_milestones(client, space_id='iCafeTestDemo')
for plan in plans_with_milestones:
    type_str = "里程碑" if plan.is_milestone else "计划"
    print(f"{type_str}: {plan.name}")

client.close()
```

## 创建新计划

### 命令行方式

```bash
python scripts/plan.py \
  --space iCafeTestDemo \
  --create \
  --name "2025 Q1 计划" \
  --desc "第一季度工作计划" \
  --start "2025-01-01" \
  --end "2025-03-31"
```

### 创建置顶计划

```bash
python scripts/plan.py \
  --space iCafeTestDemo \
  --create \
  --name "优先计划" \
  --desc "重要计划" \
  --start "2025-01-01" \
  --end "2025-12-31" \
  --stick
```

### 创建带父计划的子计划

```bash
python scripts/plan.py \
  --space iCafeTestDemo \
  --create \
  --name "Q1/1月计划" \
  --desc "1月工作计划" \
  --start "2025-01-01" \
  --end "2025-01-31" \
  --parent "2025 Q1 计划"
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.plan import create_plan

client = init_client(config_file='config/config.yaml')

plan = create_plan(
    client,
    space_id='iCafeTestDemo',
    name='2025 Q1 计划',
    desc='第一季度工作计划',
    start_date='2025-01-01',
    end_date='2025-03-31',
    stick='true'  # 置顶
)

print(f"创建成功: {plan.name} (ID: {plan.plan_id})")
client.close()
```

## 更新计划时间

### 命令行方式

```bash
python scripts/plan.py \
  --space iCafeTestDemo \
  --update-date \
  --id 473098 \
  --start "2025-04-01" \
  --end "2025-06-30"
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.plan import update_plan_date

client = init_client(config_file='config/config.yaml')

result = update_plan_date(
    client,
    space_id='iCafeTestDemo',
    plan_id='473098',
    start_date='2025-04-01',
    end_date='2025-06-30'
)

print(f"更新成功: {result}")
client.close()
```

## 查询计划下的卡片

计划 API 不返回卡片信息，需要通过 `所属计划` 字段查询卡片：

```bash
python scripts/query_card.py \
  --space iCafeTestDemo \
  --list \
  --iql '所属计划="2021Q2/04.05~04.11"'
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.query import list_cards

client = init_client(config_file='config/config.yaml')

# 查询特定计划下的卡片
cards = list_cards(client, space_id='iCafeTestDemo', iql='所属计划="2021Q2/04.05~04.11"')
print(f"计划下有 {len(cards)} 张卡片")
for card in cards:
    print(f"  [{card.full_id}] {card.title} - {card.status}")

client.close()
```

## 计划层级结构

计划可以形成层级结构：
- 父计划（如：2021Q2）
- 子计划（如：2021Q2/04.05~04.11，按周划分）

子计划的路径是 `父计划名/子计划名` 格式：

```bash
# 查询父计划
python scripts/plan.py --space iCafeTestDemo --query "2021Q2"

# 查询子计划
python scripts/plan.py --space iCafeTestDemo --query "2021Q2/04.05~04.11"
```

## 常见问题

**Q: plan 参数和 parent 参数有什么区别？**
A:
- `plan` 是计划路径（如 `2021Q2` 或 `2021Q2/04.05~04.11`），用于查询计划
- `parent` 是父计划名称，用于创建子计划

**Q: 如何查询计划下的卡片？**
A: 计划 API 不返回卡片信息，需使用卡片查询 API 并通过 `所属计划` 字段过滤：
```bash
python scripts/query_card.py --space <space> --list --iql '所属计划="<计划路径>"'
```

**Q: 计划时间格式有什么要求？**
A: 必须是 `YYYY-MM-DD` 格式，如 `2025-01-01`。

**Q: stick 参数有什么作用？**
A: `stick` 参数用于将计划置顶显示，值为 `"true"` 或 `"false"`。

**Q: 如何知道计划的 ID？**
A: 查询计划时会显示计划 ID，也可以使用计划名称查询。

**Q: 计划状态有哪些？**
A: 常见状态包括 `ACTIVE`（活跃）、`ARCHIVED`（已归档）等。

## 计划操作 API 参考表

| 操作 | 方法 | 端点 | 说明 |
|------|------|------|------|
| 列出计划 | GET | `/api/v2/space/{space_id}/plans` | 获取空间内所有计划 |
| 查询单个计划 | GET | `/api/v2/space/{space_id}/plan?path={name}` | 按名称查询计划 |
| 创建计划 | POST | `/api/v2/space/{space_id}/plan/create` | 创建新计划 |
| 更新时间 | POST | `/api/v2/space/{space_id}/plan/{id}/updatePlanDate` | 更新计划时间 |
| 计划及里程碑 | GET | `/api/v2/space/plans?spacePrefixCode={space_id}` | 获取计划及里程碑 |
