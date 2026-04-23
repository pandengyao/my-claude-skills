---
name: processing-batch-crypto
description: 当用户要求加密数据、解密数据、批量加密文件、批量解密文件、哈希密码、Base64编码解码、或使用AES/DES/RSA/SHA256/MD5/SHA512算法处理敏感信息时，引导获取算法类型和密钥参数，执行加解密操作，返回处理结果或批量处理统计报告。
---

# 批量加解密处理

## 参数

### 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `data` | 要处理的数据（单个操作） | `"hello world"`, `"password123"` |
| `input` | 输入文件路径（批量操作） | `data.txt`, `emails.txt` |
| `algorithm` | 加密算法 | `AES`, `SHA256`, `BASE64` |
| `key` | 加密密钥（对称/非对称加密必需） | 参数传入或环境变量 `CRYPTO_KEY` |
| `iv` | 初始化向量（AES 加密必需） | 参数传入或环境变量 `CRYPTO_IV` |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `salt` | 哈希盐值 | 空 |
| `output` | 输出文件路径 | `{input}.encrypted` |
| `verbose` | 显示详细信息 | `false` |

### 交互流程
1. 检查是否已提供所有必需参数
2. 缺失时，一次性提示：
   ```
   检测到以下参数缺失：
   - algorithm: 请提供算法名称（如: AES, SHA256, BASE64）
   - key: 请提供密钥（对称/非对称加密必需，无默认值）
   - iv: 请提供初始化向量（AES 加密必需，无默认值）
   输入 "list-algorithms" 查看支持的算法
   ```
3. 获取参数后，复述确认再执行

> ⚠️ **安全强化**: 为防止安全风险，对称加密（AES/DES）不再提供默认密钥，必须显式配置

---

## ⚠️ 安全注意事项

> **重要**: 加解密操作涉及敏感数据，请务必遵循以下安全规范

| 风险类型 | 说明 | 建议措施 |
|---------|------|---------|
| 🔑 密钥明文暴露 | 命令行参数可能被记录到 shell 历史 | 使用环境变量 `CRYPTO_KEY` 传递密钥 |
| 📝 日志泄露 | `-v` 模式可能输出敏感数据 | 生产环境禁用详细模式 |
| 🔓 弱密钥风险 | 短密钥易被暴力破解 | AES 密钥 ≥16 字符，RSA ≥2048 位 |
| 📁 临时文件残留 | `.encrypted` 文件可能被未授权访问 | 处理完成后及时清理或设置权限 |
| 🔄 算法选择 | MD5/SHA1 已不安全 | 哈希推荐 SHA256/SHA512，加密推荐 AES-256 |

### 密钥管理最佳实践

```bash
# ✅ 推荐：使用环境变量（AES 需同时配置 KEY 和 IV）
export CRYPTO_KEY="your-secret-key"
export CRYPTO_IV="your-init-vector"
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "sensitive" --algorithm AES

# ✅ 也可以：通过参数传入（但会记录到 shell 历史）
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "sensitive" --algorithm AES --key "your-secret-key" --iv "your-init-vector"

# ❌ 错误：未配置密钥将报错
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "sensitive" --algorithm AES
# ValueError: 未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY
```

> **重要**: 对称加密（AES/DES）不提供默认密钥，必须显式配置，否则会抛出 `ValueError`

### 处理完成后的清理检查

```bash
# 检查是否有残留的加密文件
find . -name "*.encrypted" -o -name "*.decrypted" 2>/dev/null

# 清理临时文件（确认后执行）
# rm -i *.encrypted *.decrypted
```

---

## 支持的算法

| 算法 | 类型 | 可逆 | 依赖 |
|------|------|------|------|
| `AES` | symmetric | ✅ | cryptography |
| `DES` | symmetric | ✅ | pycryptodome |
| `RSA` | asymmetric | ✅ | cryptography |
| `SHA256` | hash | ❌ | 内置 |
| `MD5` | hash | ❌ | 内置 |
| `SHA512` | hash | ❌ | 内置 |
| `BASE64` | encoding | ✅ | 内置 |

---

## 环境预检

> 在执行加解密操作前，请先确认运行环境满足要求

### Step 0: 检查 Python 版本

```bash
~/py312/bin/python3 --version
# 要求: Python 3.7+
```

**检查点**: 版本 ≥ 3.7，否则提示升级

### Step 1: 检查依赖库

```bash
# 一键检测所有依赖
~/py312/bin/python3 -c "
import sys
deps = [
    ('cryptography', 'cryptography'),
    ('Crypto.Cipher', 'pycryptodome'),
]
missing = []
for module, package in deps:
    try:
        __import__(module.split('.')[0])
        print(f'✅ {package}')
    except ImportError:
        print(f'❌ {package} - 需要安装')
        missing.append(package)
if missing:
    print(f'\n安装命令: ~/py312/bin/pip install {\" \".join(missing)}')
    sys.exit(1)
print('\n✅ 所有依赖已就绪')
"
```

**检查点**: 所有依赖显示 ✅，否则执行提示的安装命令

### Step 2: 验证脚本可用

```bash
~/py312/bin/python3 scripts/crypto_cli.py list-algorithms
```

**检查点**: 正确显示算法列表，无 ImportError 或 ModuleNotFoundError

### 快速安装依赖

```bash
# 安装所有依赖
~/py312/bin/pip install cryptography pycryptodome

# 或使用国内镜像加速
~/py312/bin/pip install cryptography pycryptodome -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 执行步骤

### 单个加密

#### Step 1: 确认算法和参数
确认用户提供的 `algorithm`、`key` 等参数完整性。
**检查点**: 必需参数齐全，否则引导补充

#### Step 2: 执行加密
```bash
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "$data" --algorithm $algorithm --key "$key"
```
**检查点**: 命令返回 Base64 编码的密文，无错误输出

#### Step 3: 返回结果
输出加密后的密文，提示保存建议。
**检查点**: 输出为有效的 Base64 字符串

### 批量加密

#### Step 1: 验证输入文件
确认 `$input` 文件存在且可读。
**检查点**: 文件存在，内容非空

#### Step 2: 执行批量加密
```bash
~/py312/bin/python3 scripts/crypto_cli.py batch-encrypt --input "$input" --algorithm $algorithm --key "$key" -v
```
**检查点**: 显示处理进度，成功/失败计数

#### Step 3: 验证输出
确认输出文件已生成，内容行数与输入匹配。
**检查点**: 输出文件存在，成功数 > 0

#### Step 4: 返回统计报告
```
批量加密完成:
  成功: N 条
  失败: M 条
  结果已保存到: $output
```

---

## 异常处理

### 输入异常
| 异常 | 处理方式 |
|------|----------|
| 参数缺失 | 提示 "请提供 [参数名]，例如: [示例值]" |
| 算法不支持 | 提示 "不支持的算法，可用: AES, DES, RSA, SHA256, MD5, SHA512, BASE64" |
| 文件不存在 | 提示 "文件不存在: [路径]，请检查路径是否正确" |

### 执行异常
| 异常 | 处理方式 |
|------|----------|
| 依赖缺失 | 提示 "需要安装 [库名]: ~/py312/bin/pip install [库名]" |
| 密钥未配置 | 提示 "未配置加密密钥！请通过参数传入 key 或设置环境变量 CRYPTO_KEY" |
| IV 未配置 | 提示 "未配置初始化向量！请通过参数传入 iv 或设置环境变量 CRYPTO_IV"（仅 AES） |
| 密钥错误 | 提示 "解密失败，请确认密钥与加密时一致" |
| 哈希解密 | 提示 "SHA256/MD5/SHA512 是单向哈希，不支持解密" |

### 恢复策略
- 批量处理失败的行标记为 `ERROR: <原因>`，不中断整体流程
- 支持使用 `-v` 参数查看详细错误信息

---

## 示例

### 示例 1: AES 加密解密

**用户输入**: 
```
用 AES 加密 "hello world"，密钥是 mySecretKey
```

**执行过程**:
```bash
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "hello world" --algorithm AES --key mySecretKey
```

**输出结果**:
```
7K8X2pQm...base64密文...==
```

**解密验证**:
```bash
~/py312/bin/python3 scripts/crypto_cli.py decrypt --data "7K8X2pQm...==" --algorithm AES --key mySecretKey
# 输出: hello world
```

### 示例 2: 批量加密用户邮箱

**用户输入**:
```
批量加密 emails.txt 文件，使用 AES 算法
```

**执行过程**:
```bash
# 1. 查看输入文件
cat emails.txt
# user1@example.com
# user2@example.com
# user3@example.com

# 2. 批量加密
~/py312/bin/python3 scripts/crypto_cli.py batch-encrypt --input emails.txt --algorithm AES --key email-key -v
```

**输出结果**:
```
开始批量加密 3 条数据...
[1/3] ✅ user1@example.com...
[2/3] ✅ user2@example.com...
[3/3] ✅ user3@example.com...

批量加密完成:
  成功: 3 条
  失败: 0 条
  结果已保存到: emails.txt.encrypted
```

### 示例 3: 密码哈希

**用户输入**:
```
对密码 "myPassword" 做 SHA256 哈希，加盐 "random123"
```

**执行过程**:
```bash
~/py312/bin/python3 scripts/crypto_cli.py hash --data "myPassword" --algorithm SHA256 --salt "random123"
```

**输出结果**:
```
a1b2c3d4e5f6...（64位十六进制哈希值）
```

---

## 完成标准

### 必须满足
- [ ] 输入参数完整（算法、数据/文件、密钥）
- [ ] 命令执行无错误
- [ ] 输出结果格式正确（密文为 Base64，哈希为 Hex）
- [ ] 批量处理时成功数 > 0

### 质量检查
- [ ] 加密后可正确解密还原（可逆算法）
- [ ] 批量处理的输出文件行数与输入一致
- [ ] 错误行已标记且不影响其他行处理

### 验证命令
```bash
# 验证算法可用
~/py312/bin/python3 scripts/crypto_cli.py list-algorithms

# 验证加解密一致性（AES 需提供 key 和 iv）
encrypted=$(~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "test" --algorithm AES --key testkey --iv testiv)
~/py312/bin/python3 scripts/crypto_cli.py decrypt --data "$encrypted" --algorithm AES --key testkey --iv testiv
# 应输出: test

# 或使用环境变量
export CRYPTO_KEY="testkey"
export CRYPTO_IV="testiv"
encrypted=$(~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "test" --algorithm AES)
~/py312/bin/python3 scripts/crypto_cli.py decrypt --data "$encrypted" --algorithm AES
# 应输出: test
```

---

## 执行完成

### 建议保存的内容
| 类型 | 路径 | 说明 |
|------|------|------|
| 加密结果 | `{input}.encrypted` | 批量加密输出 |
| 解密结果 | `{input}.decrypted` | 批量解密输出 |
| 密钥配置 | 环境变量 `CRYPTO_KEY` | 避免明文存储 |

### 保存位置选项
- 项目 `data/` 目录 - 临时数据
- 项目 `output/` 目录 - 处理结果
- 环境变量 - 敏感密钥

---

## 快速命令参考

```bash
# 列出所有算法
~/py312/bin/python3 scripts/crypto_cli.py list-algorithms

# 单个加密
~/py312/bin/python3 scripts/crypto_cli.py encrypt --data "数据" --algorithm AES --key 密钥

# 单个解密
~/py312/bin/python3 scripts/crypto_cli.py decrypt --data "密文" --algorithm AES --key 密钥

# 批量加密
~/py312/bin/python3 scripts/crypto_cli.py batch-encrypt -i 输入文件 --algorithm AES --key 密钥 -v

# 批量解密
~/py312/bin/python3 scripts/crypto_cli.py batch-decrypt -i 加密文件 --algorithm AES --key 密钥 -v

# 哈希
~/py312/bin/python3 scripts/crypto_cli.py hash --data "数据" --algorithm SHA256 --salt 盐值

# 生成示例数据
~/py312/bin/python3 scripts/crypto_cli.py generate-sample
```

---

## 项目结构

```
processing-batch-crypto/
├── SKILL.md                   # 技能定义文件
├── scripts/
│   └── crypto_cli.py          # 命令行工具入口
├── src/
│   ├── __init__.py            # 模块导出
│   ├── manager.py             # CryptoManager 工厂类
│   ├── utils.py               # 便捷函数
│   └── strategies/            # 策略实现
│       ├── base.py            # 抽象基类
│       ├── symmetric.py       # AES, DES
│       ├── asymmetric.py      # RSA
│       ├── hash.py            # SHA256, MD5, SHA512
│       └── encoding.py        # Base64
└── examples/                  # 使用示例
```