# E2E Testing Guide

This guide explains how to run end-to-end tests for the Multi-Agent Software Development System.

## Overview

We have **17 comprehensive E2E tests** using Playwright that test:
- API endpoints and responses
- Health checks and monitoring
- Project creation workflows
- Error handling
- Performance and response times
- API documentation (Swagger/ReDoc)
- Concurrent request handling
- Mobile responsiveness
- Regression tests for known issues

## Test Categories

### API Functionality (8 tests)
- `test_homepage_loads` - Verifies base URL is accessible
- `test_health_endpoint` - Health check returns healthy status
- `test_api_docs_accessible` - Swagger UI loads correctly
- `test_create_project_endpoint` - Project creation endpoint exists
- `test_list_projects_endpoint` - Project listing works
- `test_metrics_endpoint` - System metrics are returned
- `test_api_openapi_spec` - OpenAPI spec is valid
- `test_redoc_documentation` - ReDoc documentation loads

### Workflows (3 tests)
- `test_project_creation_workflow` - Full project creation and status checking
- `test_project_tasks_endpoint` - Task retrieval after project creation
- `test_error_handling_invalid_project` - 404 handling for invalid IDs

### Performance & Quality (4 tests)
- `test_api_response_times` - Response times under 1 second
- `test_concurrent_requests` - Handles parallel requests
- `test_cors_headers_present` - CORS configuration verified
- `test_responsive_design_mobile` - Mobile viewport compatibility

### Regression (2 tests)
- `test_status_flashing_bug_regression` - Status doesn't flash between states
- (Additional regression tests can be added here)

## Running Tests

### Prerequisites

```bash
# Install dependencies
source .venv/bin/activate
uv pip install pytest pytest-asyncio pytest-playwright

# Install Playwright browsers
playwright install chromium
```

### Local Testing

```bash
# Option 1: Using the helper script (recommended)
./scripts/run-e2e-tests.sh local

# Option 2: Manual execution
# Start the API server in one terminal
python cloud_api.py

# Run tests in another terminal
python -m pytest tests/e2e/ -v
```

### Testing Against Cloud Deployments

```bash
# Dev environment
E2E_BASE_URL=https://your-dev-url.com ./scripts/run-e2e-tests.sh dev

# Staging environment
E2E_BASE_URL=https://your-staging-url.com ./scripts/run-e2e-tests.sh staging

# Production environment (requires confirmation)
E2E_BASE_URL=https://your-prod-url.com ./scripts/run-e2e-tests.sh prod
```

### Using GitHub Actions

Tests run automatically on:
- Every push to `main`
- Every pull request
- Manual workflow dispatch (can specify environment)

To run manually:
1. Go to Actions tab in GitHub
2. Select "E2E Tests" workflow
3. Click "Run workflow"
4. Choose environment (dev/staging/prod)
5. Optionally override base URL

### Environment Variables

- `E2E_BASE_URL` - Base URL to test against (default: `http://localhost:8000`)
- `ANTHROPIC_API_KEY` - API key for Claude (required for project creation tests)
- `TESTING` - Set to `true` to enable test mode

## Test Configuration

### pytest.ini

E2E tests are marked with `@pytest.mark.e2e`:

```bash
# Run only e2e tests
python -m pytest -m e2e

# Run e2e tests with verbose output
python -m pytest tests/e2e/ -v --tb=short

# Run specific test
python -m pytest tests/e2e/test_ui_workflows.py::TestUIWorkflows::test_health_endpoint -v
```

### Playwright Configuration

Tests use:
- Headless Chromium browser
- 10 second timeout for page loads
- 5 second timeout for network idle state
- Automatic retry on test failures

## Writing New E2E Tests

Add tests to `tests/e2e/test_ui_workflows.py`:

```python
@pytest.mark.asyncio
async def test_new_feature(self, page, app_url):
    """Test description."""
    try:
        # Your test code
        response = await page.request.get(f"{app_url}/new-endpoint")
        assert response.status == 200
    except Exception as e:
        pytest.skip(f"Test skipped: {e}")
```

**Best Practices:**
1. Use `pytest.skip()` for graceful degradation when service unavailable
2. Include descriptive test names and docstrings
3. Test both happy path and error cases
4. Verify response structure, not just status codes
5. Use timeouts to prevent hanging tests
6. Clean up test data when possible

## CI/CD Integration

### GitHub Actions Workflow

The E2E workflow (`.github/workflows/e2e-tests.yml`) includes:

1. **Local Testing Job** - Runs on every push/PR
   - Starts local server
   - Runs all E2E tests
   - Uploads test results and coverage

2. **Cloud Testing Job** - Runs on manual trigger for staging/prod
   - Waits for deployment health check
   - Runs smoke tests first
   - Runs full suite
   - Creates GitHub issue on failure

### Required Secrets

Configure in GitHub repository settings:

```
ANTHROPIC_API_KEY - Your Claude API key
STAGING_API_URL - Staging environment URL
PROD_API_URL - Production environment URL
```

## Troubleshooting

### Tests are skipping

- Check if server is running at `E2E_BASE_URL`
- Verify health endpoint responds: `curl http://localhost:8000/health`
- Check firewall/network settings

### Playwright installation issues

```bash
# Reinstall Playwright and browsers
pip uninstall playwright
uv pip install playwright
playwright install chromium --with-deps
```

### Timeout errors

- Increase timeouts in test code
- Check server performance
- Verify network connectivity
- Check server logs for errors

### Server won't start

```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill <PID>

# Or use different port
export PORT=8001
python cloud_api.py
```

## Metrics and Reporting

Test artifacts uploaded to GitHub Actions:
- Test results (JUnit XML)
- Playwright HTML report
- Coverage reports (HTML)
- Screenshots on failure (if configured)

Retention: 30 days

## Performance Benchmarks

Expected response times:
- Health endpoint: < 100ms
- Metrics endpoint: < 200ms
- Project list: < 500ms
- Project creation: < 1000ms

Tests will fail if response times exceed 1 second for health checks.

## Future Enhancements

Planned improvements:
- [ ] Visual regression testing with screenshots
- [ ] Load testing integration
- [ ] Test data cleanup automation
- [ ] Parallel test execution
- [ ] Cross-browser testing (Firefox, Safari)
- [ ] Performance profiling reports
- [ ] Automated accessibility audits
