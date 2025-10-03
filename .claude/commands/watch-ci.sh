#!/bin/bash
# Watch the latest CI/CD workflow run
# Usage: .claude/commands/watch-ci.sh [workflow-name]
# Default: watches latest run across all workflows

set -e

if [ -n "$1" ]; then
    echo "Watching latest run for workflow: $1"
    RUN_ID=$(gh run list --workflow="$1" --limit 1 --json databaseId -q '.[0].databaseId')
else
    echo "Watching latest workflow run..."
    RUN_ID=$(gh run list --limit 1 --json databaseId -q '.[0].databaseId')
fi

if [ -z "$RUN_ID" ]; then
    echo "No workflow runs found"
    exit 1
fi

echo "Run ID: $RUN_ID"
echo ""
gh run watch $RUN_ID
