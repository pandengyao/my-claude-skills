#!/bin/bash
# Go 内存逃逸分析脚本
# 用法: ./escape-analysis.sh [package_path]

PACKAGE_PATH=${1:-.}

echo "=== Go 内存逃逸分析 ==="
echo "目标路径: $PACKAGE_PATH"
echo ""

# 执行逃逸分析
echo ">>> 执行逃逸分析..."
go build -gcflags="-m -m" "$PACKAGE_PATH/..." 2>&1 | grep -E "(escapes to heap|moved to heap|leaking param)" | head -100

echo ""
echo ">>> 分析完成"
echo "注意: 显示前 100 条逃逸信息，完整结果请去掉 head 限制"