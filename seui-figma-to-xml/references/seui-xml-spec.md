# SEUI XML 属性速查手册

## 视图类型

| `type` 值 | iOS 类 | 支持子元素 | 说明 |
|---|---|---|---|
| `container`（默认） | UIView | 是 | 布局容器 |
| `text` | UILabel / YYLabel | 否 | 不设高度时自动计算高度 |
| `button` | UIButton | 否 | 必须设置 `action` |
| `image` | UIImageView | 是 | 可在图片上叠加子元素 |

## 布局（Flexbox）

| 属性 | 可选值 | 默认值 |
|---|---|---|
| `flex-direction` | `column` `row` `row-reverse` `column-reverse` | `column` |
| `justify-content` | `flex-start` `center` `flex-end` `space-between` `space-around` `space-evenly` | `flex-start` |
| `align-items` | `stretch` `flex-start` `center` `flex-end` `baseline` | `stretch` |
| `align-self` | 同 align-items + `auto` | `auto` |
| `flex-wrap` | `no-wrap` `wrap` | `no-wrap` |
| `flex` | 数字 | - |
| `flex-grow` | 数字 | `0` |
| `flex-shrink` | 数字 | `1` |
| `flex-basis` | 数字 | `auto` |

## 尺寸

| 属性 | 格式 | 说明 |
|---|---|---|
| `width` / `height` | 数字、`"100%"` 或 数字+后缀 | 省略时自动计算 |
| `min-width` / `min-height` | 数字+后缀 | |
| `max-width` / `max-height` | 数字+后缀 | |
| `aspect-ratio` | `"16/9"` 或 `"1.778"` | 推荐使用分数格式 |

**缩放后缀**（仅iOS，直接跟在数字后面）：`F`=框架尺寸、`C`=内容尺寸、`T`=T参数、`H`=H参数  
示例：`font-size="16f"`、`width="320c"`

## 间距

| 属性 | 说明 |
|---|---|
| `margin` / `margin-top/bottom/left/right` | 外边距 |
| `padding` / `padding-top/bottom/left/right` | 内边距 |
| `position` | `relative`（默认） / `absolute` |
| `position-top/bottom/left/right` | 相对父元素的绝对偏移量 |

## 颜色

**格式**：`#RGB`、`#RRGGBB`、`#RRGGBBAA`

**渐变格式**：`#color1,#color2,...,startX,startY,endX,endY[,loc1,loc2,...]`  
常用方向：左→右 `0,0.5,1,0.5` · 上→下 `0,0,0,1` · 对角线 `0,0,1,1`

| 属性 | 暗黑模式变体 | 说明 |
|---|---|---|
| `background-color` | `background-color-dark` | 纯色或渐变 |
| `text-color` | `text-color-dark` | 仅纯色 |
| `border-color` | `border-color-dark` | 仅纯色 |
| `shadow-color` | `shadow-color-dark` | |
| `text-shadow-color` | `text-shadow-color-dark` | 仅 text/button 类型 |

## 文字

| 属性 | 可选值 / 说明 |
|---|---|
| `text` | 字符串，支持 `[img|...]` 行内图片 |
| `font-size` | 数字+后缀 |
| `font-weight` | `regular` `light` `thin` `medium` `semibold` `bold` `heavy` `black` |
| `text-align` | `left` `center` `right` `justified` `natural` |
| `number-of-lines` | 整数，`0` = 不限行数 |
| `letter-spacing` | pt，支持负值 |
| `line-spacing` | pt |
| `text-shadow-offset` | `"x,y"` |

## 富文本行内图片

```
[img|来源|宽度|高度]
[img|来源|宽度|高度|占位图]
[img|来源|宽度|高度|inset=top,left,bottom,right]
[img|来源|宽度|高度|corner-radius=值]
[img|来源|宽度|高度|占位图|inset=0,4,0,4|corner-radius=8]
```
- `来源`：本地资源名称或 `https://...` URL
- 宽高支持缩放后缀

## 图片

| 属性 | 暗黑模式变体 | 说明 |
|---|---|---|
| `src` | `src-dark` | URL 或本地资源名 |
| `placeholder` | `placeholder-dark` | 仅本地资源 |
| `background-image` | `background-image-dark` | 用于 button 背景图 |
| `background-image-placeholder` | `background-image-placeholder-dark` | |
| `content-mode` | - | `scale-to-fill` `scale-aspect-fit` `scale-aspect-fill` `center` `top` `bottom` `left` `right` |

## 边框与圆角

| 属性 | 说明 |
|---|---|
| `border-width` | pt |
| `corner-radius` | 统一四角圆角 |
| `corner-radius-top-left` | 独立圆角（iOS: CACornerMask） |
| `corner-radius-top-right` | |
| `corner-radius-bottom-left` | |
| `corner-radius-bottom-right` | |

## 显示与效果

| 属性 | 可选值 | 说明 |
|---|---|---|
| `alpha` | `0.0`–`1.0` | 透明度 |
| `is-hidden` | `true` / `false` | 隐藏时从布局流中移除 |
| `user-interaction-enabled` | `true` / `false` | 是否响应用户交互 |
| `blur-style` | `light` `dark` `extralight` `regular` `prominent` | 覆盖 background-color |

## 阴影

| 属性 | 说明 |
|---|---|
| `shadow-color` | 十六进制颜色 |
| `shadow-opacity` | `0.0`–`1.0` |
| `shadow-radius` | pt |
| `shadow-offset` | `"x,y"` |

## 事件

| 属性 | 说明 |
|---|---|
| `action` | 逗号分隔的事件名列表 |
| `custom-params` | JSON字符串，使用单引号：`'{"key":"val"}'` |
| `ubc-id` / `ubc-params` | 用于 `@ubc` 事件 |
| `toast-message` | 用于 `@toast` 事件 |
| `phone` | 用于 `@call` 事件 |
| `copy-text` | 用于 `@copy` 事件 |
| `scheme` | 用于 `@scheme` 事件 |

**内置事件**：`@toast` `@call` `@copy` `@scheme` `@ubc`

## 验证规则

1. 根元素必须为 `<view>`
2. `text` 和 `button` 类型不能包含子 `<view>` 元素
3. 颜色必须以 `#` 开头；渐变需要 ≥2 个颜色 + 4 个坐标值
4. `custom-params` / `ubc-params` 必须是用单引号包裹的有效JSON
5. `aspect-ratio` 格式：分数 `"16/9"` 或小数 `"1.778"`
6. 绝对定位元素需要一个 `position="relative"` 的祖先元素（或根元素）
7. `[img|...]` 最少3段：来源、宽度、高度
