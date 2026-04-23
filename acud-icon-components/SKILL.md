---
name: acud-icon-components
description: acud-icon 图标库使用指南。当用户需要使用图标组件、询问可用图标、查找特定功能图标时使用此 skill。包含 722 个可用图标，涵盖操作、文件、数据、导航、状态等分类。
---

# acud-icon 图标库

## 概述

acud-icon 是百度云控制台的 React 图标组件库，提供 722 个图标，分为三类风格：

| 类型 | 前缀 | 数量 | 用途 |
|------|------|------|------|
| Outlined | `outlined-` | 678 | 描边图标，默认风格 |
| Filled | `filled-` | 15 | 实心图标，强调状态 |
| MultiTone | `multiTone-` | 29 | 多色图标，特殊场景 |

## 使用方式

### 基础用法

```tsx
import { OutlinedHome, OutlinedUser, FilledSuccess } from 'acud-icon';

// 基础使用
<OutlinedHome />

// 带尺寸
<OutlinedHome size={24} />

// 带颜色
<OutlinedHome style={{ color: '#1890ff' }} />

// 带旋转
<OutlinedLoading spin />
```

### 图标命名规则

图标组件名 = PascalCase(图标文件名)

例如：
- `outlined-home` → `OutlinedHome`
- `outlined-bce-user` → `OutlinedBceUser`
- `filled-success` → `FilledSuccess`
- `multiTone-cloud` → `MultiToneCloud`

### Props

```tsx
interface IconProps {
  size?: number | string;  // 图标尺寸，默认 16
  spin?: boolean;          // 是否旋转动画
  rotate?: number;         // 旋转角度
  style?: React.CSSProperties;
  className?: string;
  onClick?: React.MouseEventHandler;
}
```

## 常用图标速查

### 操作类

| 图标名 | 组件名 | 用途 |
|--------|--------|------|
| `outlined-plus` | `OutlinedPlus` | 添加 |
| `outlined-minus` | `OutlinedMinus` | 减少 |
| `outlined-edit` | `OutlinedEdit` | 编辑 |
| `outlined-delete` | `OutlinedDelete` | 删除 |
| `outlined-copy` | `OutlinedCopy` | 复制 |
| `outlined-search` | `OutlinedSearch` | 搜索 |
| `outlined-refresh` | `OutlinedRefresh` | 刷新 |
| `outlined-download` | `OutlinedDownload` | 下载 |
| `outlined-upload` | `OutlinedUpload` | 上传 |
| `outlined-setting` | `OutlinedSetting` | 设置 |

### 导航类

| 图标名 | 组件名 | 用途 |
|--------|--------|------|
| `outlined-home` | `OutlinedHome` | 首页 |
| `outlined-left` | `OutlinedLeft` | 左箭头 |
| `outlined-right` | `OutlinedRight` | 右箭头 |
| `outlined-up` | `OutlinedUp` | 上箭头 |
| `outlined-down` | `OutlinedDown` | 下箭头 |
| `outlined-menu` | `OutlinedMenu` | 菜单 |
| `outlined-menu-fold` | `OutlinedMenuFold` | 折叠菜单 |
| `outlined-menu-unfold` | `OutlinedMenuUnfold` | 展开菜单 |

### 状态类

| 图标名 | 组件名 | 用途 |
|--------|--------|------|
| `outlined-check-circle` | `OutlinedCheckCircle` | 成功 |
| `outlined-close-circle` | `OutlinedCloseCircle` | 错误 |
| `outlined-exclamation-circle` | `OutlinedExclamationCircle` | 警告 |
| `outlined-info-circle` | `OutlinedInfoCircle` | 信息 |
| `outlined-loading` | `OutlinedLoading` | 加载中 |
| `filled-success` | `FilledSuccess` | 成功(实心) |
| `filled-error` | `FilledError` | 错误(实心) |
| `filled-warn` | `FilledWarn` | 警告(实心) |

### 文件类

| 图标名 | 组件名 | 用途 |
|--------|--------|------|
| `outlined-file` | `OutlinedFile` | 通用文件 |
| `outlined-folder` | `OutlinedFolder` | 文件夹 |
| `outlined-file-pdf` | `OutlinedFilePdf` | PDF 文件 |
| `outlined-file-excel` | `OutlinedFileExcel` | Excel 文件 |
| `outlined-file-word` | `OutlinedFileWord` | Word 文件 |
| `outlined-file-image` | `OutlinedFileImage` | 图片文件 |
| `outlined-file-video` | `OutlinedFileVideo` | 视频文件 |

### 用户类

| 图标名 | 组件名 | 用途 |
|--------|--------|------|
| `outlined-user` | `OutlinedUser` | 用户 |
| `outlined-bce-user` | `OutlinedBceUser` | BCE 用户 |
| `outlined-bce-multi-user-new` | `OutlinedBceMultiUserNew` | 多用户 |

## 完整图标列表

完整 722 个图标列表请参见 [references/icon-list.md](references/icon-list.md)。

## 使用 IconFont

支持从 iconfont.cn 引入图标：

```tsx
import { createFromIconfontCN } from 'acud-icon';

const IconFont = createFromIconfontCN({
  scriptUrl: '//at.alicdn.com/t/xxx.js',
});

<IconFont type="icon-name" />
```
