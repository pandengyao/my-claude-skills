#!/usr/bin/env bash
# San.js CR Tool 依赖校验+安装脚本
# 用途：优先检查项目本地依赖；缺失时安装到当前项目（本地 node_modules）

set -euo pipefail

NPM_REGISTRY="${NPM_REGISTRY:-http://registry.npm.baidu-int.com}"

require_cmd() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ 缺少命令: $cmd"
        exit 2
    fi
}

has_pkg_local() {
    local pkg="$1"
    [[ -f "node_modules/${pkg}/package.json" ]]
}

require_cmd "npm"
require_cmd "node"
require_cmd "npx"

echo "=== 环境信息 ==="
node -v
npm -v

echo "=== npm 配置初始化 ==="
# Do not mutate user's global npm config; keep changes in-process only.
export npm_config_proxy=
export npm_config_https_proxy=
export npm_config_registry="$NPM_REGISTRY"

declare -a TARGET_PKGS=()
if [[ $# -gt 0 ]]; then
    TARGET_PKGS=("$@")
else
    # San.js 评审所需依赖，按名称排序，便于维护
    TARGET_PKGS=(
        # san-mcp
        "@baidu/san-mcp"
        # cosmic-toolkit 及依赖包
        "@baidu/cosmic-toolkit"
        "postcss"
        "typescript"
    )
fi

echo "=== San.js CR Tool 依赖校验 ==="

declare -a MISSING_PKGS=()
for pkg in "${TARGET_PKGS[@]}"; do
    if has_pkg_local "$pkg"; then
        echo "✅ 已安装(项目本地): $pkg"
    else
        echo "❌ 缺少依赖: $pkg"
        MISSING_PKGS+=("$pkg")
    fi
done

if [[ ${#MISSING_PKGS[@]} -eq 0 ]]; then
    echo "✅ 依赖齐全，无需安装"
    exit 0
fi

echo ""
echo "=== 安装缺失依赖 ==="
echo "安装项目本地依赖: ${MISSING_PKGS[*]}"
# Avoid editing package.json/package-lock.json; we only need runtime availability in node_modules.
npm i --no-save --no-package-lock "${MISSING_PKGS[@]}" --registry="$NPM_REGISTRY"

echo ""
echo "=== 安装后复检 ==="
for pkg in "${TARGET_PKGS[@]}"; do
    if has_pkg_local "$pkg"; then
        echo "✅ 已安装(项目本地): $pkg"
    else
        echo "❌ 安装后仍缺失: $pkg"
        exit 1
    fi
done

echo "✅ San.js CR Tool 依赖已就绪"
