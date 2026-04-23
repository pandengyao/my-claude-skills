# Code Review Skill

高效、建设性的代码评审技能，支持多种编程语言。基于预制的评审规则 checklist 进行自动化代码评审。

## 添加新语言支持

要添加新的编程语言支持，请按照以下步骤：

1. 在 `languages/` 目录下创建新的语言目录（例如：`languages/vuejs/`）
2. 创建以下文件结构：
   - `checklist.yaml` - 语言特定的检查清单（在 metadata 中声明继承 common 和 fe）
   - `examples.md` - 语言特定的代码示例
   - `cr-tool.md` - 语言特定的 CR 工具说明（可选）
3. 在 `checklist.yaml` 的 metadata 中声明继承关系：
   ```yaml
   metadata:
     language: Vue
     inherits:
       - ../../core/checklists/checklist-common.yaml
       - ../../core/checklists/checklist-fe.yaml  # 前端项目需要
   ```
4. 在 `SKILL.md` 的"支持的语言"部分添加链接
5. 参考现有 `languages/sanjs/` 目录的结构和内容
