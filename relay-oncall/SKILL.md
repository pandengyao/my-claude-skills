---
name: relay-oncall
description: Relay堡垒机故障排查与问题诊断。触发词：relay/webrelay/webdesk/websql/webapp/堡垒机/连接失败/登录失败/认证失败/超时/断线/SSH报错/文件传输/远程桌面/RDP/VNC/MySQL连接/开白/客户端安装/指纹登录/扫码登录/beep认证/错误码/session共享。当用户提到以上关键词或描述连接、登录、传输相关问题时触发此Skill。
---

# Relay 堡垒机故障排查 Skill

辅助排查 Relay 堡垒机连接和使用过程中的各类问题。Relay 是百度内部堡垒机产品，用于从 OA（办公网）安全连接 IDC（数据中心）服务器。

## 产品概览

| 子产品 | 用途 | 地址 |
|--------|------|------|
| **WebRelay** | SSH 终端，登录 Linux 服务器 | webrelay.baidu-int.com |
| **WebDesk** | 远程图形桌面（RDP/VNC） | webrelay.baidu-int.com/desk |
| **WebSQL** | 跨办公网连接 MySQL 开发库 | webrelay.baidu-int.com/sql |
| **WebAPP** | 远程应用发布（Navicat/PLSQL） | webrelay.baidu-int.com/app |

## 问题分类决策树

根据用户描述的关键信息，判断问题所属分类，然后读取对应的 reference 文件进行排查：

```
用户描述问题
│
├─ 包含「登录/认证/密码/beep/指纹/扫码/令牌/token/uuap」
│  → 读取 references/auth_and_login.md
│
├─ 包含「超时/timeout/断线/连不上/Connection refused/SSH报错/错误码/no matching/no hostkey」
│  → 读取 references/connection_and_network.md
│
├─ 包含「远程桌面/RDP/VNC/WebDesk/桌面/剪切板同步/画面」
│  → 读取 references/webdesk_issues.md
│
├─ 包含「数据库/MySQL/WebSQL/SQL/开白/白名单/3306」
│  → 读取 references/websql_issues.md
│
├─ 包含「文件传输/上传/下载/lrzsz/trzsz/sftp/sz/rz/文件卡住」
│  → 读取 references/file_transfer.md
│
├─ 包含「客户端/安装/下载/配置/迁移/iterm/xshell/securecrt/relay-cli/session共享」
│  → 读取 references/client_setup.md
│
└─ 包含「快捷键/编码/乱码/vim/清屏/分屏/WebAPP/Navicat/PLSQL」
   → 读取 references/terminal_and_misc.md
```

**注意**：如果问题涉及多个分类，按需加载多个 reference 文件。

## 排查流程

1. 确认用户使用的子产品（WebRelay/WebDesk/WebSQL/WebAPP）和接入方式（浏览器/客户端/relay-cli/终端SSH）
2. 根据决策树匹配问题分类，读取对应 reference 文件
3. 在 reference 中查找匹配的问题现象和解决方案
4. **如果 reference 中无法找到匹配问题**，进入深度排查（见下方）
5. 如果深度排查仍无法解决，引导用户联系值班人员

## 深度排查：从知识库原始文档中查找

每个 reference 文件末尾附有「关联知识库文档列表」，列出了该场景相关的所有原始文档的 doc_id 和标题。

当 reference 中的总结内容无法解决用户问题时，按以下步骤操作：

1. 在当前 reference 文件末尾找到「关联知识库文档列表」
2. 根据用户问题描述，选择最可能相关的文档
3. 使用脚本读取原始文档全文：
   ```bash
   ~/py312/bin/python3 scripts/read_ku_doc.py <doc_id>
   ```
4. 从原始文档中查找与用户问题匹配的解决方案

> 知识库地址：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/HXFtYvbMQj/ZdzjXS3uzb/

## 联系方式与升级路径

当自助排查无法解决问题时，引导用户通过以下方式获取帮助：

- **邮箱**：ext_relay@baidu.com
- **如流用户群**：
  - WebRelay&Relay用户群：7033778（已满）
  - WebRelay&Relay用户2群：7780470（已满）
  - WebRelay&Relay用户3群：8927866（已满）
  - WebRelay&Relay用户4群：10198644

<!-- TODO: 如有值班人员轮值表或其他升级渠道，可在此补充 -->
