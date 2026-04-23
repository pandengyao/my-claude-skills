#!/bin/bash
# bdpan CLI 一键安装脚本
# 自动检测平台架构并下载对应的安装器

set -e

VERSION="3.2.0"
CDN_BASE="https://issuecdn.baidupcs.com/issue/netdisk/ai-bdpan/installer/${VERSION}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Darwin)
            echo "darwin"
            ;;
        Linux)
            echo "linux"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            log_error "不支持的操作系统: $(uname -s)"
            exit 1
            ;;
    esac
}

# 检测架构
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)
            echo "amd64"
            ;;
        arm64|aarch64)
            echo "arm64"
            ;;
        *)
            log_error "不支持的架构: $(uname -m)"
            exit 1
            ;;
    esac
}

# 主函数
main() {
    local force="no"

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --yes|-y|--force|-f)
                force="yes"
                shift
                ;;
            --version|-v)
                echo "bdpan install script v${VERSION}"
                exit 0
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --yes, -y     非交互式安装（跳过确认）"
                echo "  --force, -f   强制重新安装"
                echo "  --version     显示版本信息"
                echo "  --help        显示帮助信息"
                echo ""
                echo "示例:"
                echo "  $0              # 交互式安装"
                echo "  $0 --yes        # 非交互式安装"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                echo "使用 --help 查看帮助信息"
                exit 1
                ;;
        esac
    done

    # 检测平台
    local os=$(detect_os)
    local arch=$(detect_arch)

    log_info "检测到平台: ${os}/${arch}"

    # 检查是否已安装
    if command -v bdpan &> /dev/null; then
        local current_version=$(bdpan version 2>/dev/null | head -1 || echo "unknown")
        log_warn "bdpan CLI 已安装 (版本: ${current_version})"
        if [ "$force" = "yes" ]; then
            log_info "强制重新安装..."
        else
            read -p "是否要重新安装? [y/N] " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "取消安装"
                exit 0
            fi
        fi
    fi

    # 构建安装器文件名和 URL
    local installer_name="bdpan-installer-${os}-${arch}"
    local installer_url="${CDN_BASE}/${installer_name}"

    # Windows 特殊处理
    if [ "$os" = "windows" ]; then
        installer_name="${installer_name}.exe"
        installer_url="${CDN_BASE}/${installer_name}"
    fi

    log_info "正在下载 bdpan CLI 安装器 (v${VERSION})..."
    log_info "下载地址: ${installer_url}"

    # 下载并执行安装器（使用 --yes 非交互模式）
    if command -v curl &> /dev/null; then
        curl -fsSL -O "${installer_url}"
    elif command -v wget &> /dev/null; then
        wget -q "${installer_url}"
    else
        log_error "未找到 curl 或 wget，请手动下载安装器"
        exit 1
    fi

    # 添加执行权限（非 Windows）
    if [ "$os" != "windows" ]; then
        chmod +x "${installer_name}"
    fi

    log_info "安装器下载完成，开始安装..."

    # 执行安装器（非交互模式）
    ./${installer_name} --yes

    # 清理安装器
    rm -f "${installer_name}"

    # 验证安装
    log_info "验证安装..."
    if command -v bdpan &> /dev/null; then
        local installed_version=$(bdpan version 2>/dev/null | head -1 || echo "unknown")
        log_info "✓ bdpan CLI 安装成功！(版本: ${installed_version})"
        echo ""
        echo "快速开始:"
        echo "  1. 执行登录: bdpan login"
        echo "  2. 查看帮助: bdpan --help"
        echo ""
    else
        log_error "安装失败，请检查 PATH 是否包含 ~/.local/bin"
        echo "可以手动添加: export PATH=\"\$HOME/.local/bin:\$PATH\""
        exit 1
    fi
}

# 执行主函数
main "$@"
