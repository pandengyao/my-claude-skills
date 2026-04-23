---
name: scan-log-analyzer
description: 分析 Comate 扫描功能的日志，诊断初始化、配置读取、任务触发和执行状态问题。
allowed-tools:
  - shell
---

# scan-log-analyzer

分析 Comate 扫描功能的日志，诊断初始化、配置读取、任务触发和执行状态问题。

当用户请求分析扫描日志、查看扫描状态、诊断扫描问题时，使用此 skill。

## 触发词

- 日志分析
- 扫描日志
- scan log
- 分析日志
- 查看扫描状态

## 用法

### 方式 1: 直接运行脚本（推荐）

```bash
# 分析今天的日志
~/.claude/skills/scan-log-analyzer/scripts/scan-log.sh

# 分析指定日期的日志
~/.claude/skills/scan-log-analyzer/scripts/scan-log.sh 2026-03-02

# 列出可用的日志文件
~/.claude/skills/scan-log-analyzer/scripts/scan-log.sh list

# 显示帮助信息
~/.claude/skills/scan-log-analyzer/scripts/scan-log.sh help
```

脚本会自动读取 `~/.comate-engine/log/kernel-{date}.log` 并生成分析报告。

### 方式 2: 使用此 skill

提供扫描相关的日志内容，skill 将分析日志内容。

**当用户提供日志时：**
1. 首先建议运行脚本进行自动分析
2. 如果用户只想分析特定日志片段，则按以下步骤进行手工分析：
   1. 检查各组件初始化状态
   2. 验证配置加载情况
   3. 分析任务触发流程
   4. 检查扫描执行状态
   5. 识别异常和错误
   6. 提供问题诊断和修改建议

## 分析执行规则

当收到日志输入时，按以下步骤分析：

### 步骤 1: 提取和分类日志
按组件分类日志：
- ScanTriggerManager 相关日志
- ScanScheduler 相关日志
- ConfigManager 相关日志
- StateManager 相关日志
- IcrExecutor 相关日志
- IcrInstaller 相关日志
- 通用错误日志

### 步骤 2: 状态检查清单

#### 2.1 初始化状态
<!-- - [ ] `[ScanTriggerManager] Initialized` 存在? -->
- [ ] `[ScanScheduler] Initialized` 存在?
- [ ] `[IcrExecutor] Initialized` 存在且包含有效的 icrBinaryPath?
- [ ] 没有初始化相关的 error 日志?

#### 2.2 配置加载状态
- [ ] `[ConfigManager] Remote config loaded successfully` 存在且 enabled=true?
- [ ] 没有 `[ConfigManager] No userId available`?
- [ ] 没有 `[ConfigManager] Failed to load remote config`?
- [ ] 没有 `[ConfigManager] User not in gray release`?

#### 2.3 任务触发状态
- [ ] `[ScanTriggerManager] Scan request result` 存在?
- [ ] `[ScanScheduler] Generated X plans` 且 X > 0?
- [ ] 没有 `[ScanScheduler] Duplicate event`?
<!-- - [ ] `[ScanTriggerManager] File save watcher setup completed` 存在? -->

#### 2.4 执行状态
- [ ] `[IcrExecutor] Executing plan` 存在?
- [ ] `[IcrExecutor] ICR process spawned successfully` 存在?
- [ ] `[IcrExecutor] ICR task completed` 且 status='success'?
- [ ] `[StateManager] Scan completed` 存在?
<!-- - [ ] `[ScanTriggerManager] Scan result received` 存在? -->

### 步骤 3: 常见问题诊断

如果发现问题，参考以下诊断表：

| 问题症状 | 可能原因 | 相关文件 | 修复建议 |
|---------|---------|---------|---------|
| `[ConfigManager] No userId available` | kernel.config.username 为空 | ConfigManager.ts:37 | 检查用户登录状态 |
| `[ConfigManager] Failed to load remote config` | 网络问题或接口异常 | ConfigManager.ts:45-50 | 检查网络和接口地址 |
| `[ConfigManager] User not in gray release` | 用户未在灰度列表 | ConfigManager.ts:65-70 | 联系后台配置灰度 |
| `[IcrExecutor] ICR binary not found` | ICR 未安装或路径错误 | IcrInstaller.ts:26-35 | 检查 ICODE_CLI_INSTALL_DIR 或运行安装 |
<!-- | `[ScanTriggerManager] file-save trigger is disabled` | 触发器配置未启用 | ScanTriggerManager.ts:157 | 检查远端配置中的 triggers.file-save.enabled | -->
| `[ScanScheduler] Duplicate event` | 事件 ID 重复 | StateManager.ts:120-132 | 检查事件生成逻辑 |
| `[IcrExecutor] ICR task failed` | ICR 执行错误 | IcrExecutor.ts:397-402 | 检查 ICR 输入和 stderr |
| `Plan execution failed` | 计划执行异常 | ScanScheduler/index.ts:181-184 | 检查错误堆栈 |
<!-- | `[ScanTriggerManager] Failed to setup file save watcher` | 文件监听器设置失败 | ScanTriggerManager.ts:153-189 | 检查 workspace 配置 | -->
| `[IcrExecutor] TaskInput file disappeared before spawn` | 临时文件被删除 | IcrExecutor.ts:456-458 | 检查临时目录权限和清理逻辑 |

### 步骤 4: 输出分析报告

按以下格式输出报告：

```
## 扫描日志分析报告

### 执行状态摘要
- 初始化状态: ✅/❌ [详情]
- 配置加载状态: ✅/❌ [详情]
- 任务触发状态: ✅/❌ [详情]
- 执行状态: ✅/❌ [详情]

### 详细分析

#### 1. 初始化检查
- ScanTriggerManager: ✅/❌
- ScanScheduler: ✅/❌
- IcrExecutor: ✅/❌

#### 2. 配置检查
- 用户ID: ✅/❌
- 远端配置: ✅/❌
- 灰度状态: ✅/❌

#### 3. 任务触发检查
- 触发器设置: ✅/❌
- 计划生成: ✅/❌ (生成数量: X)
- 事件去重: ✅/❌

#### 4. 执行检查
- ICR 进程: ✅/❌
- 任务完成: ✅/❌
- 结果接收: ✅/❌

### 发现的问题
[列出所有发现的问题]

### 修改建议
[如果需要代码修改，提供具体的修改建议]
```

### 步骤 5: 代码修改建议格式

如果需要修改代码，使用以下格式：

```
#### 问题: [问题描述]
- **位置**: [文件路径]:[行号]
- **原因**: [具体原因]
- **建议**: [修改建议]

**修改前:**
```typescript
// 原始代码
```

**修改后:**
```typescript
// 修改后的代码
```
```

## 关键代码文件

- `packages/kernel/src/service/ScanScheduler/index.ts` - 主调度器
- `packages/kernel/src/service/ScanScheduler/ConfigManager.ts` - 配置管理
- `packages/kernel/src/service/ScanScheduler/StateManager.ts` - 状态管理
- `packages/kernel/src/service/ScanScheduler/IcrExecutor.ts` - ICR 执行器
- `packages/kernel/src/service/ScanScheduler/IcrInstaller.ts` - ICR 安装器
- `packages/vscode/src/services/ScanTriggerManager.ts` - 触发管理器

## 示例

### 示例日志输入:
```
[ScanTriggerManager] Initialized
[IcrExecutor] ICR binary not found, executor disabled
[ConfigManager] Remote config loaded successfully {"enabled":true,"taskCount":2}
[ScanScheduler] Initialized
```

### 示例输出:
```
## 扫描日志分析报告

### 执行状态摘要
- 初始化状态: ⚠️ 部分失败
- 配置加载状态: ✅
- 任务触发状态: ❓ (未检测到触发日志)
- 执行状态: ❌

### 详细分析
...

### 发现的问题
1. ICR 二进制未找到，执行器被禁用
2. 没有检测到任务触发日志

### 修改建议
...
```
