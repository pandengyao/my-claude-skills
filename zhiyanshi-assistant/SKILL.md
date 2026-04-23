---
name: zhiyanshi-assistant
description: 智研师需求自动管理接口助手，支持创建卡片、流转到开发中、查询卡片、批量提测准出等操作。
---

# 智研师需求自动管理接口助手

## 概述

本技能提供了平台化需求自动管理的 API 接口，支持以下功能：
1. 创建卡片接口 - 在 iCafe 中创建卡片（Story、Task 等）
2. 流转到开发中接口 - 将卡片状态流转到开发中
3. 查询 iCafe 卡片接口 - 使用 IQL 查询卡片
4. 批量提测准出接口 - 批量执行提测准出操作

---

## API 列表

### 1. 创建卡片接口

**功能描述**: 在指定 iCafe 空间中创建卡片

| 参数 | 说明 |
|-----|------|
| URL | `https://wf-test.dev.weiyun.baidu.com/pioneer/api/sep/requirement/create` |
| 方法 | POST |

**请求参数**:
```json
{
    "spaceCode": "joytest",
    "platform": "appgo",
    "issues": [
        {
            "parents": "",
            "title": "卡片标题",
            "type": "Story",
            "detail": "<html>卡片详情内容</html>",
            "fields": {
                "负责人": "shijiazheng",
                "所属计划": "",
                "流程状态": "新建"
            },
            "developName": "shijiazheng"
        }
    ]
}
```

---

### 2. 流转到开发中接口

**功能描述**: 将指定卡片状态流转到开发中

| 参数 | 说明 |
|-----|------|
| URL | `https://wf-test.dev.weiyun.baidu.com/bepqa/api/itest/card/status` |
| 方法 | POST |

**请求参数**:
```json
{
    "issueId": "joytest-1971",
    "operator": "shijiazheng",
    "platform": "appgo"
}
```

---

### 3. 查询 iCafe 卡片接口

**功能描述**: 使用 IQL 查询条件查询 iCafe 卡片（iqlText 必填）

| 参数 | 说明 |
|-----|------|
| URL | `https://wf-test.dev.weiyun.baidu.com/bepqa/api/itest/query/icafe/cards` |
| 方法 | POST |

**请求参数**:
```json
{
    "iCafeSpace": "joytest",
    "operator": "shijiazheng",
    "platform": "appgo",
    "iqlText": "类型 = Bug",
    "page": "1",
    "pageSize": "100"
}
```

**IQL 查询规则**:

| 运算符 | 含义 | 示例 |
|--------|------|------|
| AND | 且 | `类型 = Bug AND 负责人 = currentUser` |
| OR | 或 | `状态 = 新建 OR 状态 = 待开发` |
| >, <, =, >=, <=, != | 比较运算符 | `创建时间 > "2025-01-01"` |
| in, not in | 包含/不包含 | `类型 in (Bug, Epic, Story)` |
| is empty, is not empty | 为空/不为空 | `所属计划 is empty` |
| ~, !~ | 包含/不包含（文本） | `标题 ~ 测试` |

**常用 IQL 示例**:

| 查询需求 | IQL 表达式 |
|----------|------------|
| 查询所有卡片 | `sequence > 0` |
| 查询 Bug 类型卡片 | `类型 = Bug` |
| 查询当前用户负责的卡片 | `负责人 = currentUser` |
| 查询新建状态的卡片 | `状态 = 新建` |
| 查询 Bug 且负责人是当前用户的卡片 | `类型 = Bug AND 负责人 = currentUser` |
| 查询创建时间在指定日期之后的卡片 | `创建时间 > "2025-01-01"` |
| 查询多种类型的卡片 | `类型 in (Bug, Epic, Story)` |
| 查询标题包含关键词的卡片 | `标题 ~ 测试` |
| 查询负责人在指定列表中的卡片 | `负责人 in (user1, user2, user3)` |
| 查询流程状态在指定范围的卡片 | `流程状态 <= 开发中` |

---

### 4. 批量提测准出接口

**功能描述**: 批量执行提测准出操作

| 参数 | 说明 |
|-----|------|
| URL | `https://wf-test.dev.weiyun.baidu.com/bepqa/api/itest/execute/batch` |
| 方法 | POST |

**请求参数**:
```json
{
    "issueIds": ["joytest-1971", "joytest-1972"],
    "operator": "shijiazheng",
    "platform": "appgo",
    "operatorType": "发起提测"
}
```

**操作类型 (operator_type)**:
- `发起提测` - 发起提测
- `准出` - 准出

---

## 快速开始

```python
from scripts.platform_client import PlatformClient

# 初始化客户端（使用 Cookie 认证）
cookie = "your-cookie-here"
client = PlatformClient(cookie=cookie)

# 创建卡片
result = client.create_card(
    space_code="joytest",
    title="测试卡片",
    card_type="Story",
    platform="appgo",
    develop_name="shijiazheng",
    assignee="shijiazheng",
    detail="<p>卡片详情</p>"
)

# 流转到开发中
result = client.update_status_to_dev(
    issue_id="joytest-1971",
    operator="shijiazheng",
    platform="appgo"
)

# 查询卡片
result = client.query_icafe_cards(
    icafe_space="joytest",
    operator="shijiazheng",
    platform="appgo",
    iql_text="sequence > 0",
    page=1,
    page_size=100
)
```

---

## 使用示例

### 示例 1: 创建卡片

```python
from scripts.platform_client import PlatformClient

client = PlatformClient(cookie="your-cookie")

# 创建 Story 类型卡片
result = client.create_card(
    space_code="joytest",
    title="[用户管理] 用户登录功能",
    card_type="Story",
    platform="appgo",
    develop_name="shijiazheng",
    assignee="shijiazheng",
    status="新建",
    detail="<h2>功能描述</h2><p>实现用户登录功能</p>"
)

# 获取卡片链接
card_data = result.get("data", {}).get("result", {}).get("results", [{}])[0]
card_sequence = card_data.get("sequence")
space_prefix_code = card_data.get("spacePrefixCode", space_code)
card_url = f"https://console.cloud.baidu-int.com/devops/icafe/issue/{space_prefix_code}-{card_sequence}/show"
print(f"卡片链接: {card_url}")
```

### 示例 2: 流转到开发中

```python
from scripts.platform_client import PlatformClient

client = PlatformClient(cookie="your-cookie")

# 将卡片流转到开发中
result = client.update_status_to_dev(
    issue_id="joytest-1971",
    operator="shijiazheng",
    platform="appgo"
)
```

### 示例 3: 查询卡片

```python
from scripts.platform_client import PlatformClient

client = PlatformClient(cookie="your-cookie")

# 查询所有卡片
result = client.query_icafe_cards(
    icafe_space="joytest",
    operator="shijiazheng",
    platform="appgo",
    iql_text="sequence > 0"
)

# 使用 IQL 条件查询
result = client.query_icafe_cards(
    icafe_space="joytest",
    operator="shijiazheng",
    platform="appgo",
    iql_text="类型 = Story AND 流程状态 = 新建"
)

# 查询当前用户负责的 Bug 卡片
result = client.query_icafe_cards(
    icafe_space="joytest",
    operator="shijiazheng",
    platform="appgo",
    iql_text="类型 = Bug AND 负责人 = currentUser"
)

# 分页查询
result = client.query_icafe_cards(
    icafe_space="joytest",
    operator="shijiazheng",
    platform="appgo",
    iql_text="标题 ~ 测试",
    page=2,
    page_size=50
)
```

### 示例 4: 批量提测准出

```python
from scripts.platform_client import PlatformClient

client = PlatformClient(cookie="your-cookie")

# 发起提测
result = client.batch_approve(
    issue_ids=["joytest-1971", "joytest-1972"],
    operator="shijiazheng",
    platform="appgo",
    operator_type="发起提测"
)

# 准出
result = client.batch_approve(
    issue_ids=["joytest-1971"],
    operator="shijiazheng",
    platform="appgo",
    operator_type="准出"
)
```

---

## 交互规范

### 必填参数

**重要：调用任何 API 时，必须从用户处获取以下参数，不得使用默认值。**

#### 1. 创建卡片接口
- `space_code` - iCafe 空间标识，必须询问用户
- `title` - 卡片标题，必须询问用户
- `card_type` - 卡片类型（Story/Task/Bug/Epic），必须询问用户
- `platform` - 平台标识，必须询问用户
- `develop_name` - 开发人员姓名，必须询问用户

#### 2. 流转到开发中接口
- `issue_id` - 卡片完整 ID（格式：space_code-card_sequence），必须询问用户
- `operator` - 操作人，必须询问用户
- `platform` - 平台标识，必须询问用户

#### 3. 查询 iCafe 卡片接口
- `icafe_space` - iCafe 空间标识，必须询问用户
- `operator` - 操作人，必须询问用户
- `platform` - 平台标识，必须询问用户
- `iql_text` - IQL 查询表达式，必须询问用户（查询所有可使用: sequence > 0）

#### 4. 批量提测准出接口
- `issue_ids` - 卡片 ID 列表，必须询问用户
- `operator` - 操作人，必须询问用户
- `platform` - 平台标识，必须询问用户
- `operator_type` - 操作类型（发起提测/准出），必须询问用户

### 认证方式

本技能使用 Cookie 进行认证。使用前需要：
1. 获取 Cookie（从浏览器开发者工具中获取）
2. 在初始化客户端时传入：
   ```python
   client = PlatformClient(cookie="your-cookie-here")
   ```

### 错误处理

1. 用户未提供必要参数时，直接询问用户
2. API 调用失败时，返回具体错误信息给用户
3. Cookie 过期或无效时，提示用户重新获取

---

## 响应格式

### 创建卡片成功响应

```json
{
    "code": 200,
    "msg": "ok",
    "data": {
        "result": {
            "results": [
                {
                    "sequence": 1971,
                    "spacePrefixCode": "joytest"
                }
            ]
        }
    }
}
```

### 流转状态成功响应

```json
{
    "code": 200,
    "msg": "ok",
    "data": {
        "issueId": "joytest-1971",
        "message": "卡片状态流转成功",
        "operator": "shijiazheng",
        "status": "开发中"
    }
}
```

---

## 卡片链接格式

创建卡片成功后，可通过以下格式访问卡片：

```
https://console.cloud.baidu-int.com/devops/icafe/issue/{space_prefix_code}-{card_sequence}/show
```

示例：`https://console.cloud.baidu-int.com/devops/icafe/issue/joytest-1971/show`
