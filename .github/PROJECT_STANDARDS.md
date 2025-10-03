# Project Standards and Learnings

## Critical Requirements for All Projects

### 1. CI/CD Pipeline (ALWAYS)
- **Test before merge**: All PRs must pass tests
- **Automated deployment**: Deploy on merge to main
- **Quality gates**: Linting, security scanning, unit tests
- **No manual deployments**: Everything through CI/CD

### 2. Comprehensive Testing (ALWAYS)
**Unit Tests**
- Test all business logic
- Mock external dependencies
- Fast execution (< 1 second per test)
- Run on every commit

**Integration Tests**
- Test component interactions
- Use real dependencies when possible
- Run before deployment

**E2E Tests (if UI exists)**
- **Real browser automation** (Playwright)
- Test actual user workflows
- Run against deployed environment
- **CRITICAL**: Verify tests actually pass in CI before declaring success

### 3. Cloud-Based Everything
- **Build in cloud**: Never "works on my machine"
- **Test in cloud**: Same environment as production
- **Deploy to cloud**: No local deployments

## Hard-Learned Lessons

### Never Declare Victory Without Verification
**Problem**: Claimed E2E tests were working without running them in CI
**Impact**: User found multiple failures
**Solution**: Always verify the full pipeline end-to-end

**Checklist before saying "done":**
- [ ] Tests pass locally
- [ ] Tests pass in CI/CD
- [ ] Deployment succeeds
- [ ] Deployed app actually works
- [ ] E2E tests pass against deployed app
- [ ] User can verify it works

### Test The Basics
**Problem**: Said UI was working, but user found:
1. Root URL returned 404
2. Agent status showed "Unable to load"

**Solution**: Always manually verify:
- [ ] Homepage loads
- [ ] All UI sections load without errors
- [ ] API endpoints return expected data
- [ ] No console errors

### E2E Testing Gotchas
**Playwright in CI requires:**
1. Correct Ubuntu version (22.04, not 24.04 - libasound2 issue)
2. `python -m playwright install --with-deps chromium`
3. Isolate E2E tests from application dependencies
4. Use `--ignore` for conftest.py if it imports app code
5. Set proper base URL via environment variable

### Test Organization
```
tests/
├── unit/           # Fast, isolated, no external deps
├── integration/    # Component interactions
└── e2e/           # Browser tests, standalone, minimal deps
    └── test_ui_workflows.py  # Should NOT import from agents/
```

### CI/CD Workflow Structure
```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-22.04
    # Install all dependencies, run fast tests
  
  build-and-deploy:
    needs: unit-tests
    # Build, push to registry, deploy to cloud
  
  e2e-tests:
    needs: build-and-deploy
    runs-on: ubuntu-22.04
    # Run browser tests against deployed app
    # Use playwright install --with-deps
    # Ignore conftest.py if needed
```

## Testing Anti-Patterns to Avoid

### 1. Silent Test Failures
```python
# BAD
try:
    await page.goto(url)
    assert page.title == "Expected"
except Exception as e:
    pytest.skip(f"Test skipped: {e}")

# GOOD
await page.goto(url, timeout=30000)
assert page.title == "Expected"
```

### 2. Testing Only APIs, Not UI
```python
# BAD - Only testing with curl
curl http://localhost/health

# GOOD - Testing with real browser
await page.goto(base_url)
await page.wait_for_selector("#agent-status")
agent_text = await page.text_content("#agent-status")
assert "Unable to load" not in agent_text
```

### 3. Declaring Success Too Early
```python
# BAD
print("✅ All tests pass!")  # Only ran locally

# GOOD
# 1. Run locally
# 2. Push to CI
# 3. Wait for CI to complete
# 4. Verify deployed app works
# 5. THEN declare success
```

## Standard Project Setup

### Required Files
```
.github/workflows/
├── ci-cd.yml              # Unit tests, linting, security
├── deploy.yml             # Build and deploy to cloud
└── e2e-tests.yml          # Browser tests post-deployment

tests/
├── unit/
├── integration/
└── e2e/
    └── test_ui_workflows.py

requirements.txt           # Main dependencies
requirements-dev.txt       # Development dependencies
requirements-e2e.txt       # Minimal E2E dependencies (pytest, playwright)
pytest.ini                 # pytest configuration
.gitignore                 # Ignore build artifacts, secrets
README.md                  # Setup instructions
```

### Deployment Checklist
- [ ] Tests pass in CI
- [ ] Build succeeds
- [ ] Image pushed to registry
- [ ] Deployed to environment
- [ ] Health check passes
- [ ] E2E tests pass against deployment
- [ ] Manual smoke test of critical flows
- [ ] Verify with user before declaring done

## Key Takeaways

1. **Trust but verify**: Run the full pipeline, don't assume it works
2. **Test like a user**: Use real browsers, test actual UI
3. **Fail fast, fail loud**: No silent test skips
4. **Cloud-first**: Everything builds and runs in cloud environment
5. **Complete the loop**: Don't stop until user confirms it works

---
*Last updated: 2025-10-03*
*These standards evolved from real project issues and user feedback*
