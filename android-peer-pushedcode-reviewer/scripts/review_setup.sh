#!/bin/bash
# review_setup.sh - 从 Gerrit ref 引用设置 review 环境
# 用法: bash review_setup.sh <ssh_url> <ref_path>
# 示例: bash review_setup.sh ssh://user@icode.baidu.com:8235/baidu/project refs/changes/00/119509400/5

set -e

SSH_URL="$1"
REF_PATH="$2"

if [ -z "$SSH_URL" ] || [ -z "$REF_PATH" ]; then
    echo "用法: bash review_setup.sh <ssh_url> <ref_path>"
    echo "示例: bash review_setup.sh ssh://user@icode.baidu.com:8235/baidu/project refs/changes/00/119509400/5"
    exit 1
fi

# 从 ref 路径提取 Change ID (refs/changes/XX/CHANGE_ID/PATCHSET)
CHANGE_ID=$(echo "$REF_PATH" | awk -F'/' '{print $(NF-1)}')
# 获取当前目录名作为项目名
PROJECT_NAME=$(basename "$(pwd)")

BRANCH_NAME="review/${CHANGE_ID}"
WORKTREE_DIR="../${PROJECT_NAME}-review-${CHANGE_ID}"

echo "=== Review 环境设置 ==="
echo "Change ID: ${CHANGE_ID}"
echo "分支名: ${BRANCH_NAME}"
echo "Worktree 目录: ${WORKTREE_DIR}"
echo ""

# Step 1: Fetch
echo "[1/3] Fetching 远端提交..."
git fetch "$SSH_URL" "$REF_PATH"
echo "Fetch 完成"

# Step 2: 创建分支（如已存在则先删除）
echo "[2/3] 创建 review 分支..."
if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
    echo "分支 ${BRANCH_NAME} 已存在，先删除旧分支"
    git branch -D "$BRANCH_NAME"
fi
git branch "$BRANCH_NAME" FETCH_HEAD
echo "分支 ${BRANCH_NAME} 创建完成"

# Step 3: 创建 worktree（如已存在则先清理）
echo "[3/3] 创建 worktree..."
if [ -d "$WORKTREE_DIR" ]; then
    echo "Worktree 目录已存在，先清理"
    git worktree remove "$WORKTREE_DIR" --force 2>/dev/null || rm -rf "$WORKTREE_DIR"
fi
git worktree add "$WORKTREE_DIR" "$BRANCH_NAME"
echo "Worktree 创建完成"

WORKTREE_ABS=$(cd "$WORKTREE_DIR" && pwd)
echo ""
echo "=== 设置完成 ==="
echo "Worktree 路径: ${WORKTREE_ABS}"
echo "请 cd 到该目录开始 review"
