# 连接与网络故障

## 目录
1. [Relay节点IP信息](#relay节点ip信息)
2. [连接超时/断线](#连接超时断线)
3. [SSH协议报错](#ssh协议报错)
4. [Session相关问题](#session相关问题)
5. [连接错误码参考](#连接错误码参考)
6. [自动断连与重连](#自动断连与重连)
7. [特殊网络环境](#特殊网络环境)

---

## Relay节点IP信息

### relay.baidu-int.com（百度正式员工，beep认证）
| IP | Hostname |
|----|----------|
| 172.31.22.20 | bjkjy-sns-relay08.bjkjy |
| 172.31.23.41 | bjkjy-sns-relay09.bjkjy |
| 172.31.43.62 | bjkjy-sns-relay10.bjkjy |
| 172.31.43.61 | bjkjy-sns-relay12.bjkjy |
| 10.227.188.14 | bjhw-sws-relay01.bjhw |
| 10.227.188.28 | bjhw-sws-relay02.bjhw |

### webrelay-linux.baidu-int.com（正式员工及外包，beep认证）
| IP | Hostname |
|----|----------|
| 172.31.21.41 | bjkjy-sns-relay07.bjkjy |
| 172.31.21.24 | bjkjy-sns-relay03.bjkjy |
| 172.31.46.52 | bjkjy-sns-extrelaybeep01.bjkjy |
| 10.227.145.140 | bjhw-sws-relay04.bjhw |
| 10.227.144.165 | bjhw-sws-relay03.bjhw |

### relay-cloud.baidu-int.com（百度云）
| IP | Hostname |
|----|----------|
| 10.21.246.190 | huabei-bj-d-relay2-01.bcc-bjdd |
| 10.21.241.8 | huabei-bj-d-relay2-02.bcc-bjdd |

## 连接超时/断线

### 现象：使用中Relay忽然掉线/卡死在输入密码界面/操作过程中卡死
- **原因**：网络不稳定、电脑网卡与AP冲突、策略拦截
- **解决**：
  1. 带笔记本走动切换AP热点（须确保实际切换了AP，重启WiFi不起作用）
  2. 使用有线网络

### 现象：登录Relay出现timeout报错
- **排查**：
  1. 确认无线连接的是 BAIDU（Baidu_Wifi、Baidu_Friend 等不行）
  2. 检查Relay地址能否 `ping` 通，22端口能否 `telnet` 通
  3. 如果不通，说明网络或Relay服务器有问题

### 现象：从Relay登陆服务器出现 Connection timed out
- **原因**：（1）后台开发机故障（2）服务器隔离域未对Relay IP开放（3）服务器防火墙控制（4）Docker网段与172网段冲突
- **解决**：联系部门OP处理。查询机器负责人：http://noah.baidu.com/ → 机器管理 → 输入hostname
- **补充**：检查是否有网段冲突、虚拟网卡；BCC机器检查专线路由配置

### 现象：直连BCC云服务器22端口时连接超时
- **原因**：内网专线缺少172网段路由
- **解决**：在「私有网络VPC」→「路由表」→「添加路由」，源网段 10.45.67.128/25，目标网段 172.16.0.0/12，下一跳选专线网关

### 现象：客户端因零信任导致断开
- **原因**：零信任策略导致网关随机匹配Relay IP
- **临时解决**：修改本地 hosts 文件，将 relay.baidu-int.com 解析到固定IP
  ```
  # Windows: C:\Windows\System32\drivers\etc\hosts
  # 从上方节点IP中选一个
  172.31.22.20 relay.baidu-int.com
  ```

### 现象：ssh登录relay时卡住不动（IP可连，域名无响应）
- **解决**：`cd ~/.ssh/ && rm -f master*`

### 现象：连接堡垒机之后连接开发机过程过卡
- **原因**：机器开启了 gssapi-with-mic 认证
- **解决**：登录机器后关闭该认证；临时使用 `ssh_bak_20250717 user@hostname`

## SSH协议报错

### 现象：Unable to negotiate ... no matching host key type found. Their offer: ssh-rsa,ssh-dss
- **原因**：MacOS升级导致SSH客户端版本与Relay不兼容
- **解决**：编辑 `~/.ssh/config`（目录不存在则 `mkdir ~/.ssh`）：
  ```
  Host *
    PubkeyAcceptedAlgorithms +ssh-rsa
    HostkeyAlgorithms +ssh-rsa
  ```

### 现象：ssh_exchange_identification: Connection closed by remote host
- **原因**：使用无效用户或密码错误次数过多，被安全插件封禁IP
- **解决**：
  1. 方法一：通过VNC进入服务器，编辑 `sudo vim /etc/sshd.deny.hosteye`，删除被封禁IP
  2. 方法二：添加白名单 `sudo vim /etc/hosts.allow`，加入Relay节点IP
  3. 方法三：检查机器负载是否过高；修改 `/etc/ssh/sshd_config` 中 MaxSessions

### 现象：no kex alg 报错
- **解决**：通过VNC登录服务器，编辑 `/etc/ssh/sshd_config`：
  ```
  KexAlgorithms +diffie-hellman-group1-sha1
  HostKeyAlgorithms +ssh-rsa
  ```
  然后 `service sshd restart`

### 现象：no hostkey alg 报错
- **解决**：重新生成host key：
  ```bash
  rm -rf /etc/ssh/ssh*key
  systemctl restart sshd
  ```

### 现象：ssh设备报错 .ssh/known_hosts 问题
- **解决**：在Relay命令行执行 `clearknownhost`

### 现象：fork: Resource temporarily unavailable
- **原因1**：Relay session连接过多 → 关闭不用的session
- **原因2**：客户端缓存文件 → 删除 `~/.ssh/master*` 文件

### 现象：报错 segmentation fault
- **原因**：ssh损坏（如brew安装的openssh更新系统后失效）
- **解决**：使用系统自带ssh `/usr/bin/ssh`

### 现象：麒麟银河ssh登录报错 no matching mac found
- **解决**：编辑服务器 `/etc/ssh/sshd_config`，注释掉 MACs/Ciphers/KexAlgorithms，添加：
  ```
  KexAlgorithms diffie-hellman-group1-sha1
  ```
  重启sshd；或使用 `ssh -oKexAlgorithms=+diffie-hellman-group1-sha1 root@xxx`

### 现象：Connection reset by peer
- **排查**：（1）iptables/firewall规则变更（2）SSH服务挂掉→重启（3）密码多次失败导致IP封禁
- **注意**：giano自动更新密码功能可能导致旧密码失效→反复失败→封禁Relay IP

### 现象：从开发机跳转到其他机器出现乱码报错
- **原因**：OpenSSH版本太低
- **解决**：升级开发机上的OpenSSH版本

### 现象：proxyconnect tcp: dial tcp xxxxx: connect: connection refused
- **原因**：配置了代理 https_proxy 环境变量
- **解决**：
  ```bash
  export no_proxy="duguanjia-local.internal.baidu.com,beep.baidu.com"
  unset https_proxy
  unset http_proxy
  ```

## Session相关问题

### 现象：mux_client_request_session: session request failed
- **原因**：Relay session连接数最大10个，配置了自动登录超过限制
- **解决**：`ps -ef | grep ssh` 找到相关session并kill

### 现象：Shared connection to relay.baidu-int.com closed
- **原因**：服务器故障导致同步账号ID变化
- **解决**：删除 `~/.ssh/master*` 缓存文件后重新登录

### 现象：配置了session共享功能但不生效
- **解决**：`rm ~/.ssh/master-*` 后重试

### 现象：报错 broken pipe
- **解决**：`ssh -o ServerAliveInterval=60 xxxx@relay.baidu-int.com`；或在 `~/.ssh/config` 添加 `ServerAliveInterval 60`

## 自动断连与重连

### Relay自动退出
- 会话处于Relay状态下，10分钟无操作自动退出session，窗口信号灯变灰
- 无需刷新浏览器，点击「+」新建会话即可

### 服务器自动退出
- 若需修改超时时间：编辑 `/etc/profile`，设置 `export TMOUT=14400`（4小时）
- 关闭超时：注释该配置或设为0

### 网络断开
- 4小时内恢复网络，可在窗口内按任意键触发重连，无需重新认证

## 连接错误码参考

| 错误码 | 名称 | 解释 |
|--------|------|------|
| 0 | SUCCESS | 操作成功 |
| 256 | UNSUPPORTED | 请求的操作不受支持 |
| 512 | SERVER_ERROR | 内部错误 |
| 513 | SERVER_BUSY | 服务器繁忙 |
| 514 | UPSTREAM_TIMEOUT | 上游服务器没有响应 |
| 515 | UPSTREAM_ERROR | 上游服务器遇到错误 |
| 516 | RESOURCE_NOT_FOUND | 资源未找到 |
| 517 | RESOURCE_CONFLICT | 资源已被使用或锁定 |
| 518 | RESOURCE_CLOSED | 相关资源已关闭 |
| 519 | UPSTREAM_NOT_FOUND | 上游服务器不存在或网络不可达 |
| 520 | UPSTREAM_UNAVAILABLE | 上游服务器拒绝连接 |
| 521 | SESSION_CONFLICT | 会话与另一会话冲突 |
| 522 | SESSION_TIMEOUT | 会话因非活动状态超时 |
| 523 | SESSION_CLOSED | 会话已被强制关闭 |
| 768 | CLIENT_BAD_REQUEST | 请求参数无效 |
| 769 | CLIENT_UNAUTHORIZED | 未登录，权限被拒绝 |
| 771 | CLIENT_FORBIDDEN | 权限被拒绝，登录无法解决 |
| 776 | CLIENT_TIMEOUT | 客户端响应超时 |
| 781 | CLIENT_OVERRUN | 客户端发送数据超限 |
| 783 | CLIENT_BAD_TYPE | 客户端发送了非法类型数据 |
| 797 | CLIENT_TOO_MANY | 客户端资源使用过多 |

## 特殊网络环境

### 现象：非内网ssh relay.baidu-int.com 没反应
- **原因**：酒店/外部WiFi的IP段（如172.31.x.x）与Relay网段冲突
- **解决**：使用手机热点，或使用WebRelay网页版

### 处于办公网的服务器使用8022端口登录
- **背景**：安全部要求办公网高危端口22禁止访问
- **解决**：服务器配置同时监听22和8022端口：
  ```
  # /etc/ssh/sshd_config
  Port 22
  Port 8022
  ListenAddress 0.0.0.0
  ```

### 现象：relay-cli报错 dial tcp 127.0.0.1:5001: connect: connection refused
- **解决**：重启度管家；如配置了代理需排除域名：
  ```bash
  export no_proxy=duguanjia-local.internal.baidu.com,beep.baidu.com
  ```

<!-- TODO: 补充更多网络相关场景 -->

---

## 关联知识库文档列表

当以上内容无法解决问题时，使用 `python3 scripts/read_ku_doc.py <doc_id>` 读取以下原始文档深入排查：

| doc_id | 标题 | 说明 |
|--------|------|------|
| Cr_hhsEDud8tPP | 7.1 WebRelay常见问题 | 70+条FAQ，包含大量连接/SSH/网络问题 |
| n9CrkWrCVN9zSo | 01 连接错误码 | 完整的错误码对照表 |
| Z4kJQCruTf19j_ | 客户端因零信任导致断开的问题 | 零信任策略导致的断连专项 |
| 9A2yeVTgATUpWk | 7.6 配置本地config文件保持session问题 | SSH config配置session共享 |
| WW_K9GwsKy0Xyb | 7.9 Relay-Cli常见使用问题 | relay-cli连接报错排查 |
| CmgUDUvOs00A4k | 7.0 WebRelay客户端使用手册 | 客户端连接方式和常见问题 |
| p8_-7c-FcZZoq6 | 1.产品介绍 | WebRelay产品介绍和架构 |
| Vuc9C3G__le5U7 | WebRelay使用文档（脱敏版） | WebRelay完整使用文档 |
| 3bc0f6404dc348 | 01. WebRelay使用文档 | WebRelay使用指南 |
