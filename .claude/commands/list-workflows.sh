#!/bin/bash
# List recent workflow runs with status
# Usage: .claude/commands/list-workflows.sh [workflow-name] [limit]
# Default: all workflows, last 5 runs

set -e

WORKFLOW=${1:-}
LIMIT=${2:-5}

if [ -n "$WORKFLOW" ]; then
    echo "Recent runs for workflow: $WORKFLOW"
    gh run list --workflow="$WORKFLOW" --limit $LIMIT
else
    echo "Recent workflow runs (all workflows):"
    gh run list --limit $LIMIT
fi

echo ""
echo "To watch a specific run: gh run watch <run-id>"
echo "To view logs: gh run view <run-id> --log"
