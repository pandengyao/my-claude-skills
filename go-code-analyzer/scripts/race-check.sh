#!/bin/bash
# Go 竞态检测脚本
# 用法: ./race-check.sh [package_path]

PACKAGE_PATH=${1:-.}

echo "=== Go 竞态检测 ==="
echo "目标路径: $PACKAGE_PATH"
echo ""

# 竞态检测构建
echo ">>> 执行竞态检测构建..."
go build -race "$PACKAGE_PATH/..." 2>&1

# 如果有测试，运行测试的竞态检测
if ls "$PACKAGE_PATH"/*_test.go 1> /dev/null 2>&1; then
    echo ""
    echo ">>> 执行测试竞态检测..."
    go test -race -short "$PACKAGE_PATH/..." 2>&1
fi

echo ""
echo ">>> 检测完成"