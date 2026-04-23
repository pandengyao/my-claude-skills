# CR Tool 使用说明（SanJS）

本文件仅说明代码评审会用到的 `cr_tool`，不包含额外流程。

## 可用 cr_tool

- `san-doc`：查询 San.js 官方文档（API、生命周期、模板语法）
- `san-faq`：查询 San.js 常见问题与最佳实践
- `san-router-doc`：查询 San Router 文档
- `san-store-doc`：查询 San Store 文档
- `cosmic_token_check.sh`：调用脚本做 token 检查  
  脚本：`bash ../../core/scripts/cosmic_token_check.sh "<file1:line1,line2;file2:line3>"`
  - 使用单字符串输入；不带行号的文件条目会被忽略

## 依赖与预校验

- 统一 npm 源：`registry=http://registry.npm.baidu-int.com`
- 依赖映射：
  - `san-mcp` 相关工具（`san-doc`/`san-faq`/`san-router-doc`/`san-store-doc`）依赖 `@baidu/san-mcp`
  - `cosmic_token_check.sh` 依赖 `@baidu/cosmic-toolkit`
- 启动时必须先执行：
  - `bash ../../core/scripts/pre-install.sh`
- 说明：`pre-install.sh` 会先校验依赖，缺失时自动安装

## 什么时候调用

- 遇到可疑 San API / 生命周期：用 `san-doc` 或 `san-faq`
- 遇到路由问题：用 `san-router-doc`
- 遇到状态管理问题：用 `san-store-doc`
- 遇到样式硬编码 / token 使用问题：用 `cosmic_token_check.sh`（支持 `css/less/scss/sass/styl/san/vue`）

## cosmic_token_check.sh 输出（关键字段）

脚本返回 JSON（stdout）：

- `results[].file`：被检查文件
- `results[].platform`：`pc` 或 `mobile`
- `results[].lines`：该文件参与检查的行号集合（逗号分隔）
- `results[].issue_points[]`：工具识别的问题点（仅按传入的行号过滤）
  - `issue_points` 直接展示脚本返回内容

输入参数格式（字符串）：

- 规则：`文件路径:行号1,行号2;文件路径:行号3`
- 示例：`"./src/a.less:12,13;./src/b/index.san:45"`
- 不带行号的条目会被忽略（全部都不带行号时会报错）

## 评审落地规则（token）

- 只输出 **一条** `p0-use-cosmic-tokens` 问题（禁止按文件拆成多条）
- 该问题下按文件分块（`results[]` 顺序），每个文件块必须包含：
  - 位置：`results[i].file:results[i].lines`
  - 检测详情：展示 `results[i].issue_points`
