#!/bin/bash

# 扫描日志分析便捷脚本
# 用法: ./scripts/scan-log.sh [date|list|help]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_SCRIPT="$SCRIPT_DIR/analyze-scan-log.js"

if [ ! -f "$NODE_SCRIPT" ]; then
    echo "错误: 找不到分析脚本 $NODE_SCRIPT"
    exit 1
fi

# 调用 node 脚本
node "$NODE_SCRIPT" "$@"
