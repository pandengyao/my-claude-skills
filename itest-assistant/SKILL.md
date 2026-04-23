---
name: itest-assistant
description: 当用户询问关于 iTest 平台提测、准出相关的问题、需要查询提测信息、创建或确认提测、管理准出流程，或访问相关测试数据时，应使用此技能。它提供了全面的 API 客户端，支持提测的发起、确认、准出及相关数据查询。
---

# iTest 提测准出助手

## 概述

本技能提供了一个与 iTest 平台提测准出系统交互的 API 客户端。支持提测操作，包括查询提测信息、发起提测、确认提测、发起准出、确认准出，以及访问相关的测试计划和空间数据。

## 重要说明

**当用户请求的操作需要用户 ID（userId）时，必须直接询问用户的 userId，不要使用任何默认值。**

用户 ID 是百度内部的唯一用户标识，如 "shijiazheng"、"v_liuxiang" 等。

## 快速开始

使用 iTest API 客户端，客户端会自动从环境变量或登录文件读取认证 token：

```python
from scripts.itest_client import ITestClient, ITestConfig

# 方式一：使用默认配置（自动读取认证 token）
client = ITestClient()

# 方式二：自定义配置
config = ITestConfig(
    base_url="http://itest-api.baidu-int.com",
    timeout=30
)
client = ITestClient(config)
```

## 核心 API 方法

### 1. 查询用户有权限的空间列表

```python
spaces = client.get_accessible_spaces("your-user-id")
# 返回：用户有权限的空间列表
```

### 2. 根据空间获取提测详情

```python
details = client.get_space_test_details(
    space_code="your-space-code",
    is_req_succ=True,      # 是否成功确认提测
    is_permit_out=False,   # 是否准出
    page_num=1,
    page_size=10
)
# 返回：提测列表和总数
```

### 3. 获取未完成的提测

```python
tests = client.get_unfinished_tests(
    module="auth-service",
    branch="feature/login"
)
# 或使用流水线构建 ID
tests = client.get_unfinished_tests(
    pipeline_build_id=123456
)
# 返回：未完成的提测列表
```

### 4. 发起提测

```python
result = client.create_test_request(
    name="首次提测",
    test_plan_id=243597,
    test_users=["user1", "user2"],
    modules=[{"module": "auth-service", "branch": "feature/login"}],
    issues=[{"issueId": "AGILE-2", "issueType": "Story"}],
    operator="your-user-id",
    test_note="重点测试登录失败场景"
)
# 返回：创建的提测记录详情
```

### 5. 获取待确认的提测

```python
tests = client.get_unconfirmed_tests(
    username="your-user-id",
    issues="AGILE-2,AGILE-3",
    keyword="登录",
    modules="auth-service",
    create_test_user="another-user"
)
# 返回：待确认的提测列表
```

### 6. 确认提测

```python
result = client.confirm_test_request(
    request_test_id=123456,
    result=True,   # true - 接受，false - 驳回
    confirm_user="your-user-id",
    test_plan_id=243597,
    test_plan_name="测试计划名称",
    space_code="your-space-code"
)
# 返回：操作结果
```

### 7. 获取未准出的提测（根据用户或模块）

```python
# 根据用户获取
tests = client.get_not_permit_out_tests(
    username="your-user-id",
    start_time=1234567890000,  # 毫秒时间戳
    end_time=1234567899000
)

# 根据模块获取
tests = client.get_not_permit_out_tests(
    modules=[{"module": "auth-service", "branch": "feature/login"}]
)
# 返回：未准出的提测列表
```

### 8. 发起准出

```python
result = client.create_permit_out(
    request_test_id=123456,
    operator="your-user-id",
    permit_out_users=["user1", "user2"]
)
# 返回：操作结果
```

### 9. 确认准出

```python
result = client.confirm_permit_out(
    permit_out_id=123456,
    result=True,   # true - 接受 / false - 驳回
    confirm_user="your-user-id",
    desc_note="准出通过",
    inform_users=["user1", "user2"]
)
# 返回：操作结果
```

### 10. 批量确认准出（一键准出）

```python
result = client.batch_confirm_permit_out(
    permit_out_ids=[123, 234, 345],
    result=True,
    confirm_user="your-user-id"
)
# 返回：操作结果
```

### 11. 从 Bot 发起提测

```python
result = client.create_test_request_from_bot(
    operator="your-user-id",
    test_users=["user1", "user2"],
    modules=[{"module": "auth-service", "branch": "feature/login"}],
    is_pipeline=True,
    pipeline_conf_id=123,
    issue_ids=["AGILE-2", "AGILE-3"],
    test_note="测试备注",
    name="任务名"
)
# 返回：操作结果
```

### 12. 创建测试计划

```python
result = client.create_test_plan(
    name="首次提测计划",
    space_code="your-space-code",
    creator="your-user-id",
    test_owners=["user1", "user2"]
)
# 返回：创建的测试计划
```

### 13. 根据用户获取未准出的提测

```python
tests = client.get_not_permit_out_by_user(
    username="your-user-id",
    test_users=["user1", "user2"],
    start_time=1234567890000,
    end_time=1234567899000,
    space_name="测试空间",
    modules=[{"module": "auth-service", "branch": "feature/login"}]
)
# 返回：未准出的提测列表
```

### 14. 根据提测 ID 获取提测相关信息

```python
test_info = client.get_test_by_id(test_id=123456)
# 返回：提测信息
# 可生成访问链接：https://console.cloud.baidu-int.com/itest/#/console/test/{testId}/0
```

## 数据模型

### 模块信息

```python
{
    "module": "模块名称",      # 如 "auth-service"
    "branch": "模块分支"       # 如 "feature/login"
}
```

### 卡片信息

```python
{
    "issueId": "卡片标识",     # 如 "AGILE-2"
    "issueType": "卡片类型"    # 如 "Story"
}
```

## 错误处理

所有 API 方法可能抛出以下异常：
- `ValueError`：当缺少或无效的必需参数时
- `requests.RequestException`：当 HTTP 请求失败时

建议适当处理这些异常：

```python
try:
    result = client.create_test_request(
        name="首次提测",
        test_plan_id=243597,
        test_users=["user1"],
        modules=[{"module": "auth-service", "branch": "feature/login"}],
        issues=[{"issueId": "AGILE-2", "issueType": "Story"}],
        operator="your-user-id"
    )
except ValueError as e:
    print(f"参数无效: {e}")
except requests.RequestException as e:
    print(f"API 请求失败: {e}")
```

## 配置

### 认证配置

客户端使用 `accessToken` 查询参数进行认证，认证 token 按以下优先级读取：

1. **环境变量**：`ITEST_ACCESS_TOKEN`
2. **登录文件**：`~/.comate/itest_login`

登录文件格式：纯 token（单行）

示例设置环境变量：
```bash
export ITEST_ACCESS_TOKEN="your-token-here"
```

示例创建登录文件：
```bash
echo "your-token-here" > ~/.comate/itest_login
```

### 可选配置

可以通过 `ITestConfig` 自定义以下参数：
- `base_url`：iTest API 基础 URL，默认为 `http://itest-api.baidu-int.com`
- `timeout`：请求超时时间（秒），默认为 30

## 资源

### scripts/itest_client.py

主要的 API 客户端实现，包含所有提测准出相关的方法。此脚本用于：
- 执行提测查询和操作
- 管理准出流程
- 访问测试计划和空间数据

该脚本使用 `requests` 库进行 HTTP 请求，并为每个方法包含完整的文档字符串。
