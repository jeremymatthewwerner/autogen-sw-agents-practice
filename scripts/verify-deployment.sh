#!/bin/bash
# Deployment verification script
# Tests all critical endpoints after deployment

set -e

BASE_URL="${1:-http://multi-agent-system-alb-1995918544.us-east-1.elb.amazonaws.com}"

echo "🔍 Verifying deployment at: $BASE_URL"
echo "=========================================="

# Test 1: Homepage loads HTML
echo -n "✓ Testing homepage (/)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$RESPONSE" = "200" ]; then
    CONTENT=$(curl -s "$BASE_URL/" | head -1)
    if [[ "$CONTENT" == *"<!DOCTYPE html>"* ]]; then
        echo "✅ PASS - Returns HTML"
    else
        echo "❌ FAIL - Not returning HTML"
        exit 1
    fi
else
    echo "❌ FAIL - Status $RESPONSE"
    exit 1
fi

# Test 2: Health endpoint
echo -n "✓ Testing health endpoint (/health)... "
RESPONSE=$(curl -s "$BASE_URL/health")
if echo "$RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    AGENTS=$(echo "$RESPONSE" | jq -r '.agents_registered')
    echo "✅ PASS - Healthy with $AGENTS agents"
else
    echo "❌ FAIL - Not healthy"
    exit 1
fi

# Test 3: Status endpoint (for UI)
echo -n "✓ Testing status endpoint (/status)... "
RESPONSE=$(curl -s "$BASE_URL/status")
if echo "$RESPONSE" | jq -e '.status' > /dev/null 2>&1; then
    ACTIVE=$(echo "$RESPONSE" | jq -r '.agents_active')
    echo "✅ PASS - $ACTIVE agents active"
else
    echo "❌ FAIL - No status data"
    exit 1
fi

# Test 4: API docs
echo -n "✓ Testing API docs (/docs)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$RESPONSE" = "200" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Status $RESPONSE"
    exit 1
fi

# Test 5: OpenAPI spec
echo -n "✓ Testing OpenAPI spec (/openapi.json)... "
RESPONSE=$(curl -s "$BASE_URL/openapi.json")
if echo "$RESPONSE" | jq -e '.info.title' > /dev/null 2>&1; then
    TITLE=$(echo "$RESPONSE" | jq -r '.info.title')
    echo "✅ PASS - $TITLE"
else
    echo "❌ FAIL - Invalid spec"
    exit 1
fi

# Test 6: Projects endpoint
echo -n "✓ Testing projects endpoint (/api/v1/projects)... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/projects")
if [ "$RESPONSE" = "200" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL - Status $RESPONSE"
    exit 1
fi

# Test 7: Metrics endpoint
echo -n "✓ Testing metrics endpoint (/api/v1/metrics)... "
RESPONSE=$(curl -s "$BASE_URL/api/v1/metrics")
if echo "$RESPONSE" | jq -e '.total_projects' > /dev/null 2>&1; then
    echo "✅ PASS"
else
    echo "❌ FAIL - No metrics"
    exit 1
fi

echo "=========================================="
echo "🎉 All tests passed! Deployment verified."
