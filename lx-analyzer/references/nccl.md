## 专家经验库

以下是整理的部分结构化的专家经验库：包括日志现象、问题根因以及解决方案。


### 1. Uncorrectable ECC Error
**日志现象**: `uncorrectable ECC error encountered`
**问题根因**: GPU ECC Error
**解决方案**:
1. 关联 AIPod 硬件异常信息
2. 重启任务
3. 如果重启任务后仍旧启动失败，可能是超过了 ECC 阈值，需硬件报修

### 2. Uncorrectable NVLink Error
**日志现象**: `uncorrectable NVLink error detected during the execution`
**问题根因**: GPU nvlink 状态异常
**解决方案**:
1. 关联 AIPod 硬件异常信息
2. 硬件报修

### 3. A800 机型 NCCL 版本兼容性
**日志现象**: 机器名为 A800 机型 (包含 'a800')，且 NCCL 版本低于 2.15，任务 Hang 住
**问题根因**: A800 机型需要 NCCL 2.15 及以上版本，低版本存在兼容性问题
**解决方案**:
1. 升级 NCCL 版本到 2.15 或以上

### 4. NVLS 硬件异常
**日志现象**: WARN 日志中同时包含 `nvls.cc`、`Cuda failure` 和 `system not yet initialized`
**问题根因**: 机器 NVLS 硬件异常
**解决方案**:
1. 设置 `NCCL_NVLS_ENABLE=0` 来临时 workaround
2. 硬件报修

### 5. Socket Interface Config Error
**日志现象**: `no socket interface found`
**问题根因**: `NCCL_SOCKET_IFNAME` 配置错误
**解决方案**:
1. 请将 `NCCL_SOCKET_IFNAME` 配置为当前正确的 IP 地址或网卡名称

### 6. IBV Set ECE Failed
**日志现象**: `Call to ibv_set_ece failed with error Invalid argument errno 22`
**问题根因**: 硬件不支持 ECE 能力
**解决方案**:
1. 判断用于使用的 NCCL version
2. 如果高于 NCCL 2.23.4，可以通过 `NCCL_IB_ECE_ENABLE=0` 进行 workaround
3. 如果低于 NCCL 2.23.4，请升级 NCCL 版本

### 7. Async Event: GID Table Change
**日志现象**: `Got async event 日志。 event 为 GID table change`
**问题根因**: gid 跳变，通常是由于网卡抖动
**解决方案**:
1. 请通过 `show_gids` 确认网卡 gid 是否正常
2. 如果正常，请直接重启任务
3. 如果不正常，请剔除故障机

### 8. Async Event: Port Error / Port Active
**日志现象**: `Got async event 日志。 event 为 port error 或 port active`
**问题根因**: 网卡 down 或 网卡抖动
**解决方案**:
1. 如果 `port error` 后没有 `port active` 日志，则故障 root cause 为网卡 down 导致任务中断。建议：硬件报修。
2. 如果 `port error` 后有 `port active` 日志，且出现 `got completion error 12` 之类的日志，则故障 root cause 为网卡抖动导致任务中断。建议：`NCCL_IB_TIMEOUT=22` 进行容错。
3. 如果 `port error` 后有 `port active` 日志，且没有出现 `got completion error 12` 之类的日志，证明网卡抖动时 NCCL 层面已经进行了故障容错。请忽略该日志。

### 9. IBV Modify QP Failed
**日志现象**: 
- `Call to ibv_modify_qp failed with error No such device`
- `Call to ibv_modify_qp failed with error Invalid argument`
- `Call to ibv_modify_qp failed with error No data available`
- `non-zero status: 61 ibv_modify_qp failed`
**问题根因**: RDMA 设备或 GID 配置异常；NVSHMEM GID/HCA 配置异常。
**解决方案**:
1. 请检查 `NCCL_IB_HCA_LIST` 或 `NCCL_IB_GID_INDEX` (以及 NVSHMEM 对应配置) 与环境是否匹配
2. 检查设备注入情况 (针对 No such device)

### 10. IBV Open Device Failed
**日志现象**: `call to ibv_open_device failed`
**问题根因**: 可能是应用程序没有找到正确的 uverbs 设备
**解决方案**:
1. 执行 `ls /dev/infiniband/uverbs*` 查看环境上的 uverbs 设备
2. 如果是容器环境，请查看容器是否正常挂载设备

### 11. Wrong Magic / Wrong Type
**日志现象**: 日志包含 `misc/socket.cc` 和 `wrong magic`、`wrong type`
**问题根因**: 非法请求发送到 NCCL socket 端口；或者 NCCL 版本不一致
**解决方案**:
1. 升级 NCCL 2.27.3 来完全解决
2. 重启任务来做 workaround。可以考虑配置 `ip_local_port_range` 等参数来做更合理的规避
3. 检查并统一集群内的 NCCL 版本

### 12. Transport Create Connect Failed
**日志现象**: `transport create connect failed`
**问题根因**: 可能是用户 mlx 配置错误
**解决方案**:
1. 使用 `show_gids` 检查配置

### 13. Out Of Memory
**日志现象**: `out of memory`
**问题根因**: 任务占用了 GPU 的内存，或者当前任务的显存需求超过了机器上 GPU 的显存
**解决方案**:
1. 检查显存占用情况
2. 优化模型

### 14. No CUDA-capable Device
**日志现象**: `no CUDA-capable device is detected`
**问题根因**: 无法正确识别到应用程序所需的 CUDA 设备
**解决方案**:
1. 请检查应用程序代码和硬件配置

### 15. Connection Closed (非根因)
**日志现象**: `Connection closed by remote peer`;Connect to xxx.xxx.xxx.xxx<xxxxx> faild : Software caused connection abort
**问题根因**: 忽略此日志。这行日志并不重要，与 root cause 无关。通常是因为其他节点退出（如数据集错误、OOM、代码异常）导致。
**解决方案**:
1. 无

### 16. rank n of m ranks has already checked in
**日志现象**: `Bootstrap Root : rank 7 of 64 ranks has already checked in` 类似日志
**问题根因**: 忽略此日志。这行日志并不重要，与 root cause 无关。通常是因为其他节点退出（如数据集错误、OOM、代码异常）导致。
**解决方案**:
1. 用户代码问题。上层 paddle 代码调用 nccl 初始化的时候传错参数
