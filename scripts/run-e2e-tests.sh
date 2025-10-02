#!/bin/bash
# Script to run E2E tests against different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-"local"}
BASE_URL=${2:-""}

echo -e "${GREEN}Starting E2E Tests${NC}"
echo "Environment: $ENVIRONMENT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install Playwright browsers if needed
if ! playwright --version &> /dev/null; then
    echo -e "${YELLOW}Installing Playwright browsers...${NC}"
    playwright install chromium
fi

# Set base URL based on environment
case $ENVIRONMENT in
    "local")
        export E2E_BASE_URL=${BASE_URL:-"http://localhost:8000"}
        echo -e "${YELLOW}Testing against local server: $E2E_BASE_URL${NC}"

        # Check if local server is running
        if ! curl -f "$E2E_BASE_URL/health" &> /dev/null; then
            echo -e "${YELLOW}Local server not running. Starting it...${NC}"

            # Create test .env if it doesn't exist
            if [ ! -f .env ]; then
                echo "ANTHROPIC_API_KEY=test-key" > .env
                echo "TESTING=true" >> .env
                echo "ENVIRONMENT=dev" >> .env
            fi

            # Start server in background
            python cloud_api.py &
            SERVER_PID=$!

            # Wait for server to be ready
            echo "Waiting for server to start..."
            timeout 30 bash -c "until curl -f $E2E_BASE_URL/health &> /dev/null; do sleep 1; done" || {
                echo -e "${RED}Failed to start server${NC}"
                kill $SERVER_PID 2>/dev/null || true
                exit 1
            }

            echo -e "${GREEN}Server started successfully${NC}"
            CLEANUP_SERVER=true
        fi
        ;;
    "dev")
        export E2E_BASE_URL=${BASE_URL:-"https://api.sw-agents.dev.example.com"}
        echo -e "${YELLOW}Testing against dev: $E2E_BASE_URL${NC}"
        ;;
    "staging")
        export E2E_BASE_URL=${BASE_URL:-"https://api.sw-agents.staging.example.com"}
        echo -e "${YELLOW}Testing against staging: $E2E_BASE_URL${NC}"
        ;;
    "prod")
        export E2E_BASE_URL=${BASE_URL:-"https://api.sw-agents.prod.example.com"}
        echo -e "${RED}WARNING: Testing against production!${NC}"
        read -p "Are you sure you want to continue? (yes/no) " -n 3 -r
        echo
        if [[ ! $REPLY =~ ^yes$ ]]; then
            echo "Aborted."
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}Unknown environment: $ENVIRONMENT${NC}"
        echo "Usage: $0 [local|dev|staging|prod] [base_url]"
        exit 1
        ;;
esac

# Verify server is accessible
echo "Verifying server is accessible..."
if curl -f "$E2E_BASE_URL/health" &> /dev/null; then
    echo -e "${GREEN}Server is accessible${NC}"
else
    echo -e "${RED}Server is not accessible at $E2E_BASE_URL${NC}"
    if [ "$CLEANUP_SERVER" = true ]; then
        kill $SERVER_PID 2>/dev/null || true
    fi
    exit 1
fi

# Run the tests
echo -e "${GREEN}Running E2E tests...${NC}"
python -m pytest tests/e2e/ -v --tb=short --maxfail=3

TEST_EXIT_CODE=$?

# Cleanup
if [ "$CLEANUP_SERVER" = true ]; then
    echo "Stopping local server..."
    kill $SERVER_PID 2>/dev/null || true
fi

# Report results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}All E2E tests passed!${NC}"
else
    echo -e "${RED}E2E tests failed${NC}"
fi

exit $TEST_EXIT_CODE
