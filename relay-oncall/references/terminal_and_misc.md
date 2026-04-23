# 终端使用与其他问题

## 目录
1. [终端操作问题](#终端操作问题)
2. [快捷键参考](#快捷键参考)
3. [编码问题](#编码问题)
4. [WebAPP问题](#webapp问题)
5. [Navicat/PLSQL迁移](#navicatplsql迁移)

---

## 终端操作问题

### 现象：使用vim时无法退出（esc键不生效）
- **原因**：浏览器插件拦截esc键（如Vimium插件）
- **解决**：关闭相关插件，或使用WebRelay客户端

### 现象：vim修改模式esc退出后光标失焦，无法继续:wq
- **原因**：浏览器拓展程序影响
- **解决**：关闭拓展程序或使用WebRelay客户端

### 现象：vim模式下无法选中命令行（鼠标光标不变为可选状态）
- **原因**：用户在~/.vimrc中配置了鼠标
- **解决**：在 `~/.vimrc` 中添加 `set mouse=v`

### 现象：已登录relay但点击+无法新建tab
- **原因**：在其他页面退出了uuap导致session判断异常
- **解决**：在浏览器中重新打开 webrelay，再回到之前页面即可恢复

### 现象：使用Safari时无法显示内容
- **原因**：老版本Safari对某些功能不兼容
- **解决**：推荐使用Chrome

### 现象：Safari登录提示密码错误（密码确实无问题）
- **原因**：Safari键入bug，第一个字符需要键入两遍
- **解决**：原密码123 → 手动键入1123；推荐使用Chrome

### 现象：页面出现乱码
- **原因**：浏览器插件导致显示错乱
- **解决**：逐个排查关闭浏览器插件

### 现象：粘贴内容开头和结尾出现0~和1~
- **原因**：bracketed paste mode
- **解决**：命令行输入 `printf '\e[?2004l'` 回车关闭

### 现象：Relay窗口突然被Killed
- **原因**：大量标准输出导致终端缓存区溢出
- **解决**：不要大量输出日志，前台程序重定向到日志文件

### 现象：win端电脑无法正确粘贴复制的内容
- **原因**：页面未开放剪切板读取权限
- **解决**：检查并开启当前页面的剪切板权限

### 现象：登录上服务器输入命令很卡
- **排查**：
  1. Tab中有使用rzsz传输文件时属于正常现象（数据流共享session）
  2. 服务器本身负载高 → 运行 `uptime` 查看负载，kill耗性能进程

### 现象：Telnet登录设备时无法键入删除键
- **原因**：退格键映射不一致
- **解决**：手动输入 Control+H 键代替

### 现象：双击快速创建新连接失败
- **原因**：系统辅助功能中连按速度设置过快
- **解决**：将连按速度设置低一些

### 现象：icoding虚拟机无法访问外网
- **解决**：https://console.cloud.baidu-int.com/devops/icode/dev/machine → 选中虚拟机 → 内网权限申请 → 访问公网权限

### 现象：从icoding免密登录开发机失败
- **原因**：icoding无门神免密权限
- **注意**：登录过程中需输入动态令牌（非邮箱密码），获取路径：手机如流 → 工作流 → 应用 → 动态令牌

### 现象：申请的开发机无法通过机器名访问，但IP可以
- **原因**：新机器未挂载DNS
- **解决**：联系 v_linhaolong 提供机器名称手动处理

### 如何查询用户登录历史和操作记录
- 用户操作命令无法通过Relay侧直接查询
- 确需可通过平台申请查询：http://giano.baidu.com/index.php?r=goldenEye

### 如何快速注销应用
<!-- TODO: 补充注销步骤 -->

## 快捷键参考

### WebRelay辅助区高频问题

**Q: 如何清除屏幕/清屏**
- A: 使用快捷键 `command+k`（Mac）或 `ctrl+k`（Windows）

**Q: 下载文件超时怎么办**
- A: 如使用 `sz -b` 下载，可切换为 `sz -be`（反之亦然）

**Q: 如何分屏**
- A: 在Tab页面点击右键 → 弹出操作栏 → 点击分屏

### 完整快捷键列表

| 功能 | Windows | Mac |
|------|---------|-----|
| 复制 | 鼠标选中自动复制 | 鼠标选中自动复制 / command+c |
| 粘贴 | -- | command+v |
| 搜索 | ctrl+shift+f | command+F |
| 切换Tab（数字） | Ctrl+数字键 | command+数字键 |
| 切换Tab（左右） | Ctrl+左右方向键 | command+左右方向键 |
| 切换上一个Tab | ctrl+alt+[ | ctrl+option+[ |
| 切换下一个Tab | ctrl+alt+] | ctrl+option+] |
| 关闭当前Tab | ctrl+alt+q | ctrl+option+q |
| 激活上一个分屏 | ctrl+alt+< | ctrl+option+< |
| 激活下一个分屏 | ctrl+alt+> | ctrl+option+> |
| 收起/展开左侧菜单 | ctrl+b | command+b |
| 收起/展开右侧编辑器 | ctrl+u | command+u |
| 快速清屏 | ctrl+k | command+k |
| 创建新窗口 | ctrl+alt+n | ctrl+option+n |
| 创建新分屏 | ctrl+alt+l | ctrl+option+l |

## 编码问题

### WebRelay编码设置
- 在Tab处右键 → 设置编码
- 若仍有编码问题，排查读取数据时是否采用了对应编码（如GBK查询数据库需在WebRelay也设为GBK）

## WebAPP问题

### 基本信息
- 地址：https://webrelay.baidu-int.com/app
- 发布应用：Navicat for MySQL、PL/SQL Developer
- **权限**：有白名单限制，默认无使用权限。申请加群 10198644 或联系 v_zhangchaosheng

### 现象：WebAPP无法复制粘贴
- **排查**：
  1. 检查浏览器是否给了剪切板权限
  2. 剪切板进程异常 → 退出程序10分钟后重试，或联系管理员重启剪切板进程

### 文件传输后的文件位置
- 网络 → tsclient → tsclient\WebApp Driver

## Navicat/PLSQL迁移

### Navicat查询迁移
<!-- TODO: 补充详细步骤，来源文档 w5hx3pniDzonzy -->

### Navicat连接迁移
<!-- TODO: 补充详细步骤，来源文档 DUW2cc8h5qCc6P -->

### PLSQL脚本导出导入
<!-- TODO: 补充详细步骤，来源文档 uhTUM0jo-lQGuS -->

### Navicat替换方案
- 推荐迁移至 WebSQL（webrelay.baidu-int.com/sql）
- 如WebSQL无法满足高阶需求，可使用WebAPP中的Navicat for MySQL

### Navicat导出文件下载说明
<!-- TODO: 补充详细步骤，来源文档 ddenJbtWcJ42VZ -->

<!-- TODO: 补充更多终端使用和杂项问题 -->

---

## 关联知识库文档列表

当以上内容无法解决问题时，使用 `python3 scripts/read_ku_doc.py <doc_id>` 读取以下原始文档深入排查：

| doc_id | 标题 | 说明 |
|--------|------|------|
| Cr_hhsEDud8tPP | 7.1 WebRelay常见问题 | 70+条FAQ，终端相关（#14/#15/#23/#32/#43/#46/#47/#52/#53/#58） |
| oTvl0VbSFKCY8b | 7.4 WebAPP常见问题 | WebAPP剪切板和文件问题 |
| SxeFQ9cZMcCdk3 | 7.5 WebRelay辅助区高频问题 | 清屏/下载超时/分屏等高频问答 |
| oegr1AP56fEBSt | 03.常用的一些快捷组合键 | 完整快捷键列表 |
| ol1rRKrKkZNuXj | 5.WebAPP | WebAPP完整使用文档 |
| lM7hFgop3OgWKb | 如何快速注销应用 | 应用注销方法 |
| q5EK-b8vmyw0XI | Navicat替换方案 | Navicat替代方案说明 |
| w5hx3pniDzonzy | 堡垒机Navicat查询迁移说明 | Navicat查询功能迁移步骤 |
| DUW2cc8h5qCc6P | 堡垒机Navicat连接迁移说明 | Navicat连接功能迁移步骤 |
| uhTUM0jo-lQGuS | PLSQL脚本导出导入 | PLSQL迁移操作步骤 |
| ddenJbtWcJ42VZ | WebAPP-Navicat导出文件下载说明 | Navicat导出文件下载 |
