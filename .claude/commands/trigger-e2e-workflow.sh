#!/bin/bash
# Trigger E2E Browser Tests workflow in GitHub Actions
# Usage: .claude/commands/trigger-e2e-workflow.sh [environment]
# Default environment: dev

set -e

ENVIRONMENT=${1:-dev}

echo "Triggering E2E Browser Tests workflow for $ENVIRONMENT environment..."
gh workflow run "E2E Browser Tests" --field environment=$ENVIRONMENT

echo ""
echo "Waiting for workflow to start..."
sleep 3

echo ""
echo "Latest workflow run:"
gh run list --workflow="E2E Browser Tests" --limit 1

echo ""
echo "To watch the workflow:"
echo "  gh run watch \$(gh run list --workflow='E2E Browser Tests' --limit 1 --json databaseId -q '.[0].databaseId')"
