# bdpan-storage - 本地文件存储分享工具

> 基于 bdpan CLI 的文件上传与分享 Skill

## 简介

bdpan-storage 是一个 Claude Code Skill，用于将本地文件或文件夹上传到百度网盘并自动生成分享链接。它封装了 bdpan CLI 的核心功能，提供简洁的工作流程。

## 功能特性

- ✅ **文件上传** - 支持单文件上传到百度网盘
- ✅ **文件夹上传** - 递归上传整个文件夹结构
- ✅ **分享链接** - 自动创建 7 天有效期的分享链接
- ✅ **文件下载** - 从网盘下载文件或文件夹
- ✅ **文件列表** - 查看云端已上传的文件
- ✅ **JSON 输出** - 所有命令支持 JSON 格式输出

## 安装

### 前置条件

1. **安装 bdpan CLI**

使用本地一键安装脚本：

```bash
# 在 bdpan-skills 项目目录下执行
cd skills/bdpan-storage
bash scripts/install.sh

# 或非交互式安装
bash scripts/install.sh --yes
```

此脚本会自动检测您的操作系统和架构，下载对应的安装器并执行安装。

**当前版本**: v3.2.0

2. **完成登录认证**

```bash
bdpan login
```

桌面环境下（macOS）将自动弹出 WebView 授权窗口，完成登录后自动关闭。无 GUI 环境（如 SSH 远程登录）会自动切换到手动输入模式。

3. **验证安装**

```bash
bdpan whoami
```

### 安装 Skill

Skill 已位于项目的 `skills/bdpan-storage/` 目录下，Claude Code 会自动识别。

## 快速开始

### 上传并分享文件

只需对 Claude 说：

```
帮我上传并分享 ./report.pdf
```

Claude 会自动：
1. 执行 `bdpan upload ./report.pdf report.pdf`
2. 执行 `bdpan share report.pdf`
3. 返回分享链接和提取码

**预期输出：**
```
上传并分享成功！
链接: https://pan.baidu.com/s/1xxxxxxx
提取码: abcd
有效期: 7 天
```

### 查看已上传文件

```
查看我上传了哪些文件
```

**预期输出：**
```
类型    大小          修改时间              文件名
------  ------------  --------------------  --------
目录     -            2026-02-20 10:30:00  backup
文件    1.5 MB        2026-02-25 15:20:00  report.pdf
文件    256 KB        2026-02-24 09:15:00  config.yaml

共 3 项
```

## 命令参考

详细的命令参考请查看：
- [reference/bdpan-commands.md](./reference/bdpan-commands.md) - 完整命令文档
- [reference/troubleshooting.md](./reference/troubleshooting.md) - 故障排除指南

### 常用命令

| 命令 | 说明 |
|------|------|
| `bdpan upload <local> <remote>` | 上传文件或文件夹 |
| `bdpan download <remote> <local>` | 下载文件或文件夹 |
| `bdpan ls [path]` | 查看文件列表 |
| `bdpan share <path>` | 创建分享链接 |
| `bdpan login` | 登录授权 |
| `bdpan whoami` | 查看认证状态 |

## 存储位置

所有上传的文件存储在百度网盘的应用目录：

```
/apps/bdpan/
├── backup/          # 备份目录
├── documents/       # 文档目录
└── ...
```

## 安全说明

| 安全特性 | 说明 |
|---------|------|
| **作用域隔离** | 应用仅限 `/apps/bdpan` 目录，无法访问用户其他文件 |
| **路径穿越防护** | 自动检测并阻止 `..` 等危险路径 |
| **操作限制** | 不提供删除命令，防止数据丢失 |
| **OAuth 2.0** | 不存储密码，使用授权码模式认证 |

## 故障排除

### Token 过期

```bash
bdpan logout
bdpan login
```

### 分享接口未开通

分享功能需要购买百度网盘开放平台的付费服务。请访问 [百度网盘开放平台](https://pan.baidu.com/union/doc/) 了解详情。

### 路径不在允许范围

确保操作的路径在 `/apps/bdpan/` 目录下：

```bash
# 错误
bdpan ls /my-documents

# 正确
bdpan ls my-documents
```

更多问题请查看 [troubleshooting.md](./reference/troubleshooting.md)。

## 常见问题

### Q: 支持哪些操作系统？

A: 支持 macOS、Linux 和 Windows (WSL)。

### Q: 文件上传有大小限制吗？

A: 限制取决于百度网盘服务端。工具本身的超时设置为 30 分钟。

### Q: 分享链接可以永久有效吗？

A: 当前默认 7 天有效期。如需长期分享，可在链接过期后重新分享。

### Q: 为什么不能删除文件？

A: 出于安全考虑，暂不提供删除命令，防止误操作导致数据丢失。

### Q: 如何在脚本中使用？

A: 使用 `--json` 标志输出 JSON 格式：

```bash
# 获取所有文件名
bdpan ls --json | jq -r '.[].Name'

# 检查文件是否存在
bdpan ls --json | jq -e '.[] | select(.Name == "target.txt")'
```

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      Claude Code                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              bdpan-storage Skill                        │    │
│  │  - 解析用户意图                                       │    │
│  │  - 生成 bdpan 命令                                    │    │
│  │  - 格式化输出结果                                     │    │
│  └──────────────────────┬──────────────────────────────┘    │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      bdpan CLI                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   upload     │  │    share     │  │     ls       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  百度网盘 API                                │
│                                                              │
│  存储位置: /apps/bdpan/                                      │
└─────────────────────────────────────────────────────────────┘
```

## 相关链接

- [bdpan CLI 主项目](../../README.md)
- [bdpan 命令参考](./reference/bdpan-commands.md)
- [故障排除指南](./reference/troubleshooting.md)
- [Skill 规范参考](https://github.com/sanshao85/claude-skills-guide)

## 更新日志

### v1.1.0 (2026-03-04)

- 重构 SKILL.md，符合 claude-skills-guide 规范
- 新增故障排除文档 (troubleshooting.md)
- 优化 description，增加触发词
- 精简 SKILL.md 至 243 行（原 551 行）

### v1.0.0 (2026-02-27)

- 初始版本
- 支持文件/文件夹上传
- 支持自动生成分享链接
- 支持查看文件列表

## 许可证

[MIT License](../../LICENSE)
