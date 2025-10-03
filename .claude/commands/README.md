# Claude Code Commands

This directory contains reusable command scripts for common development workflows.

## Available Commands

### Testing

#### `run-tests.sh`
Run unit and integration tests locally
```bash
./.claude/commands/run-tests.sh
```

#### `run-e2e-tests.sh`
Run E2E browser tests against deployed application
```bash
./.claude/commands/run-e2e-tests.sh [dev|staging|prod]
# Default: dev
```

### CI/CD Workflows

#### `trigger-e2e-workflow.sh`
Trigger E2E Browser Tests workflow in GitHub Actions
```bash
./.claude/commands/trigger-e2e-workflow.sh [dev|staging|prod]
# Default: dev
```

#### `watch-ci.sh`
Watch the latest CI/CD workflow run
```bash
./.claude/commands/watch-ci.sh [workflow-name]
# Examples:
./.claude/commands/watch-ci.sh "E2E Browser Tests"
./.claude/commands/watch-ci.sh "Deploy Multi-Agent System to AWS"
./.claude/commands/watch-ci.sh  # watches latest run across all workflows
```

#### `list-workflows.sh`
List recent workflow runs with status
```bash
./.claude/commands/list-workflows.sh [workflow-name] [limit]
# Examples:
./.claude/commands/list-workflows.sh "E2E Browser Tests" 10
./.claude/commands/list-workflows.sh "" 20  # all workflows, last 20
```

### Deployment

#### `check-deployment.sh`
Check deployment health and status
```bash
./.claude/commands/check-deployment.sh [dev|staging|prod]
# Default: dev
```

### Git Operations

#### `commit-and-push.sh`
Commit and push changes with proper formatting
```bash
./.claude/commands/commit-and-push.sh "Brief description" "Detailed explanation"
# Example:
./.claude/commands/commit-and-push.sh \
  "Fix login bug" \
  "Fixed issue where login failed on Safari by updating cookie handling"
```

## Common Workflows

### Complete Test Cycle
```bash
# 1. Run tests locally
./.claude/commands/run-tests.sh

# 2. Commit and push (triggers CI/CD)
./.claude/commands/commit-and-push.sh "Add new feature" "Implemented user profile page"

# 3. Watch deployment
./.claude/commands/watch-ci.sh "Deploy Multi-Agent System to AWS"

# 4. Check deployment health
./.claude/commands/check-deployment.sh dev

# 5. Trigger E2E tests
./.claude/commands/trigger-e2e-workflow.sh dev

# 6. Watch E2E tests
./.claude/commands/watch-ci.sh "E2E Browser Tests"
```

### Quick Health Check
```bash
./.claude/commands/check-deployment.sh dev
```

### Run All Tests (Local + E2E)
```bash
./.claude/commands/run-tests.sh
./.claude/commands/run-e2e-tests.sh dev
```

## Environment URLs

- **Dev**: http://multi-agent-system-alb-1995918544.us-east-1.elb.amazonaws.com
- **Staging**: http://multi-agent-system-staging-alb.elb.amazonaws.com
- **Prod**: http://multi-agent-system-prod-alb.elb.amazonaws.com

## Requirements

- Python 3.11+ with virtual environment at `.venv/`
- GitHub CLI (`gh`) installed and authenticated
- `jq` for JSON parsing (deployment check)
- AWS deployment running (for E2E tests and health checks)

## Adding New Commands

1. Create a new `.sh` file in this directory
2. Make it executable: `chmod +x .claude/commands/your-command.sh`
3. Add usage documentation in this README
4. Follow the pattern of existing commands (set -e, usage examples, etc.)
