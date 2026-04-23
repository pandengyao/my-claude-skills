# iAPI API 参考文档

## 概述

提供HTTP端点用于与iAPI平台交互。实现了6个核心操作，支持项目管理、API发现和OpenAPI导入功能。

**基础URL**: `https://iapi.now.baidu-int.com`

**身份认证**: 所有端点都需要 `x-ac-Authorization` 请求头，携带Bearer token

**参数说明**: 项目ID和API ID 都是数字组合，如"356576868", 不包含'project-'、'api-'等字符

## 端点说明

### 1. 获取API详情

**端点**: `GET /api/v1/iapi/api/detail`

**描述**: 获取一个或多个API的详细信息。支持多种导出格式。

**查询参数**:
- `apiId` (必需): API ID，支持逗号分隔的多个ID进行批量获取
- `exportType` (可选): 导出格式 - `swagger` (默认) 或 `markdown`
- `apiId`为数字组合，如"356576868", 要去掉'api-'等字符前缀

**响应**: API详情列表，结构如下：
- `swagger`格式: 完整的OpenAPI/Swagger规范
- `markdown`格式: 格式化的markdown文档

**使用场景**:
- 获取用于代码生成的API规范
- 获取可读性强的API文档
- 并发获取多个API详情

---

### 2. 获取API列表

**端点**: `GET /api/v1/iapi/api/list`

**描述**: 获取项目中的所有API及格式化的信息。

**查询参数**:
- `projectId` (必需): 项目ID

**响应**: API列表，包含格式化的详情：
- `apiId`: API标识符
- `apiName`: API名称
- `method`: HTTP方法
- `path`: API路径
- `description`: API描述
- `parameters`: 格式化的参数列表 (格式: `name[type][required/optional]: description`)
- `requestBody`: 格式化的请求体schema
- `responses`: 格式化的响应schema
- `link`: iAPI平台中API的直接链接

**使用场景**:
- 浏览项目中的所有API
- 生成API目录
- API发现和探索

---

### 3. 获取可编辑项目

**端点**: `GET /api/v1/iapi/projects/editable`

**描述**: 获取用户具有编辑权限的项目列表。

**查询参数**: 无

**响应**: 项目列表，包含：
- `projectId`: 项目标识符，为数字组合，如"356576868"
- `projectName`: 项目名称
- `roleType`: 用户在项目中的角色
- `link`: iAPI平台中项目的直接链接

**使用场景**:
- 列出可用于导入操作的项目
- 确定用户可以在哪里创建/修改API
- 为写操作选择项目

---

### 4. 获取用户项目

**端点**: `GET /api/v1/iapi/projects/user`

**描述**: 获取用户可访问的所有项目（包括只读访问）。

**查询参数**: 无

**响应**: 项目列表，结构与可编辑项目相同。

**使用场景**:
- 浏览所有可访问的项目
- 项目发现
- 将API搜索范围限定到特定项目

---

### 5. 导入OpenAPI

**端点**: `POST /api/v1/iapi/import/openapi`

**描述**: 将OpenAPI/Swagger规范导入iAPI项目。

**请求体**:
```json
{
  "projectId": "string (必需)",
  "swaggerData": "string (必需) - OpenAPI/Swagger JSON或YAML内容",
  "apiOverwriteMode": "string (可选) - SKIP (默认), OVERWRITE, 或 MERGE",
  "schemaOverwriteMode": "string (可选) - SKIP (默认), OVERWRITE, 或 MERGE"
}
```

**覆盖模式**:
- `SKIP`: 如果API/schema已存在则跳过
- `OVERWRITE`: 完全替换现有的API/schema
- `MERGE`: 将新内容与现有内容合并

**响应**:
```json
{
  "apiCollection": [
    {
      "id": "string",
      "name": "string",
      "method": "string",
      "path": "string",
      "status": "created|updated|skipped"
    }
  ],
  "schemaCollection": [
    {
      "id": "string",
      "name": "string",
      "status": "created|updated|skipped"
    }
  ]
}
```

**使用场景**:
- 从外部OpenAPI规范导入API
- 将API定义与外部系统同步
- 在项目之间迁移API

---

### 6. 搜索API

**端点**: `POST /api/v1/iapi/api/search`

**描述**: 使用自然语言查询进行API的语义搜索。

**请求体**:
```json
{
  "query": "string (必需) - 自然语言搜索查询",
  "num": "integer (可选) - 最大结果数，默认10",
  "projectIds": ["string"] (可选) - 将搜索限制到特定项目
}
```

**响应**: 匹配的API列表，包含：
- `apiId`: API标识符
- `apiName`: API名称
- `method`: HTTP方法
- `path`: API路径
- `description`: API描述
- `projectId`: 包含该API的项目
- `projectName`: 项目名称
- `score`: 相关性得分
- `link`: API的直接链接

**使用场景**:
- 通过自然语言描述查找API
- 为用例发现相关API
- 通过语义理解跨项目搜索

## 身份认证详情

### Token来源（优先级顺序）

1. **环境变量**: `COMATE_AUTH_TOKEN`
2. **登录文件**: `~/.comate/login`

### Token格式

- 如果token不以`Bearer-`开头，会自动添加前缀
- 最终请求头: `x-ac-Authorization: Bearer-{token}`

## 响应格式

所有端点返回标准化的响应：

```json
{
  "code": 200,
  "msg": "success",
  "data": { /* 端点特定的数据 */ }
}
```

**错误响应**:
- `code: 403` - 身份认证失败
- `code: 404` - 资源未找到
- `code: 500` - 服务器错误

## 参数格式化

API列表和详情端点将参数格式化为：
```
name[type][required/optional]: description
```

对于嵌套对象：
```
objectName[object][required]:
  - field1[string][required]: 描述
  - field2[number][optional]: 描述
```

最大嵌套深度: 2层
