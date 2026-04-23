# Xiaohongshu MCP API Reference

Complete API reference for Xiaohongshu MCP service.

## Base URL

```
http://localhost:18060
```

## Endpoints

### Health Check

Check if service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

### Publish Post

Create and publish a new post to Xiaohongshu.

**Endpoint:** `POST /api/v1/publish`

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "title": "Post title (max 20 chars)",
  "content": "Post content (max 1000 chars)",
  "images": [
    "/absolute/path/to/image.jpg",
    "https://example.com/image.jpg"
  ]
}
```

**Parameters:**
- `title` (string, required): Post title, maximum 20 characters
- `content` (string, required): Post content, maximum 1000 characters
- `images` (array, required): Array of image paths or URLs, at least 1 image required

**Success Response:**
```json
{
  "success": true,
  "data": {
    "title": "Post title",
    "content": "Post content",
    "images": 1,
    "status": "发布完成"
  },
  "message": "发布成功"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": "Detailed error information"
}
```

### Search Feeds

Search for posts on Xiaohongshu.

**Endpoint:** `POST /api/v1/feeds/search`

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "keyword": "search term"
}
```

**Parameters:**
- `keyword` (string, required): Search keyword

**Success Response:**
```json
{
  "success": true,
  "data": {
    "feeds": [
      {
        "xsecToken": "ABmwbYQ2HsHXEJd0BfJG_tIjMCJ-t0dI3wTeBVDk-4Q4E=",
        "id": "697da372000000000e03ff0d",
        "modelType": "note",
        "noteCard": {
          "type": "normal",
          "displayTitle": "Post title",
          "user": {
            "userId": "63f888f9000000001001c645",
            "nickname": "Username",
            "avatar": "https://..."
          },
          "interactInfo": {
            "liked": false,
            "likedCount": "24",
            "commentCount": "16",
            "collectedCount": "14"
          },
          "cover": {
            "urlDefault": "https://..."
          }
        }
      }
    ],
    "count": 21
  },
  "message": "搜索Feeds成功"
}
```

### Comment on Post

Add a comment to a specific post.

**Endpoint:** `POST /api/v1/feeds/comment`

**Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "feed_id": "POST_ID",
  "xsec_token": "SECURITY_TOKEN",
  "content": "Your comment"
}
```

**Parameters:**
- `feed_id` (string, required): Post ID from search results
- `xsec_token` (string, required): Security token from search results
- `content` (string, required): Comment content

**Success Response:**
```json
{
  "success": true,
  "data": {
    "feed_id": "POST_ID",
    "success": true,
    "message": "评论发表成功"
  },
  "message": "评论发表成功"
}
```

**Error Response:**
```json
{
  "error": "发表评论失败",
  "code": "POST_COMMENT_FAILED",
  "details": "未找到评论输入框，该帖子可能不支持评论或网页端不可访问: context deadline exceeded"
}
```

## Common Error Codes

- `INVALID_REQUEST`: Request parameters are invalid
- `POST_COMMENT_FAILED`: Failed to post comment (may be due to post restrictions or network issues)
- `AUTH_FAILED`: Authentication failed (cookies expired or invalid)

## Rate Limits

- Daily post limit: ~50 posts per day (recommended)
- Comment rate: No strict limit, but excessive commenting may trigger anti-spam

## Image Guidelines

- **Supported formats**: JPG, PNG, WEBP
- **File paths**: Must be absolute paths (e.g., `/home/user/image.jpg`)
- **URLs**: HTTP/HTTPS URLs are supported
- **File size**: No strict limit, but keep under 10MB for best performance
- **Avoid**: Chinese characters in file paths

## Cookies Management

Cookies are stored in `~/.openclaw/mcp/cookies.json`

**Re-login when:**
- Publish fails with authentication errors
- Cookies are expired
- You want to switch accounts

**Delete cookies:**
```bash
rm ~/.openclaw/mcp/cookies.json
```
