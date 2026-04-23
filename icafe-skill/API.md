# iCafe Skill API 参考

本文档列出 iCafe Skill SDK 的所有公开 API。

---

## 目录

- [核心组件](#核心组件)
- [查询函数](#查询函数)
- [创建函数](#创建函数)
- [修改函数](#修改函数)
- [Plan Operations](#plan-operations)
- [辅助函数](#辅助函数)
- [字段配置](#字段配置)
- [数据模型](#数据模型)
- [异常类型](#异常类型)

---

## 核心组件

### `AuthConfig`

认证配置类，支持多种初始化方式。

```python
from icafe_skill import AuthConfig

# 方式1：直接传参
auth = AuthConfig(username="user", password="pass")

# 方式2：从环境变量加载
auth = AuthConfig.from_env()

# 方式3：从配置文件加载
auth = AuthConfig.from_file("config/config.yaml")
```

### `ICafeClient`

HTTP 客户端，负责与 iCafe API 通信。

```python
from icafe_skill import ICafeClient, AuthConfig

auth = AuthConfig.from_env()
client = ICafeClient(auth, timeout=30, max_retries=3)

# 使用完毕后关闭
client.close()
```

### `init_client()`

便捷初始化函数。

```python
from icafe_skill import init_client

# 从环境变量
client = init_client(use_env=True)

# 从配置文件
client = init_client(config_file="config/config.yaml")

# 显式传参
client = init_client(username="user", password="pass")
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `username` | str | iCafe 用户名 |
| `password` | str | 虚拟密码 |
| `config_file` | str | 配置文件路径 |
| `use_env` | bool | 是否从环境变量加载 |

---

## 查询函数

所有查询函数从 `icafe_skill.query` 模块导入。

### `get_card()`

获取单张卡片详情。

```python
from icafe_skill.query import get_card

card = get_card(client, space_id="my-space", card_id="123")
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `card_id` | str | 卡片 ID |

**返回：** `Card` 对象

### `list_cards()`

列出空间内的卡片，支持 IQL 查询、排序、关联卡片等功能。

> **破坏性变更 (v0.3.0)**: `max_records` 参数类型从 `int` 改为 `str`，`show_detail` 从 `bool` 改为 `str`，以符合 iCafe API 规范。

```python
from icafe_skill.query import list_cards

# 列出所有卡片
cards = list_cards(client, space_id="my-space", max_records="20")

# 使用 IQL 条件查询
cards = list_cards(client, "my-space", iql="流程状态=新建 AND 优先级=P0")

# 按最后修改时间倒序排列
cards = list_cards(client, "my-space", order="lastModifiedTime", is_desc=True)

# 显示卡片详情和关联卡片
cards = list_cards(client, "my-space", show_detail="true", show_associations=True)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `iql` | str | IQL 查询表达式（可选） |
| `max_records` | str | 最大返回数量（默认："100"，最大："100"） |
| `page` | int | 页码（默认：1） |
| `show_detail` | str | 显示卡片详情，"true" 或空字符串（默认：""） |
| `show_associations` | bool | 显示关联卡片信息（默认：False） |
| `is_desc` | bool | 是否倒序排序（默认：False） |
| `order` | str | 排序字段（默认："createTime"） |
| `show_children` | bool | 显示子卡片信息（默认：False） |
| `show_okr` | bool | 显示关联 OKR 信息（默认：False） |
| `show_accumulate` | bool | 显示周实际工时填报明细（默认：False） |

**支持的排序字段：**
- `createTime`（默认）、`lastModifiedTime`、`creatorId`、`issueStatusId`、`responsiblePeopleId`、`sequence`
- 自定义下拉字段、单选字段
- **不支持**：文本/内容字段

**返回：** `List[Card]`

### `get_card_status()`

获取卡片的流程状态。

```python
from icafe_skill.query import get_card_status

status = get_card_status(client, space_id="my-space", issue_id="123")
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `issue_id` | str | 卡片 ID |

**返回：** `dict`

### `get_dev_info()`

获取卡片的研发数据链信息（iCode 评审、流水线、分支等）。

```python
from icafe_skill.query import get_dev_info

dev_info = get_dev_info(client, space_id="my-space", issue_id="123")
print(f"评审数: {len(dev_info.icode_reviews)}")
print(f"流水线: {len(dev_info.pipelines)}")
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `issue_id` | str | 卡片 ID |

**返回：** `DevInfo` 对象

### `get_comments()`

获取卡片的评论列表。

```python
from icafe_skill.query import get_comments

comments = get_comments(client, space_id="my-space", sequence="123")
for c in comments:
    print(f"[{c.author}] {c.content}")
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `sequence` | str | 卡片编号 |

**返回：** `List[Comment]`

### `get_cards_with_dev_updates()`

查询空间下某段时间内有研发数据链更新的卡片。

```python
from icafe_skill.query import get_cards_with_dev_updates

cards = get_cards_with_dev_updates(
    client,
    space_id="my-space",
    start_time="2024-01-01 00:00:00",
    end_time="2024-12-31 00:00:00"
)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `start_time` | str | 开始时间 |
| `end_time` | str | 结束时间 |
| `page` | int | 页码（默认：1） |
| `max_records` | int | 最大返回数量 |

**返回：** `List[Card]`

---

## 创建函数

所有创建函数从 `icafe_skill.create` 模块导入。

### `create_cards()`

批量创建卡片。

```python
from icafe_skill.models import Issue
from icafe_skill.create import create_cards

issue = Issue.create(
    title="新功能",
    detail="详细描述",
    type="Story",
    creator="zhangsan",
    priority="P1-High"
)

# dry-run 模式（默认）
result = create_cards(client, "my-space", [issue], dry_run=True)

# 实际创建
result = create_cards(client, "my-space", [issue], dry_run=False)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `issues` | List[Issue] | 待创建的卡片列表 |
| `dry_run` | bool | 是否为预览模式（默认：True） |
| `validate_fields` | bool | 是否验证字段（默认：False） |
| `config_cache` | SpaceConfigCache | 配置缓存（可选） |

**返回：** `dict`

### `create_comment()`

为卡片创建评论。

```python
from icafe_skill.create import create_comment

result = create_comment(
    client,
    space_id="my-space",
    issue_id="123",
    comment_msg="这是评论内容",
    dry_run=True
)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `issue_id` | str | 卡片 ID |
| `comment_msg` | str | 评论内容 |
| `dry_run` | bool | 是否为预览模式（默认：True） |

**返回：** `dict`

---

## 修改函数

所有修改函数从 `icafe_skill.update` 模块导入。

### `update_card()`

更新卡片字段。

```python
from icafe_skill.update import update_card

result = update_card(
    client,
    space_id="my-space",
    card_id="123",
    fields={"status": "开发中", "assignee": "lisi"},
    comment="更新状态",
    dry_run=True
)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `card_id` | str | 卡片 ID |
| `fields` | dict | 要更新的字段 |
| `comment` | str | 附加评论（可选） |
| `rel_issue` | str | 关联卡片ID，格式为"空间标识-卡片序号"（可选） |
| `rel_issue_operation` | str | 关联卡片操作类型：add/delete（可选） |
| `operator` | str | 修改人邮箱前缀，用于校验卡片权限（可选） |
| `is_check_status` | bool | 是否进行流程状态可达检查，默认True（可选） |
| `rel_project` | str | 关联项目编号（可选） |
| `rel_project_operation` | str | 关联项目操作类型：add/delete（可选） |
| `dry_run` | bool | 是否为预览模式（默认：True） |

**返回：** `dict`

### `update_comment()`

更新已有评论。

```python
from icafe_skill.update import update_comment

result = update_comment(
    client,
    space_id="my-space",
    comment_id="456",
    content="更新后的评论内容",
    dry_run=True
)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `client` | ICafeClient | 客户端实例 |
| `space_id` | str | 空间标识 |
| `comment_id` | str | 评论 ID |
| `content` | str | 新的评论内容 |
| `dry_run` | bool | 是否为预览模式（默认：True） |

**返回：** `dict`

### `preview_update()`

预览更新操作（不需要客户端）。

```python
from icafe_skill.update import preview_update

preview = preview_update(
    space_id="my-space",
    card_id="123",
    fields={"status": "开发中"},
    comment="开始开发"
)
print(preview)
```

**参数：**
| 参数 | 类型 | 说明 |
|------|------|------|
| `space_id` | str | 空间标识 |
| `card_id` | str | 卡片 ID |
| `fields` | dict | 要更新的字段 |
| `comment` | str | 附加评论（可选） |

**返回：** `str` 预览文本

---

## Plan Operations

### `get_plan()`

Get a single plan by name.

```python
from icafe_skill import init_client, get_plan

client = init_client(config_file="config/config.yaml")
plan = get_plan(client, space_id="my-space", plan_name="Q1计划")
print(f"Plan: {plan.name}, {plan.start_date} - {plan.end_date}")
```

### `create_plan()`

Create a new plan.

```python
from icafe_skill import init_client, create_plan

client = init_client(config_file="config/config.yaml")
plan = create_plan(
    client,
    space_id="my-space",
    name="Q1计划",
    desc="第一季度工作计划",
    start_date="2024-01-01",
    end_date="2024-03-31",
    stick="true"  # Optional: stick to top
)
print(f"Created plan ID: {plan.plan_id}")
```

### `update_plan_date()`

Update plan date range.

```python
from icafe_skill import init_client, update_plan_date

client = init_client(config_file="config/config.yaml")
result = update_plan_date(
    client,
    space_id="my-space",
    plan_id="123",
    start_date="2024-02-01",
    end_date="2024-04-30"
)
print(result)
```

### `get_plans_with_milestones()`

Get all plans with milestones in a space.

```python
from icafe_skill import init_client, get_plans_with_milestones

client = init_client(config_file="config/config.yaml")
plans = get_plans_with_milestones(client, space_id="my-space")
for plan in plans:
    type_str = "里程碑" if plan.is_milestone else "计划"
    print(f"{type_str}: {plan.name}")
```

---

## 辅助函数

### `get_plans()`

获取空间内的计划列表。

```python
from icafe_skill import get_plans

plans = get_plans(client, space_id="my-space")
```

### `get_issue_types()`

获取空间支持的卡片类型。

```python
from icafe_skill import get_issue_types

types = get_issue_types(client, space_id="my-space")
```

### `print_available_types()`

打印空间可用的卡片类型。

```python
from icafe_skill import print_available_types

print_available_types(client, "my-space")
```

### `print_required_fields()`

打印指定类型的必填字段。

```python
from icafe_skill import print_required_fields

print_required_fields(client, "my-space", "Bug")
```

### `validate_card_data()`

验证卡片数据是否符合要求。

```python
from icafe_skill import validate_card_data

result = validate_card_data(
    client, "my-space", "Bug",
    title="测试Bug",
    detail="描述",
    fields={"优先级": "P1-High"}
)

if result['valid']:
    print("验证通过")
else:
    print(f"验证失败: {result['errors']}")
```

### `build_issue_with_guidance()`

带辅助提示的 Issue 构建函数。

```python
from icafe_skill import build_issue_with_guidance, SpaceConfigCache

cache = SpaceConfigCache(client)
issue = build_issue_with_guidance(
    client,
    space_id="my-space",
    issue_type="Bug",
    title="测试Bug",
    detail="描述",
    creator="zhangsan",
    fields={"优先级": "P1-High"},
    show_hints=True,
    config_cache=cache
)
```

---

## 字段配置

### `SpaceConfigCache`

空间配置缓存，减少重复 API 调用。

```python
from icafe_skill import SpaceConfigCache

cache = SpaceConfigCache(client, cache_ttl=3600)  # 缓存1小时

# 获取类型配置
types = cache.get_issue_types("my-space")

# 获取字段配置
fields = cache.get_fields_for_type("my-space", "Bug")

# 强制刷新
types = cache.get_issue_types("my-space", force_refresh=True)

# 清除缓存
cache.clear_cache("my-space")
cache.clear_cache()  # 清除所有
```

---

## 数据模型

### `Card`

卡片数据模型。

**属性：**
| 属性 | 类型 | 说明 |
|------|------|------|
| `full_id` | str | 完整 ID（如 space-123） |
| `title` | str | 标题 |
| `type` | str | 类型 |
| `status` | str | 状态 |
| `assignee` | str | 负责人 |
| `priority` | str | 优先级 |
| `creator` | str | 创建人 |
| `detail` | str | 详情 |

### `Issue`

用于创建卡片的数据模型。

```python
from icafe_skill.models import Issue

issue = Issue.create(
    title="标题",
    detail="详情",
    type="Story",
    creator="zhangsan",
    assignee="lisi",
    status="新建",
    priority="P1-High",
    notify_emails=["lisi@example.com"],
    comment="初始评论"
)
```

### `Comment`

评论数据模型。

**属性：**
| 属性 | 类型 | 说明 |
|------|------|------|
| `author` | str | 作者 |
| `content` | str | 内容 |
| `created_at` | datetime | 创建时间 |

### `DevInfo`

研发数据链模型。

**属性：**
| 属性 | 类型 | 说明 |
|------|------|------|
| `icode_reviews` | list | iCode 评审列表 |
| `pipelines` | list | 流水线列表 |
| `branches` | list | 分支列表 |

### `Plan`

计划数据模型。

---

## 异常类型

所有异常从 `icafe_skill.exceptions` 模块导入。

| 异常类 | 说明 |
|--------|------|
| `ICafeError` | 基础异常类 |
| `AuthenticationError` | 认证失败 |
| `AuthorizationError` | 授权失败 |
| `ResourceNotFoundError` | 资源不存在 |
| `ResourceConflictError` | 资源冲突 |
| `ValidationError` | 验证失败 |
| `InvalidParameterError` | 参数无效 |
| `NetworkError` | 网络错误 |
| `TimeoutError` | 请求超时 |
| `APIError` | API 错误 |

**使用示例：**

```python
from icafe_skill import (
    ICafeError,
    AuthenticationError,
    ValidationError,
    ResourceNotFoundError,
)

try:
    card = get_card(client, "my-space", "123")
except AuthenticationError:
    print("认证失败")
except ResourceNotFoundError:
    print("卡片不存在")
except ValidationError as e:
    print(f"验证失败: {e}")
except ICafeError as e:
    print(f"API错误: {e}")
```

# 在线API文档

https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/_SKPgSwp2G/NbX2gitgSF/1461075590af49