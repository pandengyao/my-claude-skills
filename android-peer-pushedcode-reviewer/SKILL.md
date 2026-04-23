---
name: android-peer-pushedcode-reviewer
description: 对 Android 项目进行代码审查（Code Review）。当用户提供 Gerrit Change 的 PatchSet 远端 ref 引用、提到 code review、评审代码、审查提交、review 某个 change/patchset，或粘贴了类似 ssh://xxx@icode.baidu.com 的 Gerrit 链接时，都应使用此技能。即使用户只是简单说"帮我 review 一下"并附上了 ref 引用，也要触发。
---

# Android Code Review

## 为什么这样做 Review

代码审查的价值在于发现作者视角下的盲区。仅看 diff 片段很容易遗漏上下文中的逻辑问题——比如一个看似正确的空判断，在调用链上游其实永远不为空，而真正危险的路径被忽略了。因此这套流程的核心思路是：**先在隔离环境中拿到完整代码，构建调用链和数据流模型，然后再做判断**。

## 核心原则

1. **基于完整代码做分析，而非 diff 片段** —— diff 只展示变更行，缺少调用方、数据来源、生命周期等上下文，仅凭片段分析容易产生误判或漏判。
2. **先读相关文件，再给结论** —— 变更代码可能依赖父类实现、接口契约、上游数据流等，不理解这些就下结论是不负责的。
3. **在 worktree 中工作** —— 使用 git worktree 隔离 review 环境，避免影响用户当前工作区的代码状态。
4. **先建模，后输出** —— 在脑中（或工作过程中）完成调用链、数据流、线程模型的梳理后，再输出 review 结果，确保结论有据可查。

## 流程

### 第 1 步：解析 ref 引用，定位本地项目

从用户提供的 Gerrit PatchSet ref 引用中提取项目路径，然后查找本地映射。

**解析示例：**
```
输入: ssh://zhangsan@icode.baidu.com:8235/baidu/netdisk/android refs/changes/00/119509400/5

提取云端项目路径: baidu/netdisk/android
提取 Change ID: 119509400（从 refs/changes/XX/CHANGE_ID/PATCHSET 中取）
```

**查找本地路径：**
读取 [project_localpath_mapping.md](references/project_localpath_mapping.md) 找到对应的本地绝对路径，然后 cd 进去。

**异常处理：**
- 映射不存在 → 按 project_localpath_mapping.md 中的缺省策略询问用户
- 本地路径不存在 → 提示用户路径失效，要求提供新路径，同时移除失效映射
- 不是 Android 工程（目录下没有 `build.gradle` / `build.gradle.kts` / `settings.gradle`）→ 告知用户并停止

### 第 2 步：搭建 review 环境（fetch + 建分支 + 创建 worktree）

使用 [review_setup.sh](scripts/review_setup.sh) 脚本一键完成 fetch、创建 review 分支、创建 worktree 三个操作：

```bash
bash <skill-path>/scripts/review_setup.sh <完整ssh地址> <refs/changes/...>
```

**示例：**
```bash
bash <skill-path>/scripts/review_setup.sh \
  ssh://zhangsan@icode.baidu.com:8235/baidu/netdisk/android \
  refs/changes/00/119509400/5
```

脚本会自动处理以下异常情况：
- 分支已存在 → 自动删除旧分支再重建
- worktree 目录已存在 → 自动清理再创建
- fetch 失败 → 脚本报错退出，提示用户检查网络或 SSH 权限

脚本执行完成后会输出 worktree 的绝对路径。

### 第 3 步：在 worktree 中执行代码审查

cd 进入第 2 步创建的 worktree 目录，在该目录内完成所有代码阅读与分析。

**审查步骤：**

1. **识别变更范围** —— 通过 `git diff HEAD~1` 查看本次变更涉及的所有文件和改动
2. **理解变更意图** —— 从变更内容判断这是新功能、Bug 修复、重构还是其他类型，不同类型的关注点不同
3. **阅读变更文件完整代码** —— 不要只看 diff 行，要读完整文件以理解上下文
4. **追溯调用链与数据流** —— 阅读调用方、被调用方、父类、接口、字段定义等相关文件，在 worktree 目录中查找
5. **分析线程模型与生命周期** —— 尤其关注协程作用域、Activity/Fragment 生命周期、回调时序
6. **形成完整判断后输出结论**

### 第 4 步：清理 worktree

Review 完成后，使用 [review_cleanup.sh](scripts/review_cleanup.sh) 脚本一键清理环境：

```bash
cd <原项目路径>
bash <skill-path>/scripts/review_cleanup.sh <CHANGE_ID>
```

**示例：**
```bash
cd /Users/zhangsan/Desktop/projects/baidu/netdisk/android
bash <skill-path>/scripts/review_cleanup.sh 119509400
```

脚本会自动移除 worktree 目录并删除 review 分支，如果已不存在则跳过。

---

## Review 维度

### 1. 逻辑与边界
- 空值处理是否完备（特别是 Java/Kotlin 互调场景）
- 集合操作的边界情况（空集合、单元素、并发修改）
- 条件分支是否覆盖所有情况
- 数值计算的溢出、除零风险

### 2. 并发与生命周期
- 协程的 scope 是否合理（应优先使用 viewModelScope / lifecycleScope）
- Activity/Fragment 销毁后是否有回调泄漏
- 多线程访问共享状态是否有同步保护
- Handler/Timer 等异步任务在生命周期结束时是否取消

### 3. 结构与组织
- 职责是否单一清晰
- 是否存在过度耦合
- 变更是否影响了不相关的模块

### 4. 可维护性
- 命名是否清晰表达意图
- 是否有不必要的复杂度
- 魔法数字 / 硬编码字符串

### 5. Kotlin 编码规范
参阅 [Kotlin编码规范.md](references/Kotlin编码规范.md) 获取完整指南，重点关注：
- 禁止使用 `lateinit`
- 禁止使用 `!!`
- 不被外部 module 使用的函数或类要使用 `internal` 修饰

### 6. Jetpack Compose（如变更涉及 Compose 代码）
- **状态管理**：ViewModel/State 是否只在 Route 层持有，不向下传递；Composable 是否尽量无状态
- **Modifier 使用**：多个 Composable 不能共用一个 Modifier；自定义公共组件是否暴露 Modifier 参数
- **性能**：惰性列表是否设置了 key 和 contentType；是否使用了不稳定的集合类型
- **点击事件**：是否使用了无点击阴影的 `clickable`（indication = null）
- **函数规范**：参数排序是否正确（强制参数在前，Modifier 在有默认值的参数第一位）；显示界面的 Composable 不应有返回值

### 7. 安全性
- 是否存在硬编码的密钥、token 或敏感信息
- 外部输入（Intent、URL、用户输入）是否做了校验
- 文件操作是否有路径穿越风险

---

## 问题等级

| 等级 | 含义 | 示例 |
|------|------|------|
| p0 | Crash / ANR / 严重数据错误 | 空指针崩溃、死锁导致 ANR、数据写入错误覆盖用户数据 |
| p1 | 逻辑错误 / 边界问题 / 状态错误 | 条件判断遗漏、竞态条件、生命周期泄漏 |
| p2 | 规范 / 可读性 / 结构问题 | 命名不规范、代码冗余、缺少必要注释 |

输出时按严重程度排序：p0 > p1 > p2。这个顺序很重要——review 的读者最先关心的是会不会崩溃（p0），其次是逻辑对不对（p1），最后才是规范问题（p2）。输出时先列完所有 p0，再列所有 p1，最后列 p2。

---

## 输出格式

### 有问题时

先输出变更概述，再按等级**严格从高到低分组**列出问题，最后给出总结。

```
## 变更概述
简要描述这个 change 在做什么（1-2 句话）

## 发现的问题

### p0（Crash / ANR / 严重数据错误）

问题1: 问题描述 (p0)
文件位置：相对文件路径#开始行号-结束行号
原因：为什么这是一个问题，结合调用链/数据流说明
建议修复：具体的修复方案

### p1（逻辑错误 / 边界问题 / 状态错误）

问题2: 问题描述 (p1)
文件位置：相对文件路径#开始行号-结束行号
原因：为什么这是一个问题
建议修复：具体的修复方案

### p2（规范 / 可读性 / 结构问题）

问题3: 问题描述 (p2)
文件位置：相对文件路径#开始行号-结束行号
原因：为什么这是一个问题
建议修复：具体的修复方案

## 总结
- 共发现 X 个问题（p0: N 个, p1: N 个, p2: N 个）
- 整体评价（一句话概括代码质量和主要风险）
```

如果某个等级没有问题，直接跳过该分组，不要输出空的分组标题。

### 无问题时

```
## 变更概述
简要描述这个 change 在做什么

## Review 结论
本次变更未发现明显问题。代码逻辑清晰，边界处理完备。
（可选：虽然没有问题，但有一些可以考虑优化的点：...）
```

---

## 编码规范参考
- **Kotlin 编码规范**：如果有 Kotlin 代码，参阅 [Kotlin编码规范.md](references/Kotlin编码规范.md)
- **Compose 开发规范**：如果有 Compose 代码，参照上方 Review 维度第 6 项中的 Compose 规范要点
