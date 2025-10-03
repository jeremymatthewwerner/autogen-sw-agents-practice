#!/bin/bash
# Check deployment health and status
# Usage: .claude/commands/check-deployment.sh [environment]
# Default environment: dev

set -e

ENVIRONMENT=${1:-dev}

case $ENVIRONMENT in
  dev)
    BASE_URL="http://multi-agent-system-alb-1995918544.us-east-1.elb.amazonaws.com"
    ;;
  staging)
    BASE_URL="http://multi-agent-system-staging-alb.elb.amazonaws.com"
    ;;
  prod)
    BASE_URL="http://multi-agent-system-prod-alb.elb.amazonaws.com"
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    echo "Usage: $0 [dev|staging|prod]"
    exit 1
    ;;
esac

echo "Checking deployment health for $ENVIRONMENT environment..."
echo "URL: $BASE_URL"
echo ""

echo "=== Health Check ==="
curl -s $BASE_URL/health | jq '.'

echo ""
echo "=== HTTP Status Codes ==="
echo -n "Root (/)         : "
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/
echo ""
echo -n "Health           : "
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/health
echo ""
echo -n "Agent Status     : "
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/status
echo ""
echo -n "API Docs         : "
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/docs
echo ""

echo ""
echo "✅ Deployment check complete!"
