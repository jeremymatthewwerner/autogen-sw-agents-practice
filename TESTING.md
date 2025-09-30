# Testing Documentation

## Overview

This multi-agent system employs a comprehensive testing strategy to ensure code quality, catch regressions, and maintain system reliability. Our testing approach follows the testing pyramid principle with unit tests at the base, integration tests in the middle, and E2E tests at the top.

## Testing Strategy

### 1. Unit Tests
- **Location**: `tests/unit/`
- **Coverage Target**: 80%+
- **Purpose**: Test individual components in isolation
- **Key Test Files**:
  - `test_base_agent.py`: Tests base agent functionality
  - `test_orchestrator.py`: Tests orchestrator coordination logic
  - `test_multi_agent_system.py`: Tests main system coordinator
  - `test_project_state.py`: Tests project state management

### 2. Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test API endpoints and component interactions
- **Key Test Files**:
  - `test_api_endpoints.py`: Tests FastAPI endpoints

### 3. E2E Tests
- **Location**: `tests/e2e/`
- **Framework**: Playwright
- **Purpose**: Test complete user workflows through the UI
- **Key Test Files**:
  - `test_ui_workflows.py`: Tests UI interactions and agent status updates

## Running Tests

### Using Makefile

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# Run tests with coverage
make coverage

# Clean test artifacts
make clean
```

### Using pytest directly

```bash
# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v -m integration

# Run E2E tests (requires running app)
python app.py &
pytest tests/e2e/ -v -m e2e

# Run with coverage
pytest --cov=agents --cov=utils --cov=multi_agent_system --cov-report=html
```

## CI/CD Pipeline

Our GitHub Actions workflow (`.github/workflows/ci-cd.yml`) automatically runs:

1. **On Every Push/PR**:
   - Unit tests with coverage reporting
   - Integration tests
   - Code quality checks (Black, isort, flake8)
   - Security scanning

2. **On Main Branch**:
   - E2E tests
   - Docker image build
   - Deployment to AWS ECS

## Pre-commit Hooks

Install pre-commit hooks to run tests before committing:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run:
- Code formatting (Black, isort)
- Linting (flake8)
- Unit tests
- Basic file checks

## Test Coverage

Current coverage requirements:
- Minimum: 80% overall
- Critical paths: 90%+

View coverage report:
```bash
make coverage
open htmlcov/index.html
```

## Regression Testing

### Agent Status Flashing Bug
We have a specific regression test (`test_status_flashing_bug_regression`) in the E2E suite that verifies agent statuses don't flash between states unexpectedly. This test:
1. Monitors status API calls
2. Tracks DOM changes
3. Ensures consistent state representation

## Mocking Strategy

- **Unit Tests**: Mock all external dependencies (APIs, databases)
- **Integration Tests**: Mock only external services (Claude API)
- **E2E Tests**: Mock API responses for predictable testing

## Test Data

Test fixtures are defined in `tests/conftest.py`:
- Mock agent instances
- Sample project requirements
- API response templates

## Debugging Tests

```bash
# Run with verbose output
pytest -vvv tests/unit/test_base_agent.py

# Run specific test
pytest tests/unit/test_base_agent.py::TestBaseAgent::test_agent_initialization

# Run with debugging
pytest --pdb tests/unit/

# Show print statements
pytest -s tests/unit/
```

## Performance Testing

While not currently implemented, future performance tests should cover:
- Agent response times
- API endpoint latency
- UI rendering performance
- Concurrent request handling

## Adding New Tests

1. **Unit Test**: Test individual functions/methods
   ```python
   def test_new_feature(self):
       # Arrange
       instance = MyClass()
       # Act
       result = instance.my_method()
       # Assert
       assert result == expected
   ```

2. **Integration Test**: Test API endpoints
   ```python
   def test_new_endpoint(self, client):
       response = client.get("/new-endpoint")
       assert response.status_code == 200
   ```

3. **E2E Test**: Test user workflows
   ```python
   async def test_user_workflow(self, page, app_url):
       await page.goto(app_url)
       await page.click("#button")
       await expect(page.locator("#result")).to_be_visible()
   ```

## Best Practices

1. **Keep tests independent**: Each test should be able to run in isolation
2. **Use descriptive names**: Test names should clearly describe what they test
3. **Follow AAA pattern**: Arrange, Act, Assert
4. **Mock external dependencies**: Don't make real API calls in tests
5. **Test edge cases**: Include tests for error conditions and boundary values
6. **Maintain test coverage**: Ensure new code includes tests
7. **Regular test execution**: Run tests frequently during development

## Known Issues

- E2E tests require the application to be running locally
- Some async tests may have timing issues on slower machines
- Playwright tests require Chromium to be installed

## Future Improvements

- [ ] Add performance benchmarking tests
- [ ] Implement mutation testing
- [ ] Add visual regression testing for UI
- [ ] Set up test environment in AWS for E2E tests
- [ ] Add load testing for API endpoints
- [ ] Implement contract testing for agent interfaces