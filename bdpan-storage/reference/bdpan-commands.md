# bdpan CLI 命令快速参考

## 认证命令

### login - 登录授权

```bash
bdpan login
```

桌面环境下（macOS）将自动弹出 WebView 授权窗口，完成登录后自动关闭。无 GUI 环境（如 SSH 远程登录）会自动切换到手动输入模式。

### logout - 注销登录

```bash
bdpan logout
```

清除本地存储的认证信息（`~/.config/bdpan/config.json`）。

### whoami - 查看认证状态

```bash
bdpan whoami
```

显示当前登录状态和 Token 有效期信息。

**已登录时输出：**
```
认证状态: 已登录
Token 有效期至: 2026-03-01 10:30:00
```

---

## 文件操作命令

### upload - 上传文件

```bash
bdpan upload <local> <remote>
```

| 参数 | 说明 |
|------|------|
| `local` | 本地文件或文件夹路径 |
| `remote` | 网盘目标路径（相对于 `/apps/bdpan/`） |

**示例：**
```bash
# 单文件上传
bdpan upload ./report.pdf report.pdf

# 文件夹上传
bdpan upload ./project/ project/

# 上传到子目录
bdpan upload ./data.tar.gz backup/data.tar.gz
```

**选项：**
- `--json` - JSON 格式输出上传结果

### download - 下载文件

```bash
bdpan download <remote> <local>
```

| 参数 | 说明 |
|------|------|
| `remote` | 网盘文件或文件夹路径（相对于 `/apps/bdpan/`） |
| `local` | 本地保存路径 |

**示例：**
```bash
# 单文件下载
bdpan download report.pdf ./downloaded-report.pdf

# 文件夹下载
bdpan download project/ ./project-restore/
```

**选项：**
- `--json` - JSON 格式输出下载结果

### ls - 查看文件列表

```bash
bdpan ls [path]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 要查看的目录路径 | 根目录 |

**选项：**
- `--json` - JSON 格式输出

**示例：**
```bash
# 查看根目录
bdpan ls

# 查看子目录
bdpan ls backup

# JSON 输出
bdpan ls --json
```

**输出格式：**
```
类型    大小          修改时间              文件名
------  ------------  --------------------  --------
目录     -            2026-02-20 10:30:00  documents
文件    1.5 MB        2026-02-25 15:20:00  readme.txt
文件    256 KB        2026-02-24 09:15:00  config.yaml

共 3 项
```

### share - 创建分享链接

```bash
bdpan share <path>
```

| 参数 | 说明 |
|------|------|
| `path` | 要分享的文件或文件夹路径 |

**示例：**
```bash
# 分享文件
bdpan share report.pdf

# 分享文件夹
bdpan share project

# JSON 输出
bdpan share --json report.pdf
```

**输出格式：**
```
分享链接创建成功!
链接: https://pan.baidu.com/s/1xxxxxxx
提取码: abcd
有效期: 7 天
```

**注意事项：**
- 分享功能需要付费订阅百度网盘服务
- 分享链接默认 7 天有效期

---

## 版本管理命令

### update - 检查/更新版本

```bash
# 手动检查更新
bdpan update check

# 自动更新到最新版本
bdpan update
```

**说明：**
- CLI 启动时会自动检查更新
- 发现新版本会显示提示

### version - 查看版本信息

```bash
# 查看当前版本
bdpan version

# 检查是否有更新
bdpan version --check
```

---

## 全局选项

| 选项 | 说明 |
|------|------|
| `--json` | JSON 格式输出 |
| `--no-check-update` | 禁用版本更新检查 |
| `--help` | 显示帮助 |
| `--version` | 显示版本 |

---

## JSON 输出格式

### ls 命令输出

```json
[
  {
    "Name": "report.pdf",
    "IsDir": false,
    "Size": 1536000,
    "Modified": "2026-02-25T15:20:00Z"
  },
  {
    "Name": "documents",
    "IsDir": true,
    "Size": 0,
    "Modified": "2026-02-20T10:30:00Z"
  }
]
```

### share 命令输出

```json
{
  "link": "https://pan.baidu.com/s/1xxxxxxx",
  "pwd": "abcd",
  "period": 604800,
  "short_url": "https://pan.baidu.com/s/1xxxxxxx",
  "share_id": "xxxxxxx",
  "path": "/apps/bdpan/report.pdf"
}
```

### upload/download 命令输出

```json
{
  "status": "success",
  "local_path": "./report.pdf",
  "remote_path": "report.pdf"
}
```

---

## 路径规则

- 所有路径相对于应用根目录 `/apps/bdpan/`
- 支持相对路径: `backup/data.tar.gz`
- 支持绝对路径: `/apps/bdpan/backup/data.tar.gz`
- 路径穿越 `..` 会被自动阻止

---

## 配置文件位置

```
~/.config/bdpan/config.json
```

**环境变量：**

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BDPAN_CONFIG_DIR` | 配置文件目录 | `~/.config/bdpan` |
| `BDPAN_INSTALL_DIR` | 二进制安装目录 | `~/.local/bin` |

---

## 常见错误码

| 错误 | 说明 | 解决方案 |
|------|------|---------|
| Token expired | Token 过期 | 重新登录 |
| Path not allowed | 路径不在允许范围 | 使用 /apps/bdpan/ 下的路径 |
| File not found | 文件不存在 | 检查路径是否正确 |
| Share API not available | 分享接口未开通 | 购买百度网盘开放平台服务 |

---

## 平台支持

| 功能 | macOS | Linux | Windows |
|------|-------|-------|---------|
| 基础功能 | ✅ | ✅ | ✅ |
| WebView 登录 | ✅ | - | - |
