#!/bin/bash
# Publish a post to Xiaohongshu

set -e

TITLE="$1"
CONTENT="$2"
IMAGE="$3"

if [ -z "$TITLE" ] || [ -z "$CONTENT" ] || [ -z "$IMAGE" ]; then
    echo "Usage: $0 \"title\" \"content\" \"image_path\""
    echo ""
    echo "Example:"
    echo "  $0 \"买年货啦！\" \"快过年了，大家都开始准备年货了吗？\" \"/path/to/image.jpg\""
    exit 1
fi

# Validate title length
if [ ${#TITLE} -gt 20 ]; then
    echo "❌ Error: Title must be 20 characters or less (current: ${#TITLE})"
    exit 1
fi

# Validate image exists
if [ ! -f "$IMAGE" ] && [[ ! "$IMAGE" =~ ^https?:// ]]; then
    echo "❌ Error: Image file not found: $IMAGE"
    exit 1
fi

echo "📝 Publishing post..."
echo "   Title: $TITLE (${#TITLE}/20 chars)"
echo "   Content: ${CONTENT:0:100}..."
echo "   Image: $IMAGE"

# Publish
RESPONSE=$(curl -s -X POST http://localhost:18060/api/v1/publish \
  -H "Content-Type: application/json" \
  -d "{
    \"title\": \"$TITLE\",
    \"content\": \"$CONTENT\",
    \"images\": [\"$IMAGE\"]
  }")

# Check response
if echo "$RESPONSE" | jq -e '.success' > /dev/null; then
    echo "✅ Post published successfully!"
    echo "$RESPONSE" | jq .
else
    echo "❌ Failed to publish post:"
    echo "$RESPONSE" | jq .
    exit 1
fi
