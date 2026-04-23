#!/bin/bash
# 收集代码变更信息脚本
# 用途: 收集指定 commit 的代码变更信息
# 优先级: 命令行参数 > $AGILE_COMMENTS 环境变量 > 最新 commit (fallback)
#
# 用法:
#   bash collect-changes.sh                        # 从 $AGILE_COMMENTS 或 fallback 最新 commit
#   bash collect-changes.sh <commit1> [commit2...]  # 指定一个或多个 commit

set -e

# 1. 查看当前状态
echo "=== 当前 Git 状态 ==="
git status
echo ""

# 2. 获取 commit 列表（按优先级）
echo "=== 获取 commit 列表 ==="

if [ $# -gt 0 ]; then
    # 优先级 1: 命令行参数指定的 commit
    echo "📌 来源: 命令行参数"
    COMMIT_IDS="$*"

    # 验证每个 commit 是否存在
    for commit_id in $COMMIT_IDS; do
        if ! git cat-file -t "$commit_id" &>/dev/null; then
            echo "❌ 错误: commit $commit_id 不存在!"
            exit 1
        fi
    done
    echo "✅ 使用指定的 commit: $COMMIT_IDS"

elif [ -n "$AGILE_COMMENTS" ]; then
    # 优先级 2: 从环境变量 $AGILE_COMMENTS 获取
    echo "📌 来源: 环境变量 \$AGILE_COMMENTS"
    echo "原始内容: $AGILE_COMMENTS"

    # 从 JSON 数组中提取所有 Commit 字段
    # 使用 grep 和 sed 提取 commit ID (兼容性更好)
    COMMIT_IDS=$(echo "$AGILE_COMMENTS" | grep -oE '"Commit":"[^"]+' | sed 's/"Commit":"//' | tr '\n' ' ')

    if [ -z "$COMMIT_IDS" ]; then
        echo "❌ 错误: 无法从环境变量中解析出 commit ID!"
        echo "请检查 \$AGILE_COMMENTS 格式是否正确"
        exit 1
    fi
    echo "✅ 解析到的 commit: $COMMIT_IDS"

else
    # 优先级 3: fallback - 使用最新的 commit
    echo "📌 来源: fallback 策略 (最新 commit)"
    echo "⚠️  未指定 commit 且环境变量 \$AGILE_COMMENTS 未设置"

    LATEST_COMMIT=$(git rev-parse HEAD 2>/dev/null)

    if [ -z "$LATEST_COMMIT" ]; then
        echo "❌ 错误: 无法获取最新的 commit!"
        exit 1
    fi

    echo "✅ 使用最新 commit: $LATEST_COMMIT"
    COMMIT_IDS="$LATEST_COMMIT"
fi

echo "✅ 解析到的 commit ID 列表:"
echo "$COMMIT_IDS"
echo ""

# 4. 获取每个 commit 的信息
COMMIT_COUNT=$(echo "$COMMIT_IDS" | wc -w | tr -d ' ')
echo "=== 提交历史 (共 $COMMIT_COUNT 个提交) ==="

for commit_id in $COMMIT_IDS; do
    echo "---"
    echo "📌 Commit: $commit_id"
    git log -1 --oneline "$commit_id" 2>/dev/null || echo "⚠️  警告: commit $commit_id 不存在"
done
echo ""

# 5. 获取所有 commits 的变更摘要
echo "=== 变更文件摘要 ==="

# 计算第一个和最后一个 commit 之间的差异
FIRST_COMMIT=$(echo "$COMMIT_IDS" | awk '{print $1}')
LAST_COMMIT=$(echo "$COMMIT_IDS" | awk '{print $NF}')

# 如果只有一个 commit，使用 commit^..commit 格式
if [ "$FIRST_COMMIT" = "$LAST_COMMIT" ]; then
    echo "单个 commit 的变更:"
    git show --stat "$FIRST_COMMIT" 2>/dev/null || echo "⚠️  无法显示 commit 统计信息"
else
    echo "从 $FIRST_COMMIT^ 到 $LAST_COMMIT 的变更:"
    git diff --stat "$FIRST_COMMIT^".."$LAST_COMMIT" 2>/dev/null || \
        git diff --stat "$FIRST_COMMIT~1".."$LAST_COMMIT" 2>/dev/null || \
        echo "⚠️  无法显示差异统计信息"
fi
echo ""

# 6. 输出带新文件行号标注的完整代码差异
echo "=== 完整代码差异（已标注新文件行号）==="
echo "格式说明:"
echo "  [L:行号 ] 该行在修改后新文件中的行号（上下文行或新增行）"
echo "  [del    ] 删除行，在新文件中不存在"
echo "  [hunk   ] diff hunk 头部"
echo "  [meta   ] diff 元信息行"
echo ""

# 用 awk 在每行前标注新文件行号（+ 侧行号）
annotate_diff() {
    awk '
BEGIN { new_line = 0; in_diff = 0 }
/^@@/ {
    in_diff = 1
    # 取第 3 个空格字段，固定为 "+N,M"，避免上下文中含 + 号导致贪婪匹配出错
    new_start = $3
    sub(/^\+/, "", new_start)
    split(new_start, nums, ",")
    new_line = nums[1] + 0
    print "[hunk   ] " $0
    next
}
/^(---|\+\+\+|diff |index |new file|deleted file|old mode|new mode|similarity|rename)/ {
    in_diff = 1
    print "[meta   ] " $0
    next
}
!in_diff { print $0; next }
/^-/ {
    printf "[del    ] %s\n", $0
    next
}
/^\+/ {
    printf "[L:%-5d] %s\n", new_line, $0
    new_line++
    next
}
/^ / {
    printf "[L:%-5d] %s\n", new_line, $0
    new_line++
    next
}
{ print $0 }
'
}

if [ "$FIRST_COMMIT" = "$LAST_COMMIT" ]; then
    git show "$FIRST_COMMIT" | annotate_diff
else
    git diff "${FIRST_COMMIT}^".."$LAST_COMMIT" | annotate_diff
fi
echo ""

# 7. 输出环境变量供后续使用
echo "=== 导出环境变量 ==="
echo "export COMMIT_IDS='$COMMIT_IDS'"
echo "export FIRST_COMMIT='$FIRST_COMMIT'"
echo "export LAST_COMMIT='$LAST_COMMIT'"
echo "export COMMIT_COUNT='$COMMIT_COUNT'"
echo ""
echo "✅ 代码变更信息收集完成!"
