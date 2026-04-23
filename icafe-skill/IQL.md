#### IQL 规则说明

**基本运算符：**

| 参数 | 含义 |
|------|------|
| AND | 且 |
| OR | 或 |
| >, <, =, >=, <=, != | 大于、小于、等于(是)、大于等于、小于等于、不等于(不是)，后面只能跟一个参数 |
| in, not in | 包含多个，也可以跟 () 一起使用，in 空括号例：in ()，不包含 |
| is empty, is not empty | 为空、不为空，is 跟 empty 一起使用 |
| ~, !~ | 包含的意思，常用于文本、关键词、标题的筛选，不包含 |
| - | 减，不支持 "+" |
| () | 可以将筛选条件括起来当做一个整体 |
| "" | 字段值支持引号使用，也可以不加 |

**按字段类型分类：**

| 字段类型 | 支持的参数 | 说明 | 示例 |
|---------|-----------|------|------|
| 日期 / 时间 | <, >, =, is empty, is not empty | 不支持 >= <=；时间是点逻辑 | 创建时间 > "2023-12-01 06:00:00" AND 创建时间 < "2023-12-19 00:00:00" |
| 人员字段 | =, !=, in(), not in(), is empty, is not empty | | 负责人 = v_liuxiang, 创建人 = shijiazheng |
| 类型 | =, !=, in(), not in(), is empty, is not empty | | 类型 in (Bug, Epic, Story) |
| 流程状态 | <, <=, =, >, >=, !=, in(), not in(), is empty, is not empty | 大小比较基于状态顺序 | 流程状态 in (新建, 开发中, 待开发, 进行中) |
| 所属计划 | =, !=, in(), not in(), is empty, is not empty | 需要完整路径；也可勾选父计划并包含子计划 | 所属计划 in (测试, 测试/测试1, 测试/测试1/测试3) |
| 关键字 | ~ | 只支持包含；不包含请用标题字段 | 关键字 ~ 测试 AND 关键字 ~ "测试" |
| 标题 | ~, !~, is empty, is not empty | | 标题 ~ 测试 |
| 数字类型 | <, >, =, is empty, is not empty | | 数字字段 > 1 |
| 单选 / 多选 / 单选框 / 复选框 | =, !=, in(), not in(), is empty, is not empty | | 单选框 in (是, 否) |
| 树类型 / TAG | =, !=, in(), not in(), is empty, is not empty | | 树字段 is empty |
| 单行文本 / 多行文本 | ~, !~, is empty, is not empty | | 多行文本 !~ 测试 |
| URL 类型 | ~, !~, =, is empty, is not empty | | URL = "www.baidu.com" |
| Label 标签 | =, !=, in(), not in(), is empty, is not empty | | Label = aaa |

**常用 IQL 示例：**

| 查询需求 | IQL 表达式 |
|----------|------------|
| 查询 Bug 类型卡片 | `类型 = Bug` |
| 查询当前用户负责的卡片 | `负责人 = currentUser` |
| 查询指定用户创建的卡片 | `创建人 = shijiazheng` |
| 查询指定用户创建且在指定日期之后的卡片 | `创建人 = shijiazheng AND 创建时间 > "2026-02-01"` |
| 查询新建状态的卡片 | `状态 = 新建` |
| 查询 Bug 且负责人是当前用户的卡片 | `类型 = Bug AND 负责人 = currentUser` |
| 查询创建时间在指定日期之后的卡片 | `创建时间 > "2025-01-01"` |
| 查询多种类型的卡片 | `类型 in (Bug, Epic, Story)` |
| 查询标题包含关键词的卡片 | `标题 ~ 测试` |
| 查询负责人在指定列表中的卡片 | `负责人 in (user1, user2, user3)` |
| 查询流程状态在指定范围的卡片 | `流程状态 <= 开发中` |