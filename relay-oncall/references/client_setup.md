# 客户端安装与配置

## 目录
1. [WebRelay客户端](#webrelay客户端)
2. [Relay-Cli命令行工具](#relay-cli命令行工具)
3. [Session共享配置](#session共享配置)
4. [第三方客户端迁移](#第三方客户端迁移)

---

## WebRelay客户端

### 下载地址

| 操作系统 | 下载链接 |
|----------|----------|
| Windows | https://webrelay-online-assets.bj.bcebos.com/smart-insight/web-relay-versions/WebRelay.exe |
| Mac M芯片系列 | https://webrelay-online-assets.bj.bcebos.com/smart-insight/web-relay-versions/WebRelay-arm.dmg |
| Mac Intel芯片系列 | https://webrelay-online-assets.bj.bcebos.com/smart-insight/web-relay-versions/WebRelay-intel.dmg |

### 登录账号
- 使用公司 EAC 统一登录
- **常见登录失败原因**：
  1. 本机安装了代理软件 → 关闭代理后重试
  2. Mac系统安装后需先退出安装器，从启动台启动客户端

### 登录堡垒机方式
1. 点击「+」新建relay窗口（本地窗口/relay/relay-cloud）
2. 双击左侧收藏服务器直接登录
3. 设置默认创建窗口：设置 → 通用功能 → 默认创建窗口
4. 当前窗口重连：点击侧边重连按钮

### 同步云端密码
- 左侧显示云端收藏的服务器，但密码需手动同步（安全级别较高，需二次认证）

### 应用更新
- v2.1.11 以后支持自动下载提示更新
- Mac端：设置 → 检查更新
- Windows端：帮助 → 设置 → 检查更新

### 现象：创建窗口失败，提示 posix_spawnp failed
- **解决**：退出并重启WebRelay客户端（Mac注意完全退出）

## Relay-Cli命令行工具

### 安装（仅支持Mac）
- 右键 → 打开安装包（不能直接双击打开）

### 使用方法
```bash
# 默认指纹登录
relay-cli

# 指定用户名
relay-cli -u chenshouqin

# 指纹登录
relay-cli -t fp

# 扫码登录
relay-cli -t qc

# 动态码登录
relay-cli -t ad

# 登录cloud堡垒机
relay-cli -h relay-cloud.baidu-int.com

# 查看帮助
relay-cli --help
```

### iTerm2配置
在profiles中设置命令：
```
/usr/local/bin/relay-cli -u username -t fp
```

### 常见问题

#### 报错 bad cpu type in executable
```bash
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
```
> Rosetta用于在Apple Silicon设备上运行Intel架构应用

#### 安装包安装失败
- 手动下载relay-cli二进制工具
- 出现「无法验证开发者」→ 系统设置 → 隐私与安全性中信任

#### 使用过程中提示证书到期
- 更新度管家版本

## Session共享配置

### Mac端配置
编辑 `~/.ssh/config`（目录不存在则 `mkdir ~/.ssh`）：

```
Host relay.baidu-int.com
  ControlMaster auto
  ControlPath ~/.ssh/master-%r@%h:%p
  ControlPersist yes
  ServerAliveInterval 60
  PubkeyAcceptedAlgorithms +ssh-rsa
  HostkeyAlgorithms +ssh-rsa

Host relay-cloud.baidu-int.com
  ControlMaster auto
  ControlPath ~/.ssh/master-%r@%h:%p
  ControlPersist yes
  ServerAliveInterval 60
  PubkeyAcceptedAlgorithms +ssh-rsa
  HostkeyAlgorithms +ssh-rsa
```

### 客户端一键导入
右上角设置 → 辅助功能 → 设置session共享 → 一键导入 → 刷新 → 保存

### 常见问题
- **无法一键导入**：检查目录权限，可手动写入
- **配置了不生效**：`rm ~/.ssh/master-*` 后重试
- **每打开一个Tab就需要认证**：Mac客户端使用本地OpenSSH，默认没配session共享

## 第三方客户端迁移

### Xshell迁移
<!-- TODO: 补充详细步骤，来源文档 281f422d8c1b4d -->

### SecureCRT迁移
<!-- TODO: 补充详细步骤，来源文档 LxxvGdfGME1KAw -->

### Electerm安装
<!-- TODO: 补充详细步骤，来源文档 DgiqpbhpTcujsl -->

### iTerm安装配置
<!-- TODO: 补充详细步骤，来源文档 1r8HYZa1fzAEyw -->

<!-- TODO: 补充更多客户端相关内容 -->

---

## 关联知识库文档列表

当以上内容无法解决问题时，使用 `python3 scripts/read_ku_doc.py <doc_id>` 读取以下原始文档深入排查：

| doc_id | 标题 | 说明 |
|--------|------|------|
| CmgUDUvOs00A4k | 7.0 WebRelay客户端使用手册 | 官方客户端完整使用手册 |
| xRuubnOYc2AsK8 | WebRelay官方客户端下载指南 | 客户端下载地址和说明 |
| n1IaOONZHrhwSL | 02.WebRelay官方客户端安装方法 | 客户端安装详细步骤 |
| D8SPdasmjl96D9 | Relay-Cli扫码&指纹登录来了 | relay-cli安装使用和iTerm配置 |
| 9A2yeVTgATUpWk | 7.6 配置本地config文件保持session问题 | SSH session共享配置 |
| 281f422d8c1b4d | Xshell迁移指导手册 | 从Xshell迁移到WebRelay |
| LxxvGdfGME1KAw | SecureCRT迁移指导手册 | 从SecureCRT迁移到WebRelay |
| DgiqpbhpTcujsl | Electerm下载安装教程 | Electerm安装和配置 |
| 1r8HYZa1fzAEyw | Iterm下载安装教程 | iTerm安装和relay-cli配置 |
| FmIQtgnc3CSO0W | WebRelay Client 更新日志 | 客户端版本更新记录 |
| WW_K9GwsKy0Xyb | 7.9 Relay-Cli常见使用问题 | relay-cli常见报错和解决方案 |
