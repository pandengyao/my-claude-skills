---
name: experiment-code-cleanup
description: 通用实验代码清理技能，支持多种编程语言（C/C++、JS/TS、Vue、React、Python、Java等）。分析依赖关系，基于MDR规则评估清理安全性，移除实验相关代码同时保留默认行为。当用户提到清理实验、删除特性开关、清理白名单逻辑或提供实验ID/名称时调用。
---

# 实验代码清理技能

系统化地分析和移除代码库中的实验代码、特性开关和白名单逻辑，确保代码正确性和可维护性。

**支持的语言和框架**：C/C++、JavaScript、TypeScript、Vue、React、Python、Java 等主流编程语言。

## 使用场景

当用户请求以下操作时调用此技能：
- 清理或移除指定实验ID或名称的实验代码
- 删除不再需要的特性开关逻辑
- 移除白名单/黑名单控制逻辑
- 清除废弃的实验特性
- 通过移除A/B测试分支简化代码

用户请求示例：
- "清理实验 exp_new_checkout_flow"
- "移除 dark_mode 的特性开关"
- "删除 premium_users 的白名单逻辑"
- "帮我移除实验代码 exp_12345"
- "实验名称：close_rag_search, 项目目录:/path/to/project"

## 快速使用指南

只需提供以下信息即可自动完成清理：

**必需参数**：
- **实验ID/名称**: 要清理的实验标识符（如 `close_rag_search`, `exp_new_feature`）

**可选参数**：
- **项目根目录**: 默认使用当前工作目录
- **清理决策**: `keep_false`（默认）、`keep_true`、`remove_all`

**执行流程**：
1. 自动扫描代码库，识别所有实验引用
2. 分析实验配置值，确定清理策略
3. 移除实验条件检查，保留默认行为
4. 验证编译是否通过
5. 生成清理报告



## 工作流程

### 阶段 1: 依赖分析

执行依赖分析以了解实验引用的完整范围。

**步骤 1.1: 运行分析脚本**

执行分析脚本扫描实验引用：

```bash
~/py312/bin/python3 scripts/analyze_experiment_deps.py 实验ID --root 项目根目录 --output analysis_result.json
```

参数：
- `实验ID`: 要搜索的实验ID或白名单名称
- `项目根目录`: 项目根目录（默认：当前目录）
- `--output`: 可选的JSON输出文件路径

**C++ 项目依赖分析**：

由于分析脚本主要支持JS/TS/Python/Java，对于C/C++项目，使用 `grep_content` 工具直接搜索：

```
grep_content pattern="实验ID" path="项目根目录" output_mode="content" -n=true
```

**搜索范围**：
- 代码文件: `.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp`, `.hxx`
- Proto文件: `.proto`
- 配置文件: `.conf`

**C++ 项目引用模式**：
- 代码中配置访问: `conf->experiment_id()`, `config.experiment_id()`, `qa_conf->exp_name()` **【需修改】**
- 代码中条件判断: `if (conf->experiment_id())`, `if (config.experiment_id() > 0)` **【需修改】**
- proto字段定义: `optional uint32 experiment_id = 123;` **【可选删除】**
- 配置文件: `experiment_id: 0` **【可选删除】**
- 日志输出: `CTX_DEBUG_LOG(ctx, "experiment_id: %d", value)` **【可选修改】**

脚本识别的模式类型：

**通用模式**：
- 函数调用: `isExpEnabled('exp_id')`, `getExpValue('exp_name')`, `checkFeatureFlag()`
- 配置访问: `config.experiments.expId`, `expConfig['exp_name']`
- 注释标记: `@exp: exp_id`, `experiment: exp_name`, `// TODO: remove after exp`
- 字符串字面量: 直接引用实验ID的字符串

**JavaScript/TypeScript**：
- 环境变量: `process.env.EXP_ID`, `import.meta.env.EXP_ID`
- 全局变量: `window.__EXP_CONFIG__.expId`
- 条件渲染: `condition ? expBranch : defaultBranch`

**Vue**：
- 模板指令: `v-if="experiments.expId"`, `v-show="isExpEnabled"`
- 计算属性: `computed: { showNewFeature() {...} }`

**React**：
- 条件渲染: `{isExpEnabled && <NewComponent />}`
- Hooks: `useFeatureFlag('exp_id')`

**Python**：
- 环境变量: `os.environ.get('EXP_ID')`, `os.getenv('EXP_ID')`
- 配置访问: `config['experiments']['exp_id']`
- 装饰器: `@feature_flag('exp_id')`

**Java**：
- 配置访问: `config.getExperiments().getExpId()`
- 注解: `@FeatureFlag("exp_id")`
- 系统属性: `System.getProperty("exp.id")`
- 实验工具类：`expUtils.hitExp(object, ExpUtils.expid)`

**C/C++ 项目清理**：

**C/C++ 项目清理包括**：
1. **代码清理（必需）**: 移除 `.cpp/.h` 文件中的实验条件判断
2. **Proto清理（可选）**: 删除 `.proto` 文件中的字段定义
3. **Conf清理（可选）**: 删除 `.conf` 配置文件中的实验项

**默认策略**: `keep_false`（保留默认分支，移除实验分支）

**C/C++ 项目默认策略说明**：
- **默认策略**: `keep_false`（保留默认分支，移除实验分支）
- **理由**: 
  - C++ 项目中的实验通常为开关类型（0=关闭/默认，1=开启/实验）
  - 实验关闭时，配置值为 0，代码逻辑走默认分支
  - 清理时保留默认分支，移除实验条件检查，符合线上实际行为
- **适用场景**: 实验配置值为 0 或实验已下线

**步骤 1.2: 查看分析结果**

向用户展示分析结果，包括：
- 扫描的文件总数
- 受影响的文件数
- 发现的模式类型及其频率
- 详细的文件列表（包含行号和上下文）

在继续之前请用户确认分析结果是否完整准确。

### 阶段 2: 清理策略决策

基于MDR规则和可用信息确定合适的清理策略。

**步骤 2.1: 收集信息**

从多个来源收集信息以评估清理安全性（详见 `references/cleanup_rules.md` 中的MDR指南）：

1. **MCP平台检查**（如可用）：
   - 查询实验平台的实验状态
   - 检查实验是否标记为已结束/下线

2. **代码上下文分析**：
   - 检查注释中的废弃标记
   - 审查git历史中的删除意图
   - 确定配置是否仍在修改

3. **用户确认**：
   - 询问用户实验状态
   - 确认期望的清理方向（保留true/false分支）

**步骤 2.2: 分配信任等级**

基于收集的信息分配信任等级：
- **高**: MCP明确标记实验已结束/下线
- **中**: MCP不可用，但至少有2个支持证据（如：废弃标记 + 配置无近期变更）
- **低**: 仅代码侧推断，无外部证据

**步骤 2.3: 确定清理决策**

做出三种清理决策之一：
- **keep_false**: 保留默认/回退分支（实验已下线）- **默认策略**
- **keep_true**: 保留实验分支（实验已推全）
- **remove_all**: 完全移除控制逻辑（两个分支相同）

**默认策略**: 
- **通用默认**: 当不确定时，使用 `keep_false` 保留默认行为并移除实验逻辑
- **C/C++ 项目默认**: 直接使用 `keep_false` 策略
  - C++ 实验通常为开关类型（0=默认，1=实验）
  - 配置值为 0 表示实验关闭，保留默认分支
  - 无需额外确认，直接应用 `keep_false` 策略

**步骤 2.4: 评估风险等级**

评估修改风险：
- **高风险**: 影响核心业务逻辑、依赖众多、控制流复杂
  - 操作: 仅生成详细分析报告，需人工审查
- **中/低风险**: 影响范围有限、控制流清晰、影响隔离
  - 操作: 继续自动清理，记录变更

向用户展示清理策略，包括：
- 信任等级和支持证据
- 选定的决策（keep_true/keep_false/remove_all）
- 风险评估
- 预期影响范围

**C/C++ 项目特殊说明**：
- 默认使用 `keep_false` 策略，无需额外确认
- 直接根据配置值判断：0=保留默认分支，1=保留实验分支
- 展示策略后直接执行代码修改

在继续之前请求用户批准（C++项目如使用默认策略可省略确认步骤）。

### 阶段 3: 代码修改

遵循严格的修改约束执行清理。

**步骤 3.1: 应用清理规则**

遵循以下约束（详见 `references/cleanup_rules.md` 第5节）：

**禁止的操作**：
- 引入新条件或业务逻辑
- 修改功能语义
- 执行超出清理需求的结构重构
- 合并无关逻辑

**允许的操作**：
- 删除废弃的分支和配置
- 移除未引用的依赖
- 为逻辑收敛做最小结构调整

**步骤 3.2: 实施变更**

对每个受影响的文件：

1. 读取文件以理解上下文
2. 识别要移除的特定实验逻辑
3. 根据清理决策应用修改：

   **代码文件（.java, .js, .ts, .py, .cpp 等）**：
   - **keep_false**: 移除if检查和实验分支，保留默认逻辑
   - **keep_true**: 移除if检查和默认分支，保留实验逻辑
   - **remove_all**: 如果分支相同则移除整个控制块

   **配置文件（.yaml, .yml, .properties 等）**：
   - **keep_false**: 将配置值修改为 false/0，**保留配置项**
   - **keep_true**: 将配置值修改为 true/1，**保留配置项**
   - **remove_all**: 仅当配置项完全无用且无代码引用时，才删除配置项

4. 确保代码在语法和逻辑上保持有效
5. 保留代码格式和风格

**常见清理模式**：

**JavaScript/TypeScript 示例**：

示例1 - 简单if语句 (keep_false):
```javascript
// 之前
if (isExpEnabled('exp_new_feature')) {
  showNewUI();
} else {
  showOldUI();
}

// 之后
showOldUI();
```

示例2 - 三元运算符 (keep_false):
```javascript
// 之前
const component = expConfig['new_layout'] ? NewLayout : OldLayout;

// 之后
const component = OldLayout;
```

示例3 - 配置对象 (remove_all):
```javascript
// 之前
const config = {
  experiments: {
    exp_feature_a: true,
    exp_feature_b: false
  }
};

// 之后（清理 exp_feature_a）
const config = {
  experiments: {
    exp_feature_b: false
  }
};
```

**Vue 示例**：

示例4 - 模板条件渲染 (keep_false):
```vue
<!-- 之前 -->
<template>
  <div>
    <NewComponent v-if="experiments.new_ui" />
    <OldComponent v-else />
  </div>
</template>

<!-- 之后 -->
<template>
  <div>
    <OldComponent />
  </div>
</template>
```

**React 示例**：

示例5 - JSX条件渲染 (keep_false):
```jsx
// 之前
return (
  <div>
    {isExpEnabled('new_ui') ? <NewComponent /> : <OldComponent />}
  </div>
);

// 之后
return (
  <div>
    <OldComponent />
  </div>
);
```

**Python 示例**：

示例6 - if语句 (keep_false):
```python
# 之前
if os.getenv('EXP_NEW_ALGO') == 'true':
    result = new_algorithm(data)
else:
    result = old_algorithm(data)

# 之后
result = old_algorithm(data)
```

示例7 - 装饰器 (remove_all):
```python
# 之前
@feature_flag('exp_cache')
def process_data(data):
    return data

# 之后（移除装饰器）
def process_data(data):
    return data
```

**Java 示例**：

示例8 - if语句 (keep_false):
```java
// 之前
    if (ucAuthServiceProxy.userInGroup(userId, UcAuthGroupNameEnum.AGENT_CONFIG_PAGE_NEW)) {
        return oldService.process();
    } else {
        return newService.process();  
    }

// 之后
return oldService.process();
```

示例9 - 注解 (remove_all):
```java
// 之前
@FeatureFlag("exp_optimization")
public class OptimizedProcessor {
    // ...
}

// 之后（移除注解）
public class OptimizedProcessor {
    // ...
}
```

**C/C++ 示例**（默认使用 keep_false 策略，可选择删除 proto/conf 配置）：

**默认策略**: `keep_false`（保留默认分支，移除实验分支）

示例10 - 简单if语句 (keep_false):
```cpp
// 之前
bool disable_search = false;
if (qa_conf->close_rag_search()) {
    disable_search = true;
}

// 之后（直接移除if条件）
bool disable_search = false;
```

示例11 - if-else分支 (keep_false):
```cpp
// 之前
if (qa_conf->close_rag_search()) {
    auto* prompt_info = dict::NewDictInfo::seek(key);
    if (prompt_info) {
        prompt = prompt_info->prompt_template();
    }
} else {
    auto* prompt_info = dict::OldDictInfo::seek(key);
    if (prompt_info) {
        prompt = prompt_info->prompt_template();
    }
}

// 之后（保留else分支，移除if条件）
{
    auto* prompt_info = dict::OldDictInfo::seek(key);
    if (prompt_info) {
        prompt = prompt_info->prompt_template();
    }
}
```

示例12 - 大型if-else控制块 (keep_false):
```cpp
// 之前
if (qa_conf->close_rag_search()) {
    // 实验分支：禁用搜索的逻辑（数十行代码）
    if (condition_a) {
        process_a();
    } else if (condition_b) {
        process_b();
    }
} else {
    // 默认分支：启用搜索的逻辑
    if (condition_a) {
        process_a_default();
    } else if (condition_b) {
        process_b_default();
    }
}

// 之后（移除if条件，保留else内容）
{
    if (condition_a) {
        process_a_default();
    } else if (condition_b) {
        process_b_default();
    }
}
```

**YAML 配置文件清理策略说明**：

**重要原则**：对于 YAML 配置文件，清理策略的行为与代码文件不同：
- **keep_false**: 将配置值修改为 false/0，**不要删除配置项**
- **keep_true**: 将配置值修改为 true/1，**不要删除配置项**
- **remove_all**: 仅当配置项已完全无用且无其他代码引用时，才删除整个配置项

**YAML 示例**：

示例13 - keep_false (修改值为0):
```yaml
# 之前
exp_flag: 1

# 之后 - 修改为0，保留配置项
exp_flag: 0
```

示例14 - keep_true (修改值为1):
```yaml
# 之前
exp_flag: 0

# 之后 - 修改为1，保留配置项
exp_flag: 1
```

示例15 - remove_all (删除配置项):
```yaml
# 之前
exp_flag: 1
other_config: enabled

# 之后 - 删除实验配置项，保留其他配置
other_config: enabled
```

**注意**：当清理 Java 项目的 YAML 配置时，keep_true 策略必须将配置值修改为 true/1，不能删除配置项。这是因为 Java 项目通常依赖配置文件中的配置项存在，删除会导致运行时错误。

#### C++ Proto 和 Conf 配置删除

**Proto 文件字段删除**：

直接删除字段

```proto
// 直接删除
optional uint32 trade_material_use_llm = 27;
```

**Conf 配置文件删除**：

```conf
# 之前
use_trade_knowledge:0
trade_material_use_llm:0

# 之后（直接删除实验配置行）
trade_material_use_llm:0
```

**注意**: 删除 proto/conf 配置后需要重新编译项目，会自动重新生成 `.yacl.cc` 和 `.yacl.h` 文件。

**步骤 3.3: 处理相关清理**

移除实验逻辑后，根据语言特性进行相应清理：

**通用清理**：
- 移除未使用的import/include语句
- 删除未引用的工具函数
- 清理实验特定的配置条目
- 更新相关注释和文档

**语言特定清理**：
- **JavaScript/TypeScript**: 移除未使用的import、删除空的对象属性
- **Vue**: 清理未使用的组件注册、移除空的computed/methods
- **React**: 移除未使用的Hooks、清理空的useEffect
- **Python**: 移除未使用的import、清理空的装饰器
- **Java**: 移除未使用的import、清理空的注解、删除未引用的类
- **C/C++**:
  - 移除代码中的实验条件判断: `if (conf->exp_id()) { ... }`
  - 可选择删除 `.proto` 文件中的字段定义
  - 可选择删除 `.conf` 配置文件中的实验配置项
  - 移除相关的日志输出语句（可选）

### 阶段 4: 验证和报告

**步骤 4.1: 编译前检查**

在执行编译验证前，检查修改后的代码是否存在常见问题：

**编译前检查清单**：
1. 检查 Unicode 转义问题（`\u003e` → `>`，`\u003c` → `<` 等）
2. 验证关键操作符（`->`，`>=`，`<=` 等）是否正确
3. 确认括号匹配（`{}`，`()`，`[]`）
4. 检查分号完整性

**常见问题示例**：
```cpp
// 错误：Unicode 转义
if (a \u003e b)  // 应为 if (a > b)

// 错误：操作符被破坏
conf-\u003eexp_id()  // 应为 conf->exp_id()
```

**检查方法**：
```bash
# 搜索可能的 Unicode 转义问题
grep -r "\\\\u00" 修改的文件
```

**步骤 4.2: 生成清理报告**

创建包含以下内容的综合报告：

1. **清理摘要**：
   - 清理的实验ID/名称
   - 信任等级和信息来源
   - 清理决策和理由
   - 修改的文件数量

2. **修改详情**：
   - 按文件列出的变更（含行号）
   - 关键变更的前后代码片段
   - 移除的依赖和import

3. **风险评估**：
   - 识别的风险和不确定性
   - 推荐的验证步骤
   - 建议的测试方法

**步骤 4.3: 推荐验证步骤**

建议适当的验证步骤（根据项目类型）：

**通用验证**：
- 运行现有测试套件
- 对受影响功能进行手动测试
- 与领域专家审查变更（高风险修改）
- 先部署到预发布环境

**语言特定验证**：
- **JavaScript/TypeScript**: 运行 `npm test`, `jest`, 类型检查 `tsc --noEmit`
- **Vue**: 运行 `npm run test:unit`, 检查组件渲染
- **React**: 运行 `npm test`, 检查React组件测试
- **Python**: 运行 `pytest`, `unittest`, 类型检查 `mypy`
- **Java**: 运行 `mvn test` 或 `gradle test`, 编译检查
- **C/C++ (Baidu内部)**:
  1. 登录bcloud: `bcloud login-icode -u ${username} -p ${password}`
  2. 编译项目: `cd 项目目录 && bcloud build --update &> build.log &`
  3. 检查结果: `tail -100 build.log` 查看编译是否成功
- **C/C++ (通用)**: 运行 `make` 或 `cmake --build`, 编译检查

## 使用绑定资源

### 脚本

**`scripts/analyze_experiment_deps.py`**

用于分析实验代码依赖的Python脚本。支持多种编程语言的模式识别。

用法：
```bash
~/py312/bin/python3 scripts/analyze_experiment_deps.py 实验ID --root 项目根目录 --output result.json
```

**支持的文件类型**：
- JavaScript/TypeScript: `.js`, `.ts`, `.jsx`, `.tsx`
- Vue: `.vue`
- Python: `.py`
- Java: `.java`
- C/C++ 代码: `.cpp`, `.cc`, `.cxx`, `.c`, `.h`, `.hpp`, `.hxx`
- C/C++ Proto: `.proto` (C++项目可修改)
- C/C++ 配置: `.conf` (C++项目可修改)
- 其他配置文件: `.json`, `.yaml`, `.yml`, `.xml`, `.properties`, `.cfg` (仅用于搜索引用)

**重要说明**: 对于C/C++项目：
- **修改代码文件**（`.cpp`, `.cc`, `.h` 等）
- **可选修改** `.proto` protobuf定义文件
- **可选修改** `.conf` 配置文件
- 这些配置文件用于分析实验的引用情况和配置值

输出格式：包含所有引用的JSON文件（含模式类型、文件路径、行号和代码片段）。

### 参考文档

**`references/cleanup_rules.md`**

定义MDR（模型/决策/规则）指南，包括：
- 清理操作的范围
- 信息信任等级
- 清理策略的决策模型
- 代码修改约束
- 风险评估标准

在做清理决策或评估修改安全性时加载此文件。

## 重要注意事项

### 安全第一

- 在做出变更前始终分析依赖关系
- 对中/高风险修改要求明确的用户批准
- 不确定时保留默认行为
- 记录所有假设和不确定性

### 渐进式方法

- 从低风险文件开始
- 复杂情况下一次修改一个文件
- 在继续下一个文件前验证变更

### 沟通

- 清楚地解释清理策略和理由
- 突出显示风险和不确定性
- 为重要变更提供前后对比示例

### 限制

此技能不处理：
- 业务逻辑正确性验证
- 生产影响评估
- 产品级决策
- 性能优化
- 架构重构

## 总结

使用此技能通过分析依赖关系、基于MDR指南做出安全决策、移除过时逻辑同时保留代码正确性，系统化地清理实验代码。始终优先考虑安全性，对非平凡变更寻求用户确认，并提供所有修改的全面文档。
