# 故障排除指南

本指南涵盖了使用 bdpan CLI 时的常见问题和解决方案。

---

## 认证问题

### Token 过期

**症状：**
```
错误: Token 过期
Error: Token expired
```

**解决方案：**
```bash
bdpan logout
bdpan login
```

### WebView 无法打开

**症状：** 登录过程中浏览器或 WebView 窗口未出现。

**解决方案：**
工具会自动降级到 OOB（Out-of-Band）模式，按以下步骤操作：

1. 复制控制台显示的授权链接：
   ```
   https://openapi.baidu.com/oauth/...?device_code=xxxxx
   ```

2. 在浏览器中打开该链接

3. 完成授权后，浏览器会显示授权码

4. 复制授权码并粘贴到命令行提示处

5. 按回车确认

**示例输出：**
```
请在浏览器中打开以下链接完成授权:
https://openapi.baidu.com/oauth/2.0/authorize?response_type=device_code&client_id=...&device_code=xxxxx

授权成功后，浏览器会显示授权码，请复制并粘贴到这里:
[等待用户输入授权码...]
```

### 授权后登录失败

**症状：** 授权页面完成但登录仍然失败。

**解决方案：**
```bash
# 清除配置并重试
rm ~/.config/bdpan/config.json
bdpan login
```

---

## 分享链接问题

### 分享接口未开通

**症状：**
```
错误: 分享接口为付费接口
Error: Share API requires paid service
```

**解决方案：**
分享功能是百度网盘开放平台的付费服务。您需要：
1. 访问 [百度网盘开放平台](https://pan.baidu.com/union/doc/)
2. 购买分享 API 服务
3. 配置您的 API 凭证

### 分享链接已过期

**症状：** 用户无法访问分享链接。

**解决方案：**
分享链接默认 7 天有效期。重新分享文件：
```bash
bdpan share <路径>
```

---

## 文件操作问题

### 路径不在允许范围

**症状：**
```
错误: 路径不在允许范围内
Error: Path not in allowed range
```

**解决方案：**
确保所有路径都在 `/apps/bdpan/` 目录下。

错误：
```bash
bdpan ls /my-documents
bdpan upload ./file.txt /other/file.txt
```

正确：
```bash
bdpan ls my-documents
bdpan upload ./file.txt my-documents/file.txt
```

### 文件不存在

**症状：**
```
错误: 文件不存在
Error: File not found
```

**解决方案：**
1. 检查本地文件是否存在：
   ```bash
   ls -la <本地路径>
   ```
2. 检查远程文件是否存在：
   ```bash
   bdpan ls
   ```

### 上传/下载超时

**症状：** 操作耗时过长并超时。

**解决方案：**
1. 大文件可能需要最多 30 分钟
2. 检查网络连接稳定性
3. 对于非常大的文件，考虑先压缩/分割：
   ```bash
   # 上传前压缩
   tar -czf archive.tar.gz large-folder/
   bdpan upload archive.tar.gz backup/archive.tar.gz
   ```

### 权限不足

**症状：**
```
错误: 权限不足
Error: Permission denied
```

**解决方案：**
1. 检查本地文件权限：
   ```bash
   ls -l <本地路径>
   ```
2. 确保您对目标目录有写入权限：
   ```bash
   ls -ld <目标目录>
   ```

---

## 安装问题

### 命令未找到

**症状：** `bdpan: command not found`

**解决方案：**
```bash
# 重新运行安装脚本
cd skills/bdpan-storage
bash install.sh

# 或者检查 ~/.local/bin 是否在 PATH 中
echo $PATH

# 如果缺失则添加到 PATH（添加到 ~/.zshrc 或 ~/.bashrc）
export PATH="$HOME/.local/bin:$PATH"
```

### 下载了错误的架构

**症状：** 二进制文件无法运行或提示 "exec format error"

**解决方案：**
```bash
# 删除现有二进制文件
rm ~/.local/bin/bdpan

# 重新安装
cd skills/bdpan-storage
bash install.sh
```

---

## JSON 输出问题

### 无效的 JSON 输出

**症状：** `--json` 输出无法被解析。

**解决方案：**
1. 确保 stdout 中没有错误消息
2. 检查输出中只有 JSON 内容
3. 使用 `jq` 验证：
   ```bash
   bdpan ls --json | jq .
   ```

---

## 平台特定问题

### macOS

#### Gatekeeper 阻止

**症状：** 无法打开应用，因为它来自身份不明的开发者。

**解决方案：**
```bash
xattr -d com.apple.quarantine ~/.local/bin/bdpan
```

### Linux

#### 缺少依赖

**症状：** 二进制文件运行失败，提示缺少库。

**解决方案：**
安装所需依赖（特定于发行版）：
```bash
# Debian/Ubuntu
sudo apt-get install libc6

# Fedora/RHEL
sudo dnf install glibc
```

### Windows (WSL)

#### 路径问题

**症状：** Windows 路径无法正常工作。

**解决方案：**
在 WSL 中始终使用 Unix 风格路径：
```bash
# 正确
bdpan upload ./file.txt file.txt

# 错误
bdpan upload .\\file.txt file.txt
```

---

## 获取帮助

### 检查版本

```bash
bdpan version
```

### 获取命令帮助

```bash
bdpan --help
bdpan upload --help
bdpan download --help
```

### 启用调试模式

```bash
# 检查配置位置
ls -la ~/.config/bdpan/

# 查看配置文件（如果存在）
cat ~/.config/bdpan/config.json
```

---

## 联系支持

如果尝试上述解决方案后问题仍然存在：

1. 检查 [bdpan CLI 主项目](../../README.md) 获取最新更新
2. 在项目 issues 中搜索类似问题
3. 创建新 issue，包含：
   - 操作系统和版本
   - `bdpan version` 输出
   - 完整错误消息
   - 复现步骤
