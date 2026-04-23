---
name: figma-image-processor
description: 从 Figma 文件下载图片素材并进行压缩、上传 CDN。支持两种链路：(1) api 模式：调用 feed-activity 平台接口压缩和获取 STS 上传，(2) standalone 模式：本地 Pillow 压缩并使用 BOS AK/SK 直传。适用于 Figma URL/fileKey 批量导出图片，或本地目录图片批量压缩上传，支持按节点过滤并输出压缩率和 CDN 链接清单。
---

# Figma Image Processor

## Overview

批量执行 Figma 图片下载、压缩、上传 CDN，支持 `api` 和 `standalone` 双模式。

## Workflow

1. 收集输入图片  
   - Figma：解析 `fileKey`，调用 Figma API 获取 IMAGE fills  
   - 本地：读取 `--local-dir` 或 `--local-files`
2. 下载原图（Figma）或读取本地原图
4. 压缩图片  
   - `api` 模式：`/api/image-compressor/compress`  
   - `standalone` 模式：本地 Pillow
5. 上传 CDN  
   - `api` 模式：`/api/bos/sts` + BOS 上传  
   - `standalone` 模式：BOS AK/SK 直传
6. 输出报告（压缩率、失败原因、CDN URL）

## Commands

### api 模式（依赖本地服务）

```bash
~/py312/bin/python3 scripts/figma_image_processor.py \
  --mode api \
  --figma-input "https://www.figma.com/design/<fileKey>/<name>" \
  --figma-token "$FIGMA_TOKEN" \
  --target-path "cny2026/images" \
  --api-base "http://localhost:3000"
```

### standalone 模式（不依赖本地服务）

```bash
~/py312/bin/python3 scripts/figma_image_processor.py \
  --mode standalone \
  --figma-input "<fileKey>" \
  --figma-token "$FIGMA_TOKEN" \
  --target-path "cny2026/images" \
  --bos-ak "$BOS_AK" \
  --bos-sk "$BOS_SK" \
  --format webp \
  --preset balanced
```

### standalone 仅压缩不上传

```bash
~/py312/bin/python3 scripts/figma_image_processor.py \
  --mode standalone \
  --figma-input "<fileKey>" \
  --figma-token "$FIGMA_TOKEN" \
  --no-upload \
  --output-dir "./compressed"
```

### 按 node 过滤

```bash
~/py312/bin/python3 scripts/figma_image_processor.py \
  --mode standalone \
  --figma-input "<fileKey>" \
  --figma-token "$FIGMA_TOKEN" \
  --node-ids "1:2,3:9" \
  --limit 10
```

### 处理本地目录（例如 `.temp-images`）

```bash
~/py312/bin/python3 scripts/figma_image_processor.py \
  --mode standalone \
  --local-dir "/path/to/.temp-images" \
  --target-path "cny2026freewatch/demo" \
  --bos-ak "$BOS_AK" \
  --bos-sk "$BOS_SK"
```

## Parameters

- `--mode`: `api|standalone`（默认 `api`）
- `--figma-input`: Figma URL 或 fileKey（与本地输入二选一）
- `--figma-token`: Figma token（走 Figma 输入时需要，也可通过 `FIGMA_TOKEN`）
- `--local-dir`: 本地图片目录（与 `--figma-input` 二选一）
- `--local-files`: 本地图片文件列表，逗号分隔（可与 `--local-dir` 组合）
- `--target-path`: CDN 路径（默认 `lego-data/test`）
- `--bucket`: BOS bucket（默认 `feed-activity`）
- `--bos-endpoint`: 自定义 BOS endpoint，默认 `https://{bucket}.cdn.bcebos.com`
- `--api-base`: API 地址（仅 `api` 模式使用）
- `--bos-ak`: BOS AK（仅 `standalone` 上传时需要，也可通过 `BOS_AK`/`BCE_ACCESS_KEY_ID`）
- `--bos-sk`: BOS SK（仅 `standalone` 上传时需要，也可通过 `BOS_SK`/`BCE_SECRET_ACCESS_KEY`）
- `--bos-session-token`: BOS session token（可选，支持临时凭证）
- `--format`: `original|jpeg|png|webp|avif`
- `--quality`: 压缩质量 1-100（默认 80）
- `--preset`: `high|balanced|small`（覆盖 `--quality`）
- `--node-ids`: 仅处理指定 node id（逗号分隔）
- `--limit`: 最多处理多少张
- `--no-upload`: 只压缩不上传
- `--download-dir`: 保存 Figma 原图到本地
- `--output-dir`: 保存压缩图到本地
- `--json-out`: 输出结果 JSON 路径

## Notes

- `standalone` 模式需要安装 Pillow：`~/py312/bin/pip install Pillow`
- `api` 模式链路与 `feed-activity-platform/src/views/image-compressor/index.vue` 对齐
- 批量前建议先用 `--limit 1` 验证配置
- 本地模式上传命名默认使用原文件名（如 `redpack-63.png`）
