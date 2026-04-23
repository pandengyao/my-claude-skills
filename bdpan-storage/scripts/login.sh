#!/bin/bash
# bdpan OOB 登录脚本
# 用于非 GUI 环境下的手动授权登录

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 检查 bdpan 是否已安装
if ! command -v bdpan &> /dev/null; then
    log_error "bdpan 未安装，请先运行: bash scripts/install.sh"
    exit 1
fi

# 检查当前登录状态
log_info "检查登录状态..."
if bdpan whoami &> /dev/null; then
    log_warn "已经登录，无需重复登录"
    bdpan whoami
    exit 0
fi

log_info "未登录，开始 OOB 授权流程..."

# 获取授权链接
log_info "正在获取授权链接..."

# 检查是否支持 --get-auth-url 参数
if bdpan login --help 2>/dev/null | grep -q "get-auth-url"; then
    # 新版本，支持 --get-auth-url
    AUTH_URL=$(bdpan login --get-auth-url 2>/dev/null || echo "")

    if [ -z "$AUTH_URL" ]; then
        log_error "获取授权链接失败"
        exit 1
    fi
else
    # 旧版本，尝试执行 login 捕获输出
    log_warn "当前版本可能不支持 --get-auth-url，尝试兼容模式..."
    # 这里需要根据实际 bdpan 版本调整
    log_error "请升级到支持 --get-auth-url 的 bdpan 版本"
    exit 1
fi

# 显示授权链接
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}请在浏览器中打开以下链接完成授权:${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}$AUTH_URL${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# 提示用户输入授权码
echo -n "请输入浏览器中显示的授权码: "
read -r AUTH_CODE

if [ -z "$AUTH_CODE" ]; then
    log_error "授权码不能为空"
    exit 1
fi

# 使用授权码完成登录
log_info "正在使用授权码完成登录..."

# 检查是否支持 --set-code 参数
if bdpan login --help 2>/dev/null | grep -q "set-code"; then
    bdpan login --set-code "$AUTH_CODE"
else
    log_error "当前版本不支持 --set-code"
    exit 1
fi

# 验证登录
if bdpan whoami &> /dev/null; then
    log_info "✓ 登录成功！"
    bdpan whoami
else
    log_error "登录失败，请检查授权码是否正确"
    exit 1
fi
