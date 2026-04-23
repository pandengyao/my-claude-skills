#!/bin/bash
# Comment on a Xiaohongshu post

set -e

KEYWORD="$1"
COMMENT="$2"

if [ -z "$KEYWORD" ] || [ -z "$COMMENT" ]; then
    echo "Usage: $0 \"search_keyword\" \"comment\""
    echo ""
    echo "Example:"
    echo "  $0 \"买年货\" \"哈哈，这个对比太真实了！\""
    exit 1
fi

echo "🔍 Searching for posts with keyword: $KEYWORD"

# Search for posts
SEARCH_RESPONSE=$(curl -s -X POST http://localhost:18060/api/v1/feeds/search \
  -H "Content-Type: application/json" \
  -d "{\"keyword\":\"$KEYWORD\"}")

# Get first post
FEED_ID=$(echo "$SEARCH_RESPONSE" | jq -r '.data.feeds[0].id')
XSEC_TOKEN=$(echo "$SEARCH_RESPONSE" | jq -r '.data.feeds[0].xsecToken')
TITLE=$(echo "$SEARCH_RESPONSE" | jq -r '.data.feeds[0].noteCard.displayTitle')

if [ "$FEED_ID" == "null" ] || [ "$FEED_ID" == "" ]; then
    echo "❌ No posts found for keyword: $KEYWORD"
    exit 1
fi

echo "📝 Found post: $TITLE"
echo "   Feed ID: $FEED_ID"
echo "   Comment: $COMMENT"

# Post comment
COMMENT_RESPONSE=$(curl -s -X POST http://localhost:18060/api/v1/feeds/comment \
  -H "Content-Type: application/json" \
  -d "{
    \"feed_id\": \"$FEED_ID\",
    \"xsec_token\": \"$XSEC_TOKEN\",
    \"content\": \"$COMMENT\"
  }")

# Check response
if echo "$COMMENT_RESPONSE" | jq -e '.success' > /dev/null; then
    echo "✅ Comment posted successfully!"
else
    echo "❌ Failed to post comment:"
    echo "$COMMENT_RESPONSE" | jq .
    exit 1
fi
