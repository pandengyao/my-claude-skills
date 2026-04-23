#!/bin/bash
# Deploy Xiaohongshu MCP service

set -e

MCP_DIR="$HOME/.openclaw/mcp"
BINARY_URL="https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-linux-amd64.tar.gz"
LOGIN_URL="https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-login-linux-amd64"

echo "🚀 Deploying Xiaohongshu MCP service..."

# Create directory
mkdir -p "$MCP_DIR"
cd "$MCP_DIR"

# Download binaries if not exist
if [ ! -f "xiaohongshu-mcp-linux-amd64" ]; then
    echo "📥 Downloading MCP binary..."
    wget "$BINARY_URL" -O xiaohongshu-mcp-linux-amd64.tar.gz
    tar -xzf xiaohongshu-mcp-linux-amd64.tar.gz
    rm xiaohongshu-mcp-linux-amd64.tar.gz
    chmod +x xiaohongshu-mcp-linux-amd64
fi

if [ ! -f "xiaohongshu-login-linux-amd64" ]; then
    echo "📥 Downloading login binary..."
    wget "$LOGIN_URL" -O xiaohongshu-login-linux-amd64
    chmod +x xiaohongshu-login-linux-amd64
fi

# Check if logged in
if [ ! -f "cookies.json" ]; then
    echo "🔐 Not logged in. Starting login process..."
    ./xiaohongshu-login-linux-amd64
    echo "✅ Login complete!"
else
    echo "✅ Already logged in (cookies found)"
fi

# Check if service is running
if pgrep -f "xiaohongshu-mcp-linux-amd64" > /dev/null; then
    echo "⚠️  Service already running. Stopping..."
    pkill -f xiaohongshu-mcp-linux-amd64
    sleep 2
fi

# Start service
echo "🚀 Starting MCP service..."
nohup ./xiaohongshu-mcp-linux-amd64 > mcp.log 2>&1 &
sleep 2

# Verify service is running
if curl -s http://localhost:18060/health > /dev/null; then
    echo "✅ MCP service deployed successfully!"
    echo "📍 Service running on: http://localhost:18060"
    echo "📝 Logs: tail -f $MCP_DIR/mcp.log"
else
    echo "❌ Service failed to start. Check logs:"
    tail -20 "$MCP_DIR/mcp.log"
    exit 1
fi
