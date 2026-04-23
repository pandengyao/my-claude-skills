# WebSQL 数据库问题

## 目录
1. [基础信息](#基础信息)
2. [白名单配置](#白名单配置)
3. [连接报错](#连接报错)
4. [查询相关问题](#查询相关问题)

---

## 基础信息

- **平台地址**：https://webrelay.baidu-int.com/sql
- **用途**：跨越办公网---IDC网络隔离直接访问开发库（仅用于开发，禁止连接线上库）
- **支持登录方式**：指纹登录、如流扫码登录、账密登录

## 白名单配置

### WebSQL服务器IP（需对以下IP加白）
```
10.21.2.128
10.21.244.58
10.45.33.111
```

- 微云孵化数据库已实现直连，无需额外开白
- 其他数据库需手动对以上IP加白

### MySQL开白教程
<!-- TODO: 补充 MySQL 开白的详细步骤，来源文档 kA8Of7W0V8YQTb -->

## 连接报错

| 问题描述 | 原因 | 解决方案 |
|----------|------|----------|
| `dial tcp: lookup xxx on 172.100.0.100:53: no such host` | DNS未解析到地址 | 使用IP代替主机名连接 |
| `Error 1045 (28000): Access denied for user` | 1. 密码错误 2. 账号无远程登录权限 | 确认密码；对WebSQL服务IP开白 |
| `Error 1130 - Host 'xxx' is not allowed to connect` | 数据库未对WebSQL服务IP开白 | 参考白名单配置加白 |
| `dial tcp xxx:3306: connect: connection timed out` | 网络不可达 | 检查机器防火墙 iptables 配置 |

## 查询相关问题

### 查询上限提醒
- **原因**：性能及安全限制，平台不支持大批量导出数据
- **解决**：手动分页查询
  ```sql
  -- 示例：查询第2页，每页10条
  SELECT * FROM user 
  ORDER BY id DESC
  LIMIT 10 OFFSET 10;
  ```

<!-- TODO: 补充更多 WebSQL 使用问题 -->

---

## 关联知识库文档列表

当以上内容无法解决问题时，使用 `python3 scripts/read_ku_doc.py <doc_id>` 读取以下原始文档深入排查：

| doc_id | 标题 | 说明 |
|--------|------|------|
| 0CCmrbtkUvT5MX | 7.3 WebSQL常见问题 | WebSQL全部FAQ |
| R6QtwEUQClhyos | 4.WebSQL | WebSQL完整使用文档（连接/数据库/表操作） |
| 1MT44UYF_fTySR | WebSQL使用手册 | 详细使用手册 |
| kA8Of7W0V8YQTb | MySQL开白教程 | MySQL白名单配置详细步骤 |
| KJ9e5b-qw3A_pZ | WebSQL 需求收集 | 用户需求和已知问题 |
| Kcr5kIA0FxdA_x | WebSQL 更新日志 | 版本更新记录，可能包含已修复问题 |
| LdsV7ZakWqlqQW | WebSQL客户端尝鲜版体验邀请 | WebSQL客户端信息 |
