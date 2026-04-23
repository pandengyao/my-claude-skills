---
name: bdpan-storage
description: 上传文件/文件夹到百度网盘并生成分享链接，或从云端下载文件。当用户说"上传并分享"、"存储分享"、"分享文件"、"从网盘下载"、"upload to cloud"、"share file"时使用。
---

# 百度网盘存储

将本地文件或文件夹上传到百度网盘（`/apps/bdpan/` 目录）并自动生成 7 天有效期的分享链接。同时支持从云端下载文件。

## 核心功能

| 功能 | 说明 |
|------|------|
| 上传 | 上传文件/文件夹到 `/apps/bdpan/` |
| 分享 | 生成分享链接（7 天有效期，需付费服务） |
| 下载 | 从云端下载文件/文件夹 |
| 列表 | 查看已上传文件 |
| 认证 | 登录、注销、查看状态 |

## 快速开始

### 安装

```bash
cd skills/bdpan-storage
bash scripts/install.sh
```

### 登录（OOB 模式）

非 GUI 环境下，使用登录脚本：

```bash
bash scripts/login.sh
```

脚本会自动：
1. 获取授权链接并展示
2. 等待用户在浏览器中完成授权
3. 输入授权码完成登录

**手动方式：**

```bash
# 1. 获取授权链接
AUTH_URL=$(bdpan login --get-auth-url)
echo "请访问: $AUTH_URL"

# 2. 等待用户输入授权码
read -p "请输入授权码: " CODE

# 3. 完成登录
bdpan login --set-code "$CODE"
```

> 详细认证流程请参考 [authentication.md](./reference/authentication.md)

### 验证

```bash
bdpan whoami
```

## 工作流程

### 登录检查

```bash
# 检查登录状态
bdpan whoami

# 如果未登录
bash scripts/login.sh
```

### 上传并分享

```bash
bdpan upload <本地路径> <远程路径>
bdpan share <远程路径>
```

向用户返回：分享链接、提取码、有效期。

### 下载

```bash
bdpan download <远程路径> <本地路径>
```

### 查看文件

```bash
bdpan ls              # 根目录
bdpan ls <路径>       # 特定目录
bdpan ls --json       # JSON 格式
```

## 基本示例

### 示例 1: OOB 登录流程

```bash
# 使用登录脚本
bash scripts/login.sh

# 输出:
# [INFO] 检查登录状态...
# [INFO] 未登录，开始 OOB 授权流程...
# [INFO] 正在获取授权链接...
#
# ========================================
# 请在浏览器中打开以下链接完成授权:
# ========================================
#
# https://openapi.baidu.com/oauth/2.0/authorize?device_code=xxxxx
#
# ========================================
#
# 请输入浏览器中显示的授权码: [用户输入授权码]
# [INFO] 正在使用授权码完成登录...
# [INFO] ✓ 登录成功！
```

### 示例 2: 上传并分享

```bash
# 检查登录状态（未登录会提示）
bdpan whoami

# 上传文件
bdpan upload ./report.pdf report.pdf

# 生成分享链接
bdpan share report.pdf

# 输出:
# 分享链接创建成功!
# 链接: https://pan.baidu.com/s/1xxxxxxx
# 提取码: abcd
# 有效期: 7 天
```

### 示例 3: 查看已上传文件

```bash
bdpan ls
```

**输出：**
```
类型    大小          修改时间              文件名
------  ------------  --------------------  --------
目录     -            2026-02-20 10:30:00  backup
文件    1.5 MB        2026-02-25 15:20:00  report.pdf

共 2 项
```

> 更多示例请参考 [examples.md](./reference/examples.md)

## 存储位置

```
/apps/bdpan/
├── backup/          # 备份目录
├── documents/       # 文档目录
└── ...
```

## 安全性

- **作用域隔离** - 应用仅限于 `/apps/bdpan/` 目录
- **路径穿越防护** - 自动阻止 `..` 和危险路径
- **无删除功能** - 不提供删除命令以防止数据丢失
- **OAuth 2.0** - 不存储密码，使用授权码模式

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| Token 过期 | `bdpan logout && bdpan login` |
| 分享接口未开通 | 购买百度网盘开放平台服务 |
| 路径不在允许范围 | 使用 `/apps/bdpan/` 下的路径 |

> 详细故障排除请参考 [troubleshooting.md](./reference/troubleshooting.md)

## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` | JSON 格式输出 |
| `--no-check-update` | 禁用版本检查 |
| `--help` | 显示帮助 |
| `--version` | 显示版本 |

## 参考文档

| 文档 | 说明 |
|------|------|
| [authentication.md](./reference/authentication.md) | 认证流程详解 |
| [examples.md](./reference/examples.md) | 使用示例 |
| [bdpan-commands.md](./reference/bdpan-commands.md) | 完整命令参考 |
| [troubleshooting.md](./reference/troubleshooting.md) | 故障排除 |
