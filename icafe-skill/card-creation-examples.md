# 卡片创建示例

iCafe 卡片创建的实际使用示例。

## 创建带父卡片的子卡片

### 命令行方式

```bash
python scripts/create_card.py \
  --space iCafeTestDemo \
  --title "测试1" \
  --type Feature \
  --creator v_chenzhaojun \
  --parent 98 \
  --priority P2-Middle \
  --execute
```

### Python API 方式

```python
from icafe_skill import init_client
from icafe_skill.models import Issue
from icafe_skill.create import create_cards

client = init_client(config_file='config/config.yaml')

issue = Issue.create(
    title='测试1',
    detail='测试子卡片',
    type='Feature',
    creator='v_chenzhaojun',
    priority='P2-Middle',
    parent='98'  # 父卡片序号
)

result = create_cards(client, 'iCafeTestDemo', [issue], dry_run=False)
print(f'新卡片序号: {result["issueSequences"][0]}')
client.close()
```

### 验证父子关联

```bash
python scripts/query_card.py --space iCafeTestDemo --id 100
```

输出会显示父卡片信息：
```
父卡片:
  iCafeTestDemo-98: 测试父卡片
```

## 批量创建

```python
issues = [
    Issue.create(title='测试3', type='Feature', creator='v_chenzhaojun', parent='98'),
    Issue.create(title='测试4', type='Feature', creator='v_chenzhaojun', parent='98')
]

result = create_cards(client, 'iCafeTestDemo', issues, dry_run=False)
print(f'新卡片序号: {result["issueSequences"]}')
```

## 跨空间父卡片

```python
issue = Issue.create(
    title='跨空间子任务',
    type='Task',
    creator='v_chenzhaojun',
    parent='12345',                        # 父卡片序号
    parent_space_prefix_code='other-space' # 父卡片所在空间
)
```

命令行：
```bash
python scripts/create_card.py \
  --space my-space \
  --title "跨空间子任务" \
  --type Task \
  --creator v_chenzhaojun \
  --parent 12345 \
  --parent-space other-space \
  --execute
```

## 关联卡片

```python
issue = Issue.create(
    title='关联任务',
    type='Task',
    creator='v_chenzhaojun',
    rel_issue_space_pre_seq='space1-123,space2-456'  # 多个关联卡片
)
```

命令行：
```bash
python scripts/create_card.py \
  --space my-space \
  --title "关联任务" \
  --type Task \
  --creator v_chenzhaojun \
  --related "space1-123,space2-456" \
  --execute
```

## 常见问题

**Q: parent 参数使用什么值？**
A: 使用父卡片的序号（sequence），即卡片 ID `space-123` 中的数字部分 `123`。

**Q: 如何验证父子关联？**
A: 查询子卡片，脚本会自动显示父卡片信息。

**Q: 为什么查询父卡片时看不到子卡片列表？**
A: iCafe API 默认不返回子卡片列表，需用 IQL 查询。

**Q: 优先级有哪些可选值？**
A: `P0-Highest`、`P1-High`、`P2-Middle`、`P3-Low`、`P4-Lowest`（不同空间可能不同）。

## 扩展字段参考

| 参数 | 说明 |
|------|------|
| `parent` | 父卡片序号 |
| `parent_space_prefix_code` | 父卡片所属空间（跨空间用） |
| `rel_issue_space_pre_seq` | 关联卡片，格式 "空间标识-序号,空间标识-序号" |
