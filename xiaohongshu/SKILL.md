---
name: xiaohongshu
description: Deploy and use Xiaohongshu MCP service for automated posting, commenting, and interaction. Use when user wants to deploy Xiaohongshu MCP service, publish posts to Xiaohongshu automatically, comment on posts, search for content, or manage Xiaohongshu account via API.
---

# Xiaohongshu MCP Skill

This skill helps deploy and use the Xiaohongshu MCP service for automated social media interactions.

## Quick Start

### 1. Deploy MCP Service

First, download and set up the Xiaohongshu MCP service:

```bash
# Create directory
mkdir -p ~/.openclaw/mcp
cd ~/.openclaw/mcp

# Download binaries
wget https://github.com/xpzouying/xiaohongshu-mcp/releases/latest/download/xiaohongshu-mcp-linux-amd64.tar.gz
tar -xzf xiaohongshu-mcp-linux-amd64.tar.gz

# Login to Xiaohongshu
./xiaohongshu-login-linux-amd64
# Scan QR code with Xiaohongshu app to login

# Start MCP service
nohup ./xiaohongshu-mcp-linux-amd64 > mcp.log 2>&1 &
```

Service runs on `http://localhost:18060`

### 2. Verify Deployment

Check service health:

```bash
curl http://localhost:18060/health
```

Should return `{"status":"ok"}`

## Publishing Posts

### Basic Post

```bash
curl -X POST http://localhost:18060/api/v1/publish \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Post title (max 20 chars)",
    "content": "Post content",
    "images": ["/path/to/image.jpg"]
  }'
```

### Important Constraints

- **Title**: Maximum 20 characters
- **Content**: Maximum 1000 characters
- **Images**: At least 1 image required
- **Image paths**: Use absolute paths or HTTP URLs

## Commenting on Posts

### Search for Posts

```bash
curl -X POST http://localhost:18060/api/v1/feeds/search \
  -H "Content-Type: application/json" \
  -d '{"keyword":"search term"}'
```

### Add Comment

```bash
curl -X POST http://localhost:18060/api/v1/feeds/comment \
  -H "Content-Type: application/json" \
  -d '{
    "feed_id": "POST_ID",
    "xsec_token": "SECURITY_TOKEN",
    "content": "Your comment"
  }'
```

Get `feed_id` and `xsec_token` from search results.

## Troubleshooting

### Service Won't Start

```bash
# Check port
netstat -tlnp | grep 18060

# Check logs
tail -f ~/.openclaw/mcp/mcp.log

# Restart service
pkill -f xiaohongshu-mcp
cd ~/.openclaw/mcp
nohup ./xiaohongshu-mcp-linux-amd64 > mcp.log 2>&1 &
```

### Login Issues

- Delete cookies: `rm ~/.openclaw/mcp/cookies.json`
- Re-run login: `./xiaohongshu-login-linux-amd64`
- Check network connectivity

### Publish/Comment Fails

- Verify title length (≤20 chars)
- Check image path exists
- Verify cookies are valid (re-login if expired)
- Check logs for specific error messages

## Advanced Usage

See [API_REFERENCE.md](references/API_REFERENCE.md) for complete API documentation and advanced features.
