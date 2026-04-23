#!/bin/bash
# review_cleanup.sh - 清理 review 环境
# 用法: bash review_cleanup.sh <change_id>
# 示例: bash review_cleanup.sh 119509400

set -e

CHANGE_ID="$1"

if [ -z "$CHANGE_ID" ]; then
    echo "用法: bash review_cleanup.sh <change_id>"
    echo "示例: bash review_cleanup.sh 119509400"
    exit 1
fi

PROJECT_NAME=$(basename "$(pwd)")
BRANCH_NAME="review/${CHANGE_ID}"
WORKTREE_DIR="../${PROJECT_NAME}-review-${CHANGE_ID}"

echo "=== 清理 Review 环境 ==="
echo "Change ID: ${CHANGE_ID}"
echo ""

# Step 1: 移除 worktree
if [ -d "$WORKTREE_DIR" ]; then
    echo "[1/2] 移除 worktree: ${WORKTREE_DIR}"
    git worktree remove "$WORKTREE_DIR" --force
    echo "Worktree 已移除"
else
    echo "[1/2] Worktree 目录不存在，跳过"
fi

# Step 2: 删除分支
if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
    echo "[2/2] 删除分支: ${BRANCH_NAME}"
    git branch -D "$BRANCH_NAME"
    echo "分支已删除"
else
    echo "[2/2] 分支不存在，跳过"
fi

echo ""
echo "=== 清理完成 ==="
