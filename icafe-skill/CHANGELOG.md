# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.3] - 2026-04-15

### Added
- `scripts/query_card.py` 新增 `--raw` / `-r` 参数：以 JSON 格式输出所有原始字段（包含 API 返回的完整数据）
  - 支持单个卡片查询和列表查询模式
- `query_card.py` 关键字段过滤新增 `车型` 模式

### Changed
- `SKILL.md` 更新 `--related` 参数说明，明确为 `<空间-关联卡片ID>`

## [0.4.2] - 2026-04-02

### Added
- `update_card()` 新增参数支持：
  - `operator`: 修改人邮箱前缀，用于校验卡片权限
  - `is_check_status`: 是否进行流程状态可达检查
  - `rel_project`: 关联项目编号
  - `rel_project_operation`: 关联项目操作类型（add/delete）
- `scripts/update_card.py` 命令行工具新增对应参数：
  - `--operator`: 指定修改人
  - `--no-check-status`: 禁用流程状态可达检查
  - `--rel-project` 和 `--rel-project-operation`: 关联项目操作

## [0.4.1] - 2026-03-20

### Changed
- 增强 `plan_transition.py` 字段确认逻辑
  - 新增 `additional_warnings` 收集状态检测失败时的额外警告信息
  - 新增 `confirmed_fields` 跟踪已确认的字段值，确保命令字段值与确认列表一致
  - 改进指令结构，简化 `_instruction` 字段，明确指导用户确认流程
  - 字段详情新增 `options` 字段，展示字段可选值
  - 优化关闭卡片时的评论生成逻辑，根据 Bug分析结论 智能推断评论内容

### Added
- 字段详情中新增 `options` 字段，用于展示字段的预定义选项列表

## [0.4.0] - 2026-03-19

### Added
- 计划操作功能：支持查询、创建和更新计划
- 新增 `icafe_skill.plan` 模块
- 新增计划操作命令行工具 `scripts/plan.py`
  - 列出空间内所有计划
  - 查询单个计划（按名称）
  - 创建新计划（支持置顶和父计划）
  - 更新计划时间范围
  - 获取计划及里程碑信息
- 导出 `get_plan`, `create_plan`, `update_plan_date`, `get_plans_with_milestones` 函数

### Changed
- SKILL.md 文档添加计划管理工作流

## [0.3.1] - 2026-03-10

### Added
- `query_card.py` 脚本新增 `--fields` 参数：显示卡片自定义字段
  - 显示 Bug 关键字段（Bug问题原因、Bug分析结论、Bug修复方案等）
  - JSON 格式输出也包含 custom_fields 数据
- 更新 SKILL.md 帮助文档，添加 `--fields` 参数使用示例

### Fixed
- 修复 `query_card.py` 无法显示自定义字段的问题
  - 自定义字段存储在 `card.extra_fields['properties']` 中，但原代码未输出

## [0.3.0] - 2026-03-09

### Added
- 扩展卡片查询能力，支持排序、关联卡片、子卡片等高级功能
  - `list_cards` 新增 `show_associations` 参数：显示关联卡片信息
  - `list_cards` 新增 `is_desc` 参数：倒序排序
  - `list_cards` 新增 `order` 参数：排序字段（支持自定义字段）
  - `list_cards` 新增 `show_children` 参数：显示子卡片信息
  - `list_cards` 新增 `show_okr` 参数：显示关联 OKR 信息
  - `list_cards` 新增 `show_accumulate` 参数：显示周实际工时填报明细
- `query_card.py` 脚本新增列表查询模式（`--list`）
  - 支持批量查询卡片列表
  - 支持排序、详情、关联卡片、子卡片等参数
  - 新增 `print_cards_list` 函数打印卡片列表
- `batch_operations.py` 脚本新增排序参数（`--order`）
  - 支持 `batch_query` 函数排序
  - 支持 `status_summary` 函数排序

### Changed
- **破坏性变更**：`list_cards` 的 `max_records` 参数类型从 `int` 改为 `str`，以符合 iCafe API 规范
- **破坏性变更**：`list_cards` 的 `show_detail` 参数类型从 `bool` 改为 `str`
- `list_cards` 添加 `max_records` 值验证（最大值 100）
- 更新 `docs/API.md`，记录破坏性变更和新增参数说明
- 更新 `README.md`，添加新参数的使用示例
- 移除 `batch_operations.py` 中的 Emoji 字符，改用文字标签

### Fixed
- 修复 `get_plans` space_id 命名不一致问题
- 排除集成测试脚本，避免测试污染

## [0.2.5] - 2026-03-09

### Added
- 扩展卡片创建能力，支持父卡片关联、跨空间父卡片、卡片关联
  - `Issue` 数据类新增 `parent` 字段：支持父卡片序号引用
  - `Issue` 数据类新增 `parent_space_prefix_code` 字段：支持跨空间父卡片
  - `Issue` 数据类新增 `rel_issue_space_pre_seq` 字段：支持卡片关联（批量）
- 新增卡片关联功能（update_card）
  - `update_card` 函数新增 `rel_issue` 和 `rel_issue_operation` 参数
  - `preview_update` 函数支持预览关联卡片操作
  - 支持添加和删除关联卡片（`--rel-operation add/delete`）
- 新增单元测试 `tests/test_issue_models.py`（6 个测试用例）
  - 测试父卡片字段功能
  - 测试跨空间父卡片功能
  - 测试关联卡片功能
  - 测试所有扩展字段组合
  - 测试向后兼容性
  - 测试直接 dataclass 实例化
- 新增集成测试 `tests/test_extended_create.py`（4 个测试函数）
  - 测试父卡片创建（使用真实空间卡片）
  - 测试跨空间父卡片创建
  - 测试关联卡片创建
  - 测试批量创建（各种字段组合）
- 更新 `tests/test_all_features.py`，集成扩展创建功能测试
- 更新 `README.md`，添加扩展创建功能使用示例
  - 创建带父卡片的卡片示例
  - 创建跨空间父卡片的子卡片示例
  - 创建带关联卡片的卡片示例
- 更新 `SKILL.md`，添加 Issue 扩展字段参数说明和创建示例
  - 参数表格：parent、parent_space_prefix_code、rel_issue_space_pre_seq
  - 4 个创建示例（基础、带父卡片、跨空间、带关联）
  - 新增关联卡片命令示例（添加/删除关联）
- 更新 `docs/Skill_Guide.md` 版本更新日志

### Changed
- 更新 `icafe_skill/__init__.py` 版本号：0.2.4 → 0.2.5
- 更新 `setup.py` 版本号：0.2.4 → 0.2.5
- 优化 `update_card` 验证逻辑：允许空的 `fields` 字典，仅进行关联操作时无需其他字段

## [0.2.4] - 2026-03-03

### Added
- 完善 references 文档，增加更多实用场景和最佳实践
  - `general-guide.md`: 新增核心工作流、批量操作、常见流转场景说明
  - `general-guide.md`: 新增字段管理、最佳实践说明
  - `transition-to-fixed.md`: 新增状态流转交互规则说明
  - `transition-to-fixed.md`: 新增实际案例（云端泛化错误修复）
  - `transition-to-fixed.md`: 新增 Bug分析结论选项说明
  - `transition-to-nonbug.md`: 新增智能推断规则说明
  - `transition-to-nonbug.md`: 新增非Bug类卡片核心字段说明

### Changed
- 更新 pyproject.toml 版本号为 0.2.3
- 更新 docs/Skill_Guide.md 版本信息

## [0.2.3] - 2026-02-27

### Changed
- 优化技能描述，提高触发准确性
  - 增加空间ID格式（如 `edc-scrum`）作为触发词
  - 增加"Bug流转"、"状态转换"等用户常用表达
  - 增加"Bug分析结论"等字段名作为触发词
  - 采用触发导向式描述风格

## [0.2.2] - 2026-02-27

### Added
- 新增环境初始化指南，支持配置文件自动创建和依赖安装
  - `config/config.yaml` 不存在时自动从 `config.yaml.example` 复制
  - 提供 `pip install -e .` 依赖安装指引
  - 提供环境验证步骤

### Changed
- SKILL.md 新增环境错误提示，引导用户查阅通用指南完成环境配置
- 将环境初始化说明放置在 `references/general-guide.md`，避免每次技能加载时检查

## [0.2.1] - 2026-02-27

### Changed
- 提高必填字段检测阈值从 50% 到 80%，减少误判经常填写但实际非必填的字段
- `plan_transition.py` 默认输出格式改为 JSON，更适合 LLM 解析
- 重构 JSON 输出结构，新增 `_instruction` 字段明确指导 Claude 如何处理输出
- `plan_transition.py` 新增 `--comment` 参数支持，关闭卡片时自动添加默认评论
- 精简 README.md 文档，移除重复内容，改为引用外部详细文档
- 优化 SKILL.md 状态流转交互规则说明，简化文档结构

### Fixed
- 修复 `plan_transition.py` 关闭卡片时缺少必填 comment 字段的问题
- 修复必填字段检测中文本类型字段因值各不相同无法通过一致性判断的问题

### Removed
- 移除根目录 `postman_collections/` 目录，移动到 `docs/postman_collections/`

## [0.2.0] - 2026-02-26

### Added
- 新增 `scripts/plan_transition.py`: 一次性获取卡片状态流转的完整规划
  - 自动计算流转路径（多步流转支持）
  - 智能推断必填字段建议值（基于样本卡片）
  - 生成可直接执行的命令序列
  - 支持 `--max-samples` 参数调整样本数量
  - 支持 JSON 格式输出（`--format json`）

### Fixed
- 修复必填字段检测逻辑：车型、Bug问题原因等字段因值多样化导致未被检测的问题
- 修复文本类型字段因值各不相同无法通过一致性判断的问题
- 修复 resolveTime 等系统字段被错误识别为必填字段的问题

### Changed
- `_analyze_field_from_samples`: 新增 `fill_ratio` 和 `filled_count` 返回值
- `detect_required_fields`: 统一使用填写比例(fill_ratio >= 0.5)判断所有字段类型
- 添加 `SYSTEM_FIELDS` 过滤列表，过滤内部系统字段
- 改进空字符串过滤逻辑，正确判断 `needs_fill` 状态
- 更新 SKILL.md 文档，添加状态流转交互规则说明

## [0.1.4] - 2025-02-26

### Fixed
- 修复拼写错误
- 改进异常处理逻辑
- 修复配置键名问题

### Changed
- 迁移到 pyproject.toml (从 setup.py)
- 添加 CHANGELOG.md 文档

## [0.1.3] - 2025-02-26

### Added
- 完善文档说明
- 完善智能补全功能

### Removed
- 删除冗余代码

## [0.1.2] - 2025-02-26

### Fixed
- 修复必填字段设计时间时，没有检测出来的问题

## [0.1.1] - 2025-02-26

### Changed
- 修改 card_id 字段处理逻辑
- 调整 SKILL 文档

## [0.1.0] - 2025-02-26

### Added
- 移除冗余逻辑
- 修正 SKILL 提示信息

### Fixed
- 修复语法和ID错误
- 调整流程提示

## [0.0.9] - 2025-02-26

### Fixed
- 修复正则语法错误

## [0.0.8] - 2025-02-26

### Added
- 补全缺少字段异常处理

## [0.0.7] - 2025-02-26

### Added
- 增加必填参数参考文档

## [0.0.1] - 2025-02-26

### Added
- 初始版本发布
- 支持 iCafe 卡片查询、创建、修改操作
- 支持评论管理功能
- 支持字段验证
- 集成 click 命令行工具
