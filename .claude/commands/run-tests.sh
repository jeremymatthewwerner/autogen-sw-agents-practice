#!/bin/bash
# Run unit and integration tests locally
# Usage: .claude/commands/run-tests.sh

set -e

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running unit and integration tests..."
PYTHONPATH=. pytest tests/unit/ tests/integration/ -v -m "not slow" --tb=short

echo ""
echo "✅ Tests complete!"
