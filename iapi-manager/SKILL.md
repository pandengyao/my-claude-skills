---
name: iapi-manager
description: iapi-manager是一个与iAPI平台交互进行接口管理设计的技能，支持项目检索、API接口详情获取、导入、关键字检索等核心功能。当用户需要以下功能时使用：(1) 使用自然语言查询搜索API，(2) 浏览或列出iAPI项目中的API，(3) 获取API详情或规范（Swagger/Markdown格式），(4) 将OpenAPI/Swagger规范导入iAPI，(5) 列出或发现iAPI项目。自动处理通过COMATE_AUTH_TOKEN或~/.comate/login文件的身份认证。
---

# iAPI 管理器

## 概述

通过HTTP API与iAPI平台交互。支持项目检索、API接口详情获取、导入、关键字检索等核心操作。

## 核心功能

### 1. 搜索API

使用自然语言查询进行语义理解的API搜索。

**使用Python客户端**:
```bash
~/py312/bin/python3 scripts/iapi_client.py search-apis \
  --query "用户认证" \
  --num 10 \
  --project-ids proj1 proj2
```

**直接实现**:
```python
from scripts.iapi_client import IapiClient

client = IapiClient()
result = client.search_apis(
    query="查找与用户认证相关的API",
    num=10,
    project_ids=["465657", "436346457"]  # 可选
)

if result['success']:
    for api in result['data']:
        print(f"{api['method']} {api['path']} - {api['apiName']}")
        print(f"  项目: {api['projectName']}")
        print(f"  链接: {api['link']}")
```

### 2. 获取API详情

获取Swagger或Markdown格式的详细API规范。

**Swagger格式**（用于代码生成）:
```python
result = client.get_api_detail("1234567", export_type="swagger")
# 返回OpenAPI/Swagger JSON规范
```

**Markdown格式**（用于文档）:
```python
result = client.get_api_detail("1234567", export_type="markdown")
# 返回格式化的markdown文档
```

**多个API**（逗号分隔）:
```python
result = client.get_api_detail("123,456,789")
# 并发获取多个API
```

### 3. 列出项目API

获取指定项目中的所有API及格式化的详细信息。

```python
result = client.get_api_list("project-id-456")

if result['success']:
    for api in result['data']:
        print(f"{api['apiName']} - {api['method']} {api['path']}")
        print(f"  参数: {api['parameters']}")
        print(f"  请求体: {api['requestBody']}")
        print(f"  响应: {api['responses']}")
```

### 4. 发现项目

**获取可编辑项目**（用于导入操作）:
```python
result = client.get_editable_projects()
# 返回用户可以创建/修改API的项目
```

**获取所有用户项目**（用于浏览）:
```python
result = client.get_user_projects()
# 返回所有可访问的项目（包括只读）
```

### 5. 导入OpenAPI

将OpenAPI/Swagger规范导入iAPI项目。

```python
# 读取OpenAPI文件
with open('api-spec.json', 'r') as f:
    swagger_data = f.read()

# 导入并控制覆盖模式
result = client.import_openapi(
    project_id="1234567",
    swagger_data=swagger_data,
    api_overwrite_mode="SKIP",      # SKIP, OVERWRITE, 或 MERGE
    schema_overwrite_mode="SKIP"    # SKIP, OVERWRITE, 或 MERGE
)

if result['success']:
    import_result = result['data']
    print(f"导入的API数量: {len(import_result['apiCollection'])}")
    print(f"导入的Schema数量: {len(import_result['schemaCollection'])}")
```

## 身份认证

身份认证是自动的。客户端从以下位置读取token：
1. 环境变量 `COMATE_AUTH_TOKEN`
2. 登录文件 `~/.comate/login`

如果token没有`Bearer-`前缀，会自动添加。

**验证身份认证**:
```python
client = IapiClient()
if not client.auth_token:
    print("错误: 未找到身份认证token")
    print("请设置COMATE_AUTH_TOKEN或创建~/.comate/login文件")
```

## 常见工作流

### 工作流1: 查找并获取API详情

```python
# 1. 搜索API
result = client.search_apis("支付处理", num=5)
apis = result['data']

# 2. 获取详细文档
api_id = apis[0]['apiId']
doc = client.get_api_detail(api_id, export_type="markdown")
print(doc['data'][0])  # Markdown文档
```

### 工作流2: 导入并验证API

```python
# 1. 获取目标项目
projects = client.get_editable_projects()
project_id = projects['data'][0]['projectId']

# 2. 导入OpenAPI规范
with open('openapi.yaml') as f:
    result = client.import_openapi(
        project_id=project_id,
        swagger_data=f.read(),
        api_overwrite_mode="MERGE"
    )

# 3. 验证导入
api_list = client.get_api_list(project_id)
print(f"项目中的API总数: {len(api_list['data'])}")
```

### 工作流3: 跨项目API检索

```python
# 1. 获取所有可访问的项目
projects = client.get_user_projects()
project_ids = [p['projectId'] for p in projects['data']]

# 2. 跨所有项目搜索
result = client.search_apis(
    query="限流",
    num=20,
    project_ids=project_ids
)

# 3. 按项目分组结果
from collections import defaultdict
by_project = defaultdict(list)
for api in result['data']:
    by_project[api['projectName']].append(api)
```

## 资源

### scripts/iapi_client.py

该脚本使用 `requests` 库进行 HTTP 请求。

实现所有iAPI操作并自动处理身份认证的Python客户端。可以用作：
- **库**: 导入`IapiClient`类进行编程访问
- **CLI**: 直接使用命令行参数运行

CLI示例:
```bash
# 搜索API
~/py312/bin/python3 scripts/iapi_client.py search-apis --query "认证" --num 10

# 获取API详情
~/py312/bin/python3 scripts/iapi_client.py get-api-detail --api-id 123 --export-type swagger

# 列出项目API
~/py312/bin/python3 scripts/iapi_client.py get-api-list --project-id 456

# 获取项目
~/py312/bin/python3 scripts/iapi_client.py get-editable-projects
~/py312/bin/python3 scripts/iapi_client.py get-user-projects

# 导入OpenAPI
~/py312/bin/python3 scripts/iapi_client.py import-openapi \
  --project-id 789 \
  --swagger-file openapi.json \
  --api-overwrite MERGE
```

### references/api_reference.md

完整的API文档，包括：
- 所有6个端点规范
- 请求/响应格式
- 身份认证详情
- 参数格式化规则
- 错误代码和处理

当需要关于API端点、参数或响应结构的详细信息时，请阅读此参考文档。

## 错误处理

所有方法都返回带有`success`字段的字典：

```python
result = client.search_apis("测试")

if result['success']:
    data = result['data']
    # 处理成功结果
else:
    error = result['error']
    code = result.get('code')
    print(f"错误 ({code}): {error}")
```

常见错误代码：
- `403`: 身份认证失败 - 检查token
- `404`: 资源未找到 - 验证ID
- `500`: 服务器错误 - 检查请求格式

## 使用技巧

- **优先使用搜索**: 自然语言搜索通常比浏览项目列表更快
- **批量获取API详情**: 向`get_api_detail`传递逗号分隔的ID进行并发获取
- **合并导入**: 更新现有API时使用`MERGE`模式以保留手动更改
- **限定搜索范围**: 使用`project_ids`将搜索限制在特定项目以获得更快的结果
