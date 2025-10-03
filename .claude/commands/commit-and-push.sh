#!/bin/bash
# Commit and push changes with proper formatting
# Usage: .claude/commands/commit-and-push.sh "Brief description" "Detailed explanation"

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 \"Brief description\" \"Detailed explanation\""
    echo "Example: $0 \"Fix login bug\" \"Fixed issue where login failed on Safari\""
    exit 1
fi

BRIEF="$1"
DETAIL="$2"

echo "Staging all changes..."
git add .

echo ""
echo "Creating commit..."
git commit -m "$(cat <<EOF
$BRIEF

$DETAIL

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo ""
echo "Pushing to origin main..."
git push origin main

echo ""
echo "✅ Commit and push complete!"
echo ""
echo "This will trigger CI/CD pipeline:"
echo "  1. Run unit/integration tests"
echo "  2. Deploy to AWS (if tests pass)"
echo "  3. Run E2E browser tests"
