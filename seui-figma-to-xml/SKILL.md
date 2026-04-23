---
name: seui-figma-to-xml
description: >
  根据Figma设计稿信息生成SEUI XML动态布局代码，适用于BDPSEUI框架。
  当用户提供Figma设计信息（画框、组件、样式、布局属性）并希望生成与设计视觉一致的有效、格式化的SEUI XML时，使用此skill。
  同样适用于用户要求验证、格式化或修复现有SEUI XML的场景。
  触发条件："根据Figma生成seui xml"、"figma转seui xml"、"生成SEUI XML"、"validate seui xml"、"格式化seui xml"、
  "根据设计稿写seui xml"，或任何将Figma设计数据与SEUI/XML输出相结合的请求。
---

# SEUI Figma → XML

## 参考文档

- **[seui-xml-spec.md](references/seui-xml-spec.md)** — 所有XML属性、验证规则、视图类型。需要属性详情时加载。
- **[figma-mapping.md](references/figma-mapping.md)** — Figma属性 → SEUI XML属性映射表及常用模式。翻译Figma设计时加载。

任何生成或验证任务开始时，请同时加载两个参考文档。

---

## 工作流程

### 1. 读取Figma输入

接受任意形式的设计数据：
- Figma2Code插件输出（JSON / 结构化描述）
- 用户描述的布局（文字描述画框、颜色、字体、约束）
- 截图标注（用户手动标注属性）

如果输入不明确，只询问最少必要信息：视图尺寸、布局方向、颜色和交互需求。

### 2. 映射到SEUI结构

使用 **figma-mapping.md** 进行属性转换。关键决策：

| 问题 | 规则 |
|---|---|
| 含子元素的Frame → ? | `type="container"` |
| 文本图层 → ? | `type="text"`（只读）或 `type="button"`（可交互） |
| 图片图层 → ? | `type="image"` |
| 有Auto Layout？ | 将方向/对齐/间距映射为Flexbox属性 |
| 绝对固定图层？ | `position="absolute"` + `position-top/left/right/bottom` |
| 渐变填充？ | 将角度转换为 `startX,startY,endX,endY` 坐标 |

### 3. 生成XML

**输出格式规范：**
- 每级缩进4个空格
- 每个属性之间使用空格分割
- 用注释（`<!-- ... -->`）标注逻辑分区（头部、主体、底部等）
- 所有`<view>`标签都需要有`type`属性，默认值为 `type="container"`
- 无子元素的叶节点使用自闭合 `/>`
- 图片视图添加随机背景色

```xml
<view type="container" background-color="#FFFFFF" corner-radius="12" padding="16">
    <!-- 标题区域 -->
    <view type="text" text="提交反馈" font-size="18" font-weight="bold" text-color="#333333" margin-bottom="8"/>
    <!-- 操作按钮 -->
    <view type="button" text="确认" background-color="#007AFF" text-color="#FFFFFF" corner-radius="8" height="44" action="onConfirm"/>
</view>
```

### 4. 验证

对照以下规则检查每个输出（完整列表见 seui-xml-spec.md §验证规则）：

- [ ] 根元素为 `<view>`
- [ ] `text` / `button` 类型没有子 `<view>` 元素
- [ ] 所有颜色以 `#` 开头；渐变：≥2 个颜色 + 4 个坐标值
- [ ] JSON参数（`custom-params`、`ubc-params`）用单引号包裹
- [ ] `[img|...]` 行内图片至少3个管道分隔段
- [ ] `aspect-ratio` 使用 `"16/9"` 分数或小数，不用 `16:9`
- [ ] 所有叶节点使用自闭合 `/>`

### 5. 输出

交付内容：
1. **格式化XML**（代码块）
2. **属性列表**： 属性 + 属性值的映射表
3. **备注**：XML无法表达的内容说明（动画、原生交互、平台限制），重点提示下（增加⚠️⚠️⚠️）图片视图添加了随机背景色需进行手动更改

---

## 属性速查表

| 需求 | 属性 |
|---|---|
| 水平排列 | `flex-direction="row"` |
| 子元素垂直居中 | `align-items="center"` |
| 子元素均匀分布 | `justify-content="space-between"` |
| 填充剩余宽度 | `flex="1"` |
| 叠加在图片上 | 子元素使用 `position="absolute"` |
| 圆形视图 | `corner-radius` = 宽度/2 |
| 仅顶部圆角 | `corner-radius-top-left` + `corner-radius-top-right` |
| 暗黑模式颜色 | `background-color-dark` 与 `background-color` 配合使用 |
| 文字内联图标 | `text="文字 [img|icon_name|16|16] 更多"` |
| 多事件按钮 | `action="onCustom,@ubc"` 配合 `ubc-id` 属性 |
| 模糊背景 | `blur-style="regular"` |
