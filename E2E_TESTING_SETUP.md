# E2E Browser Testing Setup

## Summary
Implemented comprehensive end-to-end browser testing with Playwright, integrated into CI/CD pipeline.

## What Was Fixed

### 1. Browser Test Issues
**Problem**: Tests were using `pytest.skip()` in try/except blocks, silently hiding all failures
**Solution**: 
- Removed all try/except/skip patterns
- Tests now fail loudly when something is wrong
- Increased timeouts to 30s for cloud deployments
- Fixed selectors (#swagger-ui instead of .swagger-ui)

### 2. Missing Test Coverage
**Problem**: No test for the "Unable to load agent status" error you saw
**Solution**: Added `test_agent_status_loads()` that specifically checks:
- Agent status section loads without errors
- No "Unable to load" message appears
- Agent status cards are rendered

### 3. CI/CD Integration
**Problem**: No automated browser regression tests after deployment  
**Solution**: Created two workflows:

#### e2e-browser-tests.yml (NEW - Automatic)
- Triggers automatically after successful AWS deployment
- Runs full Playwright browser test suite
- Tests against deployed cloud environment
- Uploads test results and screenshots as artifacts

#### e2e-tests.yml (Updated - Manual)
- Changed to manual dispatch only
- Removed broken local server startup
- Uses cloud AWS URL by default
- Can specify custom URL for testing

## Test Coverage

### Current Browser Tests (All Passing ✅)
1. **test_homepage_loads** - Homepage loads with correct HTML and title
2. **test_agent_status_loads** - Agent status section loads without errors
3. **test_health_endpoint** - Health endpoint returns healthy status  
4. **test_api_docs_accessible** - Swagger UI loads correctly
5. **test_list_projects_endpoint** - Projects API endpoint works
6. **test_metrics_endpoint** - Metrics API endpoint works
7. **test_cors_headers_present** - CORS headers configured
8. **test_project_creation_workflow** - Can create projects
9. **test_error_handling_invalid_project** - Error handling works
10. **test_concurrent_requests** - Handles concurrent requests
11. **test_api_openapi_spec** - OpenAPI spec available
12. **test_project_tasks_endpoint** - Project tasks endpoint works

## Running Tests Locally

```bash
# Install Playwright browsers (one-time setup)
source .venv/bin/activate
playwright install chromium

# Run against deployed environment
E2E_BASE_URL=http://multi-agent-system-alb-1995918544.us-east-1.elb.amazonaws.com \
  python -m pytest tests/e2e/test_ui_workflows.py -v

# Run specific test
E2E_BASE_URL=http://multi-agent-system-alb-1995918544.us-east-1.elb.amazonaws.com \
  python -m pytest tests/e2e/test_ui_workflows.py::TestUIWorkflows::test_agent_status_loads -v
```

## Running in CI/CD

### Automatic (After Each Deployment)
The `e2e-browser-tests.yml` workflow automatically runs after every successful deployment to AWS.

### Manual Trigger
```bash
# Run E2E tests manually against dev
gh workflow run e2e-tests.yml --field environment=dev

# Run against custom URL
gh workflow run e2e-tests.yml --field environment=dev --field base_url=http://your-url.com
```

## Dependencies

### requirements-e2e.txt
```
pytest==8.3.4
pytest-asyncio==0.25.0
playwright==1.41.2
```

## Workflow Files

### .github/workflows/e2e-browser-tests.yml
- Triggers: After successful AWS deployment
- Purpose: Automated regression testing
- Environment: Headless Chrome in CI
- Artifacts: Screenshots, test results

### .github/workflows/e2e-tests.yml  
- Triggers: Manual dispatch only
- Purpose: On-demand testing against any environment
- Can specify custom URLs

## Key Improvements

1. **No More Silent Failures**: Tests fail loudly when UI is broken
2. **Specific Regression Tests**: Agent status loading is now explicitly tested
3. **Automated Quality Gate**: Deployments are verified with real browser tests
4. **CI/CD Integration**: Browser tests run automatically after deployment
5. **Artifact Collection**: Screenshots and reports saved for debugging

## Next Steps

To add more browser tests, follow this pattern:

```python
@pytest.mark.asyncio
async def test_my_feature(self, page, app_url):
    """Test my feature description."""
    response = await page.goto(app_url, timeout=30000)
    assert response.status == 200
    
    # Wait for element
    await page.wait_for_selector("#my-element", timeout=10000)
    
    # Interact
    await page.click("#my-button")
    
    # Assert
    result = await page.text_content("#result")
    assert "expected" in result
```

## Verification

All critical UI elements are now tested with real browser automation:
- ✅ Homepage loads
- ✅ Agent status loads without errors
- ✅ API documentation accessible
- ✅ All API endpoints functional
- ✅ Error handling works
- ✅ Concurrent requests supported
