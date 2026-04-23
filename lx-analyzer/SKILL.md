---
name: lx-analyzer
description: 灵犀分析。训练/推理任务故障分析技能，进行分布式训练或推理任务的故障诊断分析。可以分析 hang 问题、性能下降问题、OOM 问题、通信错误、NCCL 错误等。支持根据 job id 或任务日志进行分析。
---

## 概述

本技能用于分析和诊断分布式训练/推理任务的故障问题：

- **Hang 问题**: 任务挂起/超时诊断
- **性能下降**: 训练速度异常分析
- **NCCL 通信错误**: GPU 集合通信故障
- **OOM 问题**: 显存溢出
- **网络问题**: RDMA/InfiniBand 故障
- **硬件故障**: GPU ECC 错误、NVLink 故障

## 使用场景

- 分布式训练任务 hang 住或超时
- NCCL 通信失败
- GPU 显存溢出 (OOM)
- 训练性能异常下降
- 多节点通信问题

## 快速开始

使用 `analyzer_job.py` 进行 hang 和性能下降问题的诊断：

```bash
# 分析指定目录下的日志
~/py312/bin/python3 scripts/analyzer_job.py --log-dir /path/to/job-logs --pretty

# 指定 GPU 数量和输出文件
~/py312/bin/python3 scripts/analyzer_job.py --log-dir ./job-xxx \
    --gpus-per-node 8 \
    --output result.json \
    --pretty

# 详细模式
~/py312/bin/python3 scripts/analyzer_job.py --log-dir ./job-xxx -v
```

> **注意**: `analyzer_job.py` 仅用于 hang 和性能下降问题的诊断，故障根因诊断请参考专家经验库。

## 故障排查流程

### 0. 准备日志文件

检查 `nccl_logs/` 文件夹中是否有用户指定的日志文件夹：

```bash
ls -la nccl_logs/
```

**如果目录下没有日志文件，使用 `log_fetcher.py` 拉取日志：**

```bash
# 方式1：通过 Job ID 拉取（需要配置远程拉取服务）
~/py312/bin/python3 scripts/log_fetcher.py --job-id job-xxx --log-dir ./nccl_logs

# 方式2：仅检查本地日志是否存在
~/py312/bin/python3 scripts/log_fetcher.py --check-exists --log-dir ./nccl_logs/job-xxx

# 方式3：查找本地目录中的最新日志文件
~/py312/bin/python3 scripts/log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx -v

# 方式4：指定日志前缀（默认为 nccl）
~/py312/bin/python3 scripts/log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx --log-prefix run
```

**日志拉取逻辑说明：**

`log_fetcher.py` 实现了与 Go 版本 `LatestLogsWithPrefix` 相同的日志查找逻辑：

1. **本地查找**：在 `nccl_logs/` 目录下查找匹配 Job ID 的目录
   - 首先尝试精确匹配（如 `nccl_logs/job-xxx`）
   - 然后尝试前缀匹配（如 `nccl_logs/job-xxx-20240101`）

2. **日志文件发现**：从 `worker_*` 子目录中查找最新的日志文件
   - 支持日志前缀过滤（如 `run.log`, `nccl.log`）
   - 按文件修改时间选取最新的 `.log` 文件

3. **远程拉取**：如果本地没有日志，则从远程服务器拉取（使用内置默认配置）

**内置默认配置**（可通过环境变量覆盖）：

```bash
# 触发日志拉取的 URL
DIAGNOSE_LOG_TRIGGER_URL=http://10.206.196.162:8557/server/pdclog/log_load
# 查询拉取状态的 URL
DIAGNOSE_LOG_STATUS_URL=http://10.206.196.162:8557/server/pdclog/log_load_stat
# 轮询间隔（秒）
DIAGNOSE_POLL_INTERVAL=5
# 超时时间（分钟）
DIAGNOSE_TIMEOUT=30
# 最大文件大小（字节）
DIAGNOSE_MAX_FILE_SIZE=10485760
# NCCL 日志存储目录
DIAGNOSE_NCCL_LOG_DIR=nccl_logs
```

**输出结果示例：**

```json
{
  "success": true,
  "log_dir": "nccl_logs/job-xxx",
  "log_files": {
    "worker_00": "nccl_logs/job-xxx/worker_00/run.log",
    "worker_01": "nccl_logs/job-xxx/worker_01/run.log"
  },
  "count": 2,
  "message": "Found 2 log files in nccl_logs/job-xxx"
}
```

> **注意**: 如果日志拉取失败，请提示用户提供日志文件夹路径或确认 Job ID 是否正确。

### 1. Hang/降速问题诊断

使用 `analyzer_job.py` 进行诊断：

```bash
~/py312/bin/python3 scripts/analyzer_job.py --log-dir nccl_logs/<job-folder> --pretty -v
```

**分析结果判断**:
- **通信问题** (timeout、网络错误) → 进入步骤 2
- **OOM** → 参考专家经验库「显存问题」
- **静默 hang** → 建议使用 FlightRecorder 诊断

### 2. 通信问题分析

查看日志文件夹结构，搜索关键错误模式：

```bash
# 查看日志文件夹结构
ls -la nccl_logs/<job-folder>/

# 搜索 NCCL 错误
grep -r "NCCL.*error\|NCCL.*Error" nccl_logs/<job-folder>/

# 搜索网络相关错误
grep -r "network error\|remote process exited\|connection" nccl_logs/<job-folder>/

# 搜索 IB/RDMA 错误
grep -r "ibv_.*failed\|GID\|async event" nccl_logs/<job-folder>/

# 搜索 GPU 硬件错误
grep -r "ECC error\|NVLink error\|CUDA.*error" nccl_logs/<job-folder>/
```

根据搜索到的错误日志，参考专家经验库进行诊断。

### 3. 常见问题检查清单

- [ ] NCCL 版本是否满足要求 (A800 需要 >= 2.15)
- [ ] NCCL_SOCKET_IFNAME 是否正确配置
- [ ] NCCL_IB_HCA 是否与实际网卡匹配
- [ ] 防火墙是否允许 NCCL 端口通信
- [ ] ulimit 设置是否足够 (文件描述符、内存锁)
- [ ] GPU 驱动和 CUDA 版本是否兼容
- [ ] 集群内 NCCL 版本是否一致

## 故障诊断专家经验库

### 1. GPU 硬件故障

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `uncorrectable ECC error encountered` | GPU ECC Error | 关联硬件异常信息，重启任务，超过阈值需硬件报修 |
| `uncorrectable NVLink error detected` | GPU NVLink 异常 | 硬件报修 |
| `nvls.cc` + `Cuda failure` + `system not yet initialized` | NVLS 硬件异常 | `NCCL_NVLS_ENABLE=0` 临时规避，硬件报修 |

### 2. NCCL 版本兼容性

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| A800 机型 + NCCL < 2.15 + Hang | A800 需要 NCCL >= 2.15 | 升级 NCCL 版本 |

### 3. 网络配置问题

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `no socket interface found` | `NCCL_SOCKET_IFNAME` 配置错误 | 配置正确的 IP 或网卡名称 |
| `ibv_set_ece failed with Invalid argument` | 硬件不支持 ECE | NCCL >= 2.23.4: `NCCL_IB_ECE_ENABLE=0`；否则升级 NCCL |
| `ibv_modify_qp failed with No such device` | RDMA 设备配置异常 | 检查设备注入情况 |
| `ibv_modify_qp failed with Invalid argument/No data available` | GID 配置异常 | 检查 `NCCL_IB_GID_INDEX` |
| `ibv_open_device failed` | 未找到 uverbs 设备 | `ls /dev/infiniband/uverbs*`，容器环境检查设备挂载 |
| `transport create connect failed` | mlx 配置错误 | 使用 `show_gids` 检查配置 |

### 4. 异步事件

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `async event` + `GID table change` | GID 跳变，网卡抖动 | `show_gids` 确认状态，正常则重启任务，异常则剔除故障机 |
| `port error` 无 `port active` | 网卡 down | 硬件报修 |
| `port error` + `port active` + `completion error 12` | 网卡抖动 | `NCCL_IB_TIMEOUT=22` 容错 |
| `port error` + `port active` 无 error | NCCL 已容错 | 可忽略 |

### 5. NCCL 内部错误

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `misc/socket.cc` + `wrong magic/wrong type` | 非法请求或 NCCL 版本不一致 | 升级 NCCL 2.27.3；重启任务；统一集群 NCCL 版本 |

### 6. 显存问题

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `out of memory` | GPU 显存不足 | 检查显存占用；减小 batch size；使用梯度检查点 |

### 7. CUDA 设备问题

| 错误现象 | 根因 | 解决方案 |
|---------|------|---------|
| `no CUDA-capable device is detected` | 无法识别 CUDA 设备 | 检查应用程序代码和硬件配置 |

### 8. 可忽略的日志

| 日志内容 | 说明 |
|----------|------|
| `Connection closed by remote peer` | 因其他节点退出导致，非根因 |
| `rank n of m ranks has already checked in` | 上层代码参数错误，非 NCCL 问题 |

## Hang 问题诊断

### 静默 Hang (Silent Hang)

**现象**: 所有 rank 都报告超时，无明显的错误日志。

**诊断**: 检查是否所有 rank 都报告 `Watchdog caught collective operation timeout`

**解决**: 使用 FlightRecorder 进行 hang 故障诊断

### 部分节点超时

**现象**: 部分 rank 报告超时，有 rank 未报告。

**诊断**: 找出未报告超时的 rank，检查该 rank 的日志是否有错误

**解决**: 检查缺失 rank 的日志定位根因

## 错误代码参考

| 错误代码 | 描述 | 建议 |
|----------|------|------|
| ERR_GID_INDEX | GID 索引错误 | 检查 NCCL_IB_GID_INDEX 配置 |
| ERR_NETWORK_UNREACHABLE | 网络不可达 | 检查网络连接和防火墙 |
| ERR_CUDA_OOM | 显存溢出 | 减少模型大小或 batch size |
| ERR_COLLECTIVE_TIMEOUT | 集合通信超时 | 检查网络和硬件问题 |
| ERR_SILENT_HANG | 静默挂起 | 使用 FlightRecorder 诊断 |
| ERR_NCCL_INTERNAL | NCCL 内部错误 | 检查 NCCL 日志 |
| ERR_SEGMENTATION_FAULT | 段错误 | 检查 core dump 和堆栈 |

## 相关资源

- **NCCL 官方文档**: https://docs.nvidia.com/deeplearning/nccl/
- **NCCL GitHub**: https://github.com/NVIDIA/nccl
- **NCCL Tests**: https://github.com/NVIDIA/nccl-tests

## 脚本参考

### analyzer_job.py

**用途**: Hang 和性能下降问题诊断

**支持日志布局**:
- `worker_XX/*.log` (如 worker_00/run.log)
- `*-log.txt` (如 job-xxx-worker-0-log.txt)

**输出结果**:

| 错误代码 | 描述 |
|----------|------|
| ERR_SILENT_HANG | 所有 rank 都超时，静默 hang |
| ERR_COLLECTIVE_TIMEOUT | 部分 rank 超时 |
| ERR_NETWORK_UNREACHABLE | 网络问题导致启动失败 |
| ERR_CUDA_OOM | 显存溢出 |
| ERR_GID_INDEX | GID 配置错误 |

### analyzer_config.yaml

配置文件支持自定义时间戳解析模式、实例名提取模式、文件大小限制等。详见 `scripts/analyzer_config.yaml.example`。

### log_fetcher.py

**用途**: 日志拉取和查找工具

**核心功能**:
- 从本地目录查找匹配前缀的最新日志文件
- 从远程服务器下载任务日志（需配置 `LOG_FETCH_URL`）
- 检查日志文件是否存在

**使用方法**:

```bash
# 查找本地目录中的最新日志（默认前缀 nccl）
~/py312/bin/python3 scripts/log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx

# 检查日志是否存在
~/py312/bin/python3 scripts/log_fetcher.py --check-exists --log-dir ./nccl_logs/job-xxx

# 指定日志前缀
~/py312/bin/python3 scripts/log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx --log-prefix run

# 下载远程日志（需配置环境变量，可使用 .env 文件）
~/py312/bin/python3 scripts/log_fetcher.py --job-id job-xxx

# 详细模式
~/py312/bin/python3 scripts/log_fetcher.py --find-latest --log-dir ./nccl_logs/job-xxx -v
```

**参数说明**:

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--job-id` | 任务 ID（以 job- 开头） | - |
| `--log-dir` | 日志目录路径 | - |
| `--log-prefix` | 日志文件前缀 | `nccl` |
| `--find-latest` | 仅查找本地最新日志 | `false` |
| `--check-exists` | 仅检查日志是否存在 | `false` |
| `--output, -o` | 输出到 JSON 文件 | - |
| `--verbose, -v` | 详细输出 | - |

**环境变量**:

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DIAGNOSE_LOG_TRIGGER_URL` | 远程日志拉取触发 URL | `http://10.206.196.162:8557/server/pdclog/log_load` |
| `DIAGNOSE_LOG_STATUS_URL` | 远程日志拉取状态查询 URL | `http://10.206.196.162:8557/server/pdclog/log_load_stat` |
| `DIAGNOSE_POLL_INTERVAL` | 轮询间隔（秒） | `5` |
| `DIAGNOSE_TIMEOUT` | 超时时间（分钟） | `30` |
| `DIAGNOSE_MAX_FILE_SIZE` | 最大文件大小（字节） | `10485760` |
| `DIAGNOSE_NCCL_LOG_DIR` | NCCL 日志存储目录 | `nccl_logs` |

**日志查找逻辑**:

与 Go 版本 `LatestLogsWithPrefix` 保持一致：
1. 遍历 `worker_*` 子目录
2. 过滤匹配前缀的 `.log` 文件
3. 按修改时间选取最新文件
4. 返回 `worker -> log_file` 映射
