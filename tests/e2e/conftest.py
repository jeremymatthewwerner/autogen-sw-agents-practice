"""E2E test configuration - isolated from main app dependencies."""

import os
import pytest


@pytest.fixture(autouse=True)
def set_e2e_environment():
    """Set environment variables for E2E testing."""
    # Only set minimal environment needed for E2E tests
    if not os.getenv("E2E_BASE_URL"):
        os.environ["E2E_BASE_URL"] = "http://localhost:8000"
    yield
