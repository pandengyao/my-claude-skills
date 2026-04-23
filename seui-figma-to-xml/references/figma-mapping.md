# Figma → SEUI XML 映射指南

## 布局

### Frame / Auto Layout → container

| Figma | SEUI XML |
|---|---|
| Auto Layout 方向：垂直 | `flex-direction="column"`（默认，可省略） |
| Auto Layout 方向：水平 | `flex-direction="row"` |
| 对齐：居中 | `align-items="center"` |
| 对齐：末端 | `align-items="flex-end"` |
| 主轴：两端对齐 | `justify-content="space-between"` |
| 主轴：居中 | `justify-content="center"` |
| Gap（统一间距） | 在子元素上使用 `margin-bottom` 或 `margin-right`（SEUI无gap属性，用margin代替） |
| Padding（统一） | `padding="N"` |
| Padding（分边） | `padding-top/bottom/left/right="N"` |
| Fill container（填充父容器） | `flex="1"` 或 `width="100%"` |
| Hug contents（包裹内容） | 省略 width/height（自动计算） |
| 固定宽高 | `width="N"` `height="N"` |
| 裁剪内容 | 设置 `corner-radius` 或隐式 overflow: hidden |

### 约束 / 绝对定位

| Figma | SEUI XML |
|---|---|
| 固定顶部/左边（绝对父容器内） | `position="absolute"` `position-top="N"` `position-left="N"` |
| 固定四边（填满叠加） | `position="absolute"` `position-top="0"` `position-bottom="0"` `position-left="0"` `position-right="0"` |
| 父容器包含绝对子元素 | 父级无需特殊属性（`position="relative"` 为默认值） |

## 颜色

### 填充

| Figma | SEUI XML |
|---|---|
| 纯色填充（Frame） | `background-color="#RRGGBB"` |
| 带透明度的纯色填充 | 使用8位十六进制 `#RRGGBBAA`（透明度→Alpha通道） |
| 线性渐变填充 | `background-color="#color1,#color2,startX,startY,endX,endY"` |
| 带色标的线性渐变 | `background-color="#c1,#c2,#c3,sX,sY,eX,eY,loc1,loc2,loc3"` |
| 图片填充（Frame） | `background-image="asset_name"` 或 image类型上的 `src` |
| 无填充 / 透明 | 省略 `background-color` |

**渐变坐标转换：**  
Figma使用角度（度数），常用对应关系：
- 0°（上→下）：`0,0,0,1`
- 90°（左→右）：`0,0.5,1,0.5`
- 180°（下→上）：`0,1,0,0`
- 270°（右→左）：`1,0.5,0,0.5`
- 45°（左上→右下）：`0,0,1,1`
- 135°（右上→左下）：`1,0,0,1`

**透明度：** 图层透明度 → `alpha="0.8"`。填充透明度 → 转换为颜色十六进制的Alpha通道。

### 文字颜色

| Figma | SEUI XML |
|---|---|
| 文字填充（纯色） | `text-color="#RRGGBB"` |
| 带透明度的文字填充 | 8位十六进制或在文字视图上使用 `alpha` |

## 字体排印

| Figma | SEUI XML |
|---|---|
| 字号 | `font-size="16"` |
| 字重 100/200 | `font-weight="thin"` |
| 字重 300 | `font-weight="light"` |
| 字重 400 | `font-weight="regular"` |
| 字重 500 | `font-weight="medium"` |
| 字重 600 | `font-weight="semibold"` |
| 字重 700 | `font-weight="bold"` |
| 字重 800 | `font-weight="heavy"` |
| 字重 900 | `font-weight="black"` |
| 文字左对齐 | `text-align="left"`（默认，可省略） |
| 文字居中 | `text-align="center"` |
| 文字右对齐 | `text-align="right"` |
| 行高（超出默认的额外间距） | `line-spacing="N"`（N = Figma行高 - 字号 ≈ 额外间距） |
| 字间距 | `letter-spacing="N"`（Figma使用%，换算：`pt = fontSize × percent / 100`） |
| 文字截断 | `number-of-lines="1"`（或N为最大行数） |
| 文字换行 / 不截断 | `number-of-lines="0"` |

## 圆角

| Figma | SEUI XML |
|---|---|
| 统一圆角 | `corner-radius="N"` |
| 独立圆角 | `corner-radius-top-left="N"` `corner-radius-top-right="N"` `corner-radius-bottom-left="N"` `corner-radius-bottom-right="N"` |
| 圆形（半径 = 等边长度的一半） | `corner-radius="N"`，N ≥ 宽度/2 |

## 边框 / 描边

| Figma | SEUI XML |
|---|---|
| 描边（内部/居中/外部） | `border-width="N"` `border-color="#RRGGBB"` |
| 描边透明度 | border-color使用8位十六进制 |

注：SEUI使用 `layer.borderWidth/Color`，绘制在边界内（等同于Figma的"内部"描边）。

## 效果

### 阴影

| Figma 投影 | SEUI XML |
|---|---|
| 颜色 | `shadow-color="#RRGGBB"` |
| 透明度 | `shadow-opacity="0.3"` |
| 模糊 | `shadow-radius="N"` |
| X偏移 | `shadow-offset="x,y"` 的第一个值 |
| Y偏移 | `shadow-offset="x,y"` 的第二个值 |

### 模糊（背景模糊）

| Figma | SEUI XML |
|---|---|
| 背景模糊（浅色背景） | `blur-style="light"` |
| 背景模糊（深色背景） | `blur-style="dark"` |
| 通用 / 自适应 | `blur-style="regular"`（推荐） |

### 图层透明度

Figma图层透明度 → `alpha="0.8"`（值范围 0.0–1.0）

### 可见性

隐藏图层 → `is-hidden="true"`

## 视图类型选择

| Figma图层类型 | SEUI类型 | 条件 |
|---|---|---|
| Frame / Group | `container` | 有子元素，无文字内容 |
| 文字图层 | `text` | 只读文字展示 |
| 文字图层（可点击） | `button` 或带 `action` 的 `text` | 有交互 |
| 图片 / 图标 | `image` | 主要内容是图片 |
| 矩形 / Frame（按钮角色） | `button` | 明显的可交互元素 |
| 带图片填充的Frame | `image` 或带 `background-image` 的 `container` | 取决于是否有叠加子元素 |

## 常用 Figma 模式 → SEUI XML

### 带圆角和阴影的卡片
```xml
<view type="container" background-color="#FFFFFF" corner-radius="12" padding="16" shadow-color="#000000" shadow-opacity="0.12" shadow-radius="8" shadow-offset="0,4">
```

### 头像（圆形图片）
```xml
<view type="image" src="avatar_url" width="48" height="48" corner-radius="24" content-mode="scale-aspect-fill"/>
```

### 图标+文字水平排列
```xml
<view flex-direction="row" align-items="center">
    <view type="image" src="icon_name" width="20" height="20" margin-right="8"/>
    <view type="text" text="标签" font-size="14" flex="1"/>
</view>
```

### 渐变按钮
```xml
<view type="button" text="立即购买" background-color="#FF6B6B,#FF3B30,0,0.5,1,0.5" text-color="#FFFFFF" corner-radius="22" height="44" font-weight="semibold"/>
```

### 图片叠加文字（绝对定位）
```xml
<view type="image" src="banner_image" width="100%" height="200" content-mode="scale-aspect-fill">
    <view type="container" position="absolute" position-bottom="0" position-left="0" position-right="0" background-color="#00000080" padding-left="12" padding-right="12" padding-top="8" padding-bottom="8">
        <view type="text" text="图片标题" font-size="16" font-weight="semibold" text-color="#FFFFFF"/>
    </view>
</view>
```

### 标签 / 徽标
```xml
<view type="text" text="NEW" font-size="10" font-weight="bold" text-color="#FFFFFF" background-color="#FF3B30" corner-radius="4" padding-left="6" padding-right="6" padding-top="2" padding-bottom="2"/>
```

## 暗黑模式

当Figma同时提供浅色和深色设计方案时：
```xml
<background-color="#FFFFFF" background-color-dark="#1C1C1E" text-color="#000000" text-color-dark="#FFFFFF"/>
```
