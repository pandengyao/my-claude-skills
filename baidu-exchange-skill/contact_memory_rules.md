# 联系人记忆规则

当用户表达以下意图时，应调用 baidu-dumail-skill 并修改 references/MEMORY.md：

## 触发关键词/模式
1. **领导/老板/上级关系声明**：
   - "XXX是我领导/老板/上级"
   - "XXX是我主管/经理"
   - "向XXX汇报"
   - "我的领导是XXX"

2. **联系人偏好设置**：
   - "记住XXX的邮箱"
   - "XXX的邮件需要特殊关注/优先处理"
   - "重要联系人XXX"
   - "把XXX标记为重要/紧急联系人"

3. **邮件处理偏好**：
   - "来自XXX的邮件要马上提醒我"
   - "XXX的邮件需要优先回复"
   - "领导邮件优先处理"

4. **邮箱地址记录**：
   - "XXX的邮箱是xxx@baidu.com"
   - "记一下XXX的联系邮箱"
   - "保存XXX的邮件地址"

## 处理流程
1. 识别用户意图中的**人物名称**和**邮箱地址**
2. 读取当前的 `references/MEMORY.md`
3. 在"常用联系人"部分添加/更新条目
4. 如果提到"领导/需要特殊关注"，可以添加备注说明

## 示例转换
用户输入 → MEMORY.md 记录
- "zhangjianxing是我领导，他的邮件需要特殊关注" → `- **领导**: zhangjianxing (zhangjianxing@baidu.com)`
- "记住 lisi@baidu.com 是财务" → `- **财务**: lisi (lisi@baidu.com)`
- "wangwu 的邮件要优先处理" → `- **重要联系人**: wangwu (wangwu@baidu.com)`
- "我的项目经理是 zhaoliu，邮箱 zhaoliu@baidu.com" → `- **项目经理**: zhaoliu (zhaoliu@baidu.com)`

## 特殊说明
- 如果没有提供邮箱地址，默认使用 `姓名@baidu.com` 格式
- 可以添加emoji区分重要性：⭐ 表示重要，👑 表示领导，📧 表示普通联系人