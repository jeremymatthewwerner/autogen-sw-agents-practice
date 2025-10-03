#!/bin/bash
# Test locally before committing - "Shift Left" testing approach
# This catches application bugs locally before deployment

set -e  # Exit on any error

echo "🧪 Running full local test suite..."
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# 1. Unit and Integration tests
echo "📋 Step 1/5: Running unit and integration tests..."
PYTHONPATH=. pytest tests/unit/ tests/integration/ -v -m "not slow" --tb=short
echo "✅ Unit and integration tests passed!"
echo ""

# 2. Start local server
echo "🚀 Step 2/5: Starting local server..."
uvicorn cloud_api:app --reload --port 8000 > /dev/null 2>&1 &
SERVER_PID=$!
echo "   Server PID: $SERVER_PID"
sleep 5
echo "✅ Local server started on http://localhost:8000"
echo ""

# 3. Run E2E browser tests against localhost
echo "🌐 Step 3/5: Running E2E browser tests against localhost..."
E2E_BASE_URL=http://localhost:8000 python -m pytest tests/e2e/test_ui_workflows.py -v --tb=short
echo "✅ E2E tests passed against localhost!"
echo ""

# 4. Stop local server
echo "🛑 Step 4/5: Stopping local server..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null || true
echo "✅ Local server stopped"
echo ""

# 5. Format code
echo "🎨 Step 5/5: Formatting code with Black..."
black models/ services/ tests/ utils/ agents/ *.py 2>/dev/null || true
echo "✅ Code formatted"
echo ""

echo "🎉 All local tests passed! Safe to commit and push."
echo ""
echo "Next steps:"
echo "  git add -A"
echo "  git commit -m 'Your commit message'"
echo "  git push"
