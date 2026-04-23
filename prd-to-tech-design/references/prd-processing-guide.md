# PRD 处理指南

> 本文档详细说明如何处理 PRD 文档,包括图片下载和优化版生成

---

## 目的

在技术设计过程中,需要多次阅读和引用 PRD 文档。为了提高效率和可靠性:

1. **下载 PRD 图片到本地** - 避免图片链接失效,确保设计过程中随时可查看
2. **生成优化版 PRD** - 优化格式和可读性,便于多次阅读和引用

同时支持两类 PRD 输入来源:
- 本地/仓库文档路径(如 `.md`、`.docx`、`.pdf`)
- 知识库链接(如 `https://ku.baidu-int.com/...`)

---

## 处理流程

### 第一步:读取原始 PRD

先识别用户提供的 PRD 来源,再统一转换为本地 Markdown 进行后续处理。

#### 1.1 输入来源识别

1. **本地/仓库文档路径**
   - 若是 `.md`,直接读取
   - 若是 `.docx`/`.pdf`,先转换为 `.md` 再读取

2. **知识库链接**
   - 解析 URL 域名
   - 若域名是 `ku.baidu-int.com`,**必须**按以下步骤处理:

     **步骤 2.1: 提取 doc_id**
     - URL 格式: `https://ku.baidu-int.com/knowledge/{path1}/{path2}/{path3}/{doc_id}`
     - doc_id 是 URL 最后一个斜杠后的字符串
     - 示例: `https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/85I3JF2Ic4/0KSeXIPWR5/5DF8f3AKCn8rSy`
       - doc_id = `5DF8f3AKCn8rSy`

     **步骤 2.2: 调用 ku-doc-manage API**
     使用 Bash 工具执行 Python 脚本:
     ```bash
     cd ~/.claude/skills/ku-doc-manage && python3 -c "
     from scripts.ku_api_client import KuApiClient
     client = KuApiClient()
     result = client.query_content(doc_id='YOUR_DOC_ID')
     import json
     print(json.dumps(result, ensure_ascii=False))
     "
     ```

     **⚠️ 重要**: 不要使用 playwright 或浏览器工具访问知识库，必须使用上述 API。

     **步骤 2.3: 保存 JSON 结果**
     - 将返回的 JSON 保存到: `tech_design/{需求名称}/source_prd/ku-content.json`

     **步骤 2.4: 转换为 Markdown**
     使用 ku-json-to-md 脚本:
     ```bash
     python ~/.claude/skills/ku-json-to-md/scripts/ku_json_to_md.py \
       --input tech_design/{需求名称}/source_prd/ku-content.json \
       --output tech_design/{需求名称}/source_prd/PRD-原始.md
     ```

#### 1.2 读取本地 Markdown PRD

使用 Read 工具读取本地 Markdown PRD:

```
Read: tech_design/{需求名称}/source_prd/PRD-原始.md
```

**关键信息提取:**
- 文档结构(标题层级、章节划分)
- 图片链接(Markdown 格式:`![alt](url)`)
- 功能描述、业务规则、约束条件
- 非功能需求(性能、安全、可用性)

### 第二步:识别图片链接

扫描本地 Markdown PRD,识别所有图片链接:

**图片类型识别:**

1. **内网图片**(需要认证)
   - `https://weiyun.baidu.com/xxx`
   - `https://ku.baidu-int.com/xxx`
   - `http://internal-image-server/xxx`
   - 公司内部图床链接

2. **外网图片**(公开访问)
   - `https://imgur.com/xxx`
   - `https://i.imgur.com/xxx.png`
   - 云存储公开链接

3. **本地图片**(相对或绝对路径)
   - `./images/flow-diagram.png`
   - `/docs/assets/ui-mockup.png`

**提取图片清单:**

| 序号 | 图片描述 | 原始链接 | 类型 | 状态 |
|------|---------|---------|------|------|
| 1 | 账号管理流程图 | https://weiyun.baidu.com/xxx/flow.png | 内网 | 待下载 |
| 2 | UI 原型图 | https://imgur.com/xxx.png | 外网 | 待下载 |
| 3 | 数据库 ER 图 | ./assets/er-diagram.png | 本地 | 待复制 |

### 第三步:创建工作目录

创建技术设计工作目录:

```bash
tech_design/
└── {需求名称}/
    └── prd_assets/    # PRD 图片资源目录
```

**目录命名规则:**
- 需求名称:简洁清晰,如"账号管理"、"短信配置"、"FAQ知识库"
- 避免特殊字符和空格
- 使用中文或英文,保持一致

### 第四步:下载图片

根据图片类型,使用不同的下载方式:

#### 4.1 下载内网图片

**使用内置脚本:**

```bash
# 从 JSON 文件提取并下载图片（推荐）
python3 ~/.claude/skills/prd-to-tech-design/scripts/download_images.py \
  --json tech_design/{需求名称}/source_prd/ku-content.json \
  --output tech_design/{需求名称}/prd_assets/

# 或从 Markdown 文件提取并下载
python3 ~/.claude/skills/prd-to-tech-design/scripts/download_images.py \
  --markdown tech_design/{需求名称}/source_prd/PRD-原始.md \
  --output tech_design/{需求名称}/prd_assets/
```

**脚本功能:**
- 自动识别 JSON/Markdown 中的内网图片链接（weiyun.baidu.com）
- 自动识别图片格式（png/jpg/gif/webp）
- 支持自定义文件名前缀

#### 4.2 下载外网图片

**使用 WebFetch 或浏览器工具:**

```python
# 示例:使用 Python 下载外网图片
import requests

def download_image(url, output_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

# 下载图片
download_image(
    'https://imgur.com/xxx.png',
    'tech_design/账号管理/prd_assets/ui-mockup.png'
)
```

#### 4.3 复制本地图片

**使用 Bash 工具:**

```bash
# 复制本地图片到工作目录
cp ./assets/er-diagram.png tech_design/账号管理/prd_assets/er-diagram.png
```

#### 4.4 图片重命名规则

使用描述性文件名,便于识别:

**推荐命名:**
- `flow-diagram.png` - 流程图
- `ui-mockup-01.png` - UI 原型图 1
- `ui-mockup-02.png` - UI 原型图 2
- `er-diagram.png` - 数据库 ER 图
- `architecture.png` - 架构图
- `sequence-diagram.png` - 时序图

**避免命名:**
- `image1.png` - 无意义
- `屏幕快照 2024-01-15.png` - 包含日期
- `IMG_1234.png` - 无描述信息

### 第五步:生成优化版 PRD

创建优化版 PRD:`tech_design/{需求名称}/PRD-优化版.md`

#### 5.1 优化原则

**核心原则:保留原 PRD 完整信息,不添加、不删减、不修改。**

**优化内容:**

1. **格式优化**
   - 统一标题层级(# 一级标题、## 二级标题、### 三级标题)
   - 规范列表格式(使用 `-` 或 `1.` 统一风格)
   - 美化表格(对齐列、统一分隔符)
   - 规范代码块(添加语言标识)

2. **结构优化**
   - 添加文档目录(TOC)
   - 合并相似章节(如多个"背景"章节合并为一个)
   - 调整章节顺序(按逻辑顺序排列)
   - 去除重复内容

3. **图片本地化**
   - 将所有图片链接替换为本地路径
   - 格式:`![描述](./prd_assets/图片名.png)`
   - 确保图片描述清晰

4. **可读性优化**
   - 添加章节说明(简短的章节概述)
   - 规范术语使用(统一专业术语)
   - 优化段落结构(避免过长段落)

#### 5.2 优化版结构

```markdown
# PRD 优化版 - {需求名称}

> **原始 PRD**: {原始文档路径}
> **优化时间**: {日期}
> **优化说明**: 保留原 PRD 完整信息,优化格式和可读性,图片已本地化

---

## 目录

- [一、需求背景](#一需求背景)
- [二、功能详细设计](#二功能详细设计)
  - [2.1 功能模块 A](#21-功能模块-a)
  - [2.2 功能模块 B](#22-功能模块-b)
- [三、非功能需求](#三非功能需求)
- [四、排期计划](#四排期计划)

---

## 一、需求背景

### 1.1 业务背景

[从原 PRD 提取,保持原文]

### 1.2 用户价值

[从原 PRD 提取,保持原文]

### 1.3 使用场景

[从原 PRD 提取,保持原文]

---

## 二、功能详细设计

### 2.1 功能模块 A

#### 功能描述

[从原 PRD 提取,保持原文]

#### 流程图

![账号管理流程图](./prd_assets/flow-diagram.png)

**流程说明:**
1. 用户点击"添加账号"按钮
2. 系统弹出账号配置表单
3. 用户填写账号信息并提交
4. 系统验证并保存账号信息

#### 业务规则

- 规则 1:[从原 PRD 提取]
- 规则 2:[从原 PRD 提取]

#### UI 原型

![UI 原型图](./prd_assets/ui-mockup-01.png)

---

## 三、非功能需求

### 3.1 性能要求

[从原 PRD 提取,保持原文]

### 3.2 安全要求

[从原 PRD 提取,保持原文]

### 3.3 可用性要求

[从原 PRD 提取,保持原文]

---

## 四、排期计划

[从原 PRD 提取,保持原文]

---

## 附录

### 附录 A:术语表

| 术语 | 定义 |
|------|------|
| 账号 | [定义] |
| 平台 | [定义] |

### 附录 B:参考资料

- 原始 PRD:{原始文档路径}
- 相关技术文档:{链接}
```

#### 5.3 优化示例

**原始 PRD(格式混乱):**

```markdown
# 账号管理功能

背景:
用户需要管理多个平台的账号

功能:
1、添加账号
2、编辑账号
3、删除账号

![](https://weiyun.baidu.com/xxx/flow.png)

性能要求:接口响应时间<500ms
```

**优化版 PRD(格式规范):**

```markdown
# PRD 优化版 - 账号管理功能

> **原始 PRD**: /docs/account-management-prd.md
> **优化时间**: 2026-03-03
> **优化说明**: 保留原 PRD 完整信息,优化格式和可读性,图片已本地化

---

## 目录

- [一、需求背景](#一需求背景)
- [二、功能详细设计](#二功能详细设计)
- [三、非功能需求](#三非功能需求)

---

## 一、需求背景

用户需要管理多个平台的账号,包括添加、编辑、删除等操作。

---

## 二、功能详细设计

### 2.1 账号管理功能

#### 功能列表

1. **添加账号** - 用户可以添加新的平台账号
2. **编辑账号** - 用户可以修改已有账号的配置
3. **删除账号** - 用户可以删除不再使用的账号

#### 流程图

![账号管理流程图](./prd_assets/flow-diagram.png)

---

## 三、非功能需求

### 3.1 性能要求

- 接口响应时间 < 500ms
```

### 第六步:验证优化版 PRD

**验证清单:**

- [ ] 所有原 PRD 信息是否完整保留?
- [ ] 图片链接是否全部替换为本地路径?
- [ ] 图片文件是否全部下载成功?
- [ ] 格式是否统一规范?
- [ ] 目录是否完整准确?
- [ ] 章节结构是否清晰?

**如果发现问题:**
- 缺失信息:立即补充
- 图片下载失败:记录在"待确认问题"中
- 格式问题:重新优化

---

## 常见问题

### Q1: 内网图片下载失败怎么办?

**A:** 检查以下几点:
1. 确认图片链接是否有效
2. 确认网络是否可以访问内网
3. 下载失败的图片会记录在日志中,可在"待确认问题"中标注

### Q2: 图片链接失效怎么办?

**A:** 在优化版 PRD 中标注"[图片缺失]",并在"待确认问题"中列出:

```markdown
## 待确认问题

### 图片缺失

1. **账号管理流程图**(原链接:https://xxx/flow.png)
   - 状态:链接失效
   - 建议:请用户提供新的图片链接或本地文件
```

### Q3: 原 PRD 格式很乱,可以大幅修改吗?

**A:** 不可以。优化版 PRD 必须保留原 PRD 的所有信息,只能优化格式,不能修改内容。

**允许的优化:**
- 统一标题层级
- 规范列表格式
- 美化表格
- 添加目录

**不允许的修改:**
- 删除任何内容
- 添加新的功能描述
- 修改业务规则
- 改变功能优先级

### Q4: 优化版 PRD 需要用户确认吗?

**A:** 不需要。优化版 PRD 只是格式优化,不改变内容,无需用户确认。

但如果发现以下情况,需要向用户确认:
- 原 PRD 内容矛盾(如同一功能有两种不同描述)
- 原 PRD 信息不完整(如缺少关键业务规则)
- 图片下载失败

### Q5: 如果用户后续修改了 PRD 怎么办?

**A:** 同步更新优化版 PRD,并在"PRD 变更记录"中记录:

```markdown
## PRD 变更记录

### 变更 1:代理配置层级调整(2026-03-03)

- **变更来源**:用户在技术设计过程中纠正
- **原 PRD 描述**:代理配置在账号级别
- **修改后描述**:代理配置在平台级别,一个平台共享一个代理配置
- **影响范围**:数据库设计、接口设计
- **更新时间**:2026-03-03
```

---

## 最佳实践

### 1. 图片命名规范

**推荐:**
- 使用描述性名称:`flow-diagram.png`、`ui-mockup-login.png`
- 使用连字符分隔:`account-management-flow.png`
- 使用小写字母:`architecture.png`(不是 `Architecture.png`)

**避免:**
- 无意义名称:`image1.png`、`pic.png`
- 包含日期:`screenshot-2024-01-15.png`
- 包含特殊字符:`流程图@2024.png`

### 2. 优化版 PRD 结构

**推荐结构:**
```
# PRD 优化版 - {需求名称}
> 元信息

## 目录
[自动生成]

## 一、需求背景
### 1.1 业务背景
### 1.2 用户价值
### 1.3 使用场景

## 二、功能详细设计
### 2.1 功能模块 A
#### 功能描述
#### 流程图
#### 业务规则
#### UI 原型

## 三、非功能需求
### 3.1 性能要求
### 3.2 安全要求
### 3.3 可用性要求

## 四、排期计划

## 附录
### 附录 A:术语表
### 附录 B:参考资料
```

### 3. 工作目录组织

**推荐结构:**
```
tech_design/
└── {需求名称}/
    ├── PRD-优化版.md              # 优化版 PRD
    ├── 技术设计-{功能名称}.md      # 技术设计文档
    └── prd_assets/                # PRD 图片资源
        ├── flow-diagram.png
        ├── ui-mockup-01.png
        ├── ui-mockup-02.png
        └── er-diagram.png
```

### 4. 图片引用规范

**在优化版 PRD 中:**
```markdown
![账号管理流程图](./prd_assets/flow-diagram.png)
```

**在技术设计文档中:**
```markdown
![账号管理流程图](./prd_assets/flow-diagram.png)

**流程说明:**
1. 用户点击"添加账号"按钮
2. 系统弹出账号配置表单
3. ...
```

---

## 参考资料

- Markdown 格式规范
- 技术设计文档模板:`tech-design-template.md`

---

**文档版本**: v1.0
**创建时间**: 2026-03-03
**维护状态**: 🟢 活跃维护中
