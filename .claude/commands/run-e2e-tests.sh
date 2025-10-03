#!/bin/bash
# Run E2E browser tests against deployed application
# Usage: .claude/commands/run-e2e-tests.sh [environment]
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

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running E2E tests against $ENVIRONMENT ($BASE_URL)..."
E2E_BASE_URL=$BASE_URL python -m pytest tests/e2e/test_ui_workflows.py -v --tb=short

echo ""
echo "✅ E2E tests complete!"
