"""E2E tests for UI workflows using Playwright."""

import pytest
import asyncio
import json
from playwright.async_api import async_playwright, expect
from unittest.mock import patch


@pytest.mark.e2e
class TestUIWorkflows:
    """End-to-end tests for the UI workflows."""

    @pytest.fixture
    async def browser(self):
        """Create browser instance for testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            yield browser
            await browser.close()

    @pytest.fixture
    async def page(self, browser):
        """Create a new page for each test."""
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await context.close()

    @pytest.fixture
    def app_url(self):
        """URL for the application."""
        # Use localhost for E2E tests
        return "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_homepage_loads(self, page, app_url):
        """Test that the homepage loads successfully."""
        await page.goto(app_url)

        # Check title
        await expect(page).to_have_title("Multi-Agent Software Development System")

        # Check main heading
        heading = page.locator("h1")
        await expect(heading).to_have_text("Multi-Agent Software Development System")

    @pytest.mark.asyncio
    async def test_agent_status_display(self, page, app_url):
        """Test that agent statuses are displayed correctly."""
        await page.goto(app_url)

        # Wait for agents container to load
        agents_container = page.locator("#agents")
        await expect(agents_container).to_be_visible()

        # Check that agent cards are displayed
        agent_cards = page.locator(".agent-card")
        await expect(agent_cards).to_have_count(6)  # We have 6 agents

        # Verify each agent has required elements
        for i in range(6):
            card = agent_cards.nth(i)

            # Check for agent name
            name = card.locator(".agent-name")
            await expect(name).to_be_visible()

            # Check for status indicator
            status = card.locator(".status-indicator")
            await expect(status).to_be_visible()

    @pytest.mark.asyncio
    async def test_development_request_form(self, page, app_url):
        """Test the development request form interaction."""
        await page.goto(app_url)

        # Find and fill the development request input
        input_field = page.locator("#taskInput")
        await expect(input_field).to_be_visible()

        # Enter a task description
        await input_field.fill("Build a simple todo list application")

        # Submit button should be visible
        submit_button = page.locator('button:has-text("Start Development")')
        await expect(submit_button).to_be_visible()

        # Check button is enabled when input has text
        await expect(submit_button).to_be_enabled()

    @pytest.mark.asyncio
    async def test_submit_development_request(self, page, app_url):
        """Test submitting a development request."""
        await page.goto(app_url)

        # Mock the API response
        await page.route(
            "**/develop",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "started",
                        "project_id": "test-123",
                        "result": "Processing your request",
                        "agents_involved": ["ProductManager", "Architect"],
                    }
                ),
            ),
        )

        # Fill and submit form
        input_field = page.locator("#taskInput")
        await input_field.fill("Build a todo app")

        submit_button = page.locator('button:has-text("Start Development")')
        await submit_button.click()

        # Check for response display (assuming there's a result area)
        # This depends on how the UI shows results
        await page.wait_for_timeout(1000)  # Wait for UI update

    @pytest.mark.asyncio
    async def test_status_polling(self, page, app_url):
        """Test that agent status is polled regularly."""
        status_call_count = 0

        async def mock_status(route):
            nonlocal status_call_count
            status_call_count += 1
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ready",
                        "agents_active": 6,
                        "agents": [
                            {
                                "name": "ProductManager",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "Architect",
                                "status": "working",
                                "current_task": "Designing",
                            },
                            {
                                "name": "BackendDeveloper",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "QAEngineer",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "DevOpsEngineer",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "DocumentationAgent",
                                "status": "ready",
                                "current_task": "",
                            },
                        ],
                    }
                ),
            )

        # Intercept status API calls
        await page.route("**/status", mock_status)

        await page.goto(app_url)

        # Wait for initial status call
        await page.wait_for_timeout(1000)

        # Wait for at least one more poll (status should update every 5 seconds)
        await page.wait_for_timeout(6000)

        # Should have made at least 2 calls (initial + 1 poll)
        assert status_call_count >= 2

    @pytest.mark.asyncio
    async def test_agent_status_visual_states(self, page, app_url):
        """Test different visual states of agent status."""
        # Mock different agent states
        await page.route(
            "**/status",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "active",
                        "agents_active": 6,
                        "agents": [
                            {
                                "name": "ProductManager",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "Architect",
                                "status": "working",
                                "current_task": "Designing system",
                            },
                            {
                                "name": "BackendDeveloper",
                                "status": "error",
                                "current_task": "Error: Build failed",
                            },
                            {
                                "name": "QAEngineer",
                                "status": "idle",
                                "current_task": "",
                            },
                            {
                                "name": "DevOpsEngineer",
                                "status": "ready",
                                "current_task": "",
                            },
                            {
                                "name": "DocumentationAgent",
                                "status": "working",
                                "current_task": "Writing docs",
                            },
                        ],
                    }
                ),
            ),
        )

        await page.goto(app_url)
        await page.wait_for_timeout(1000)

        # Check for different status classes
        ready_agents = page.locator(".agent-card.ready")
        working_agents = page.locator(".agent-card.working")
        error_agents = page.locator(".agent-card.error")

        # Verify counts based on mock data
        await expect(ready_agents).to_have_count(2)
        await expect(working_agents).to_have_count(2)
        await expect(error_agents).to_have_count(1)

    @pytest.mark.asyncio
    async def test_responsive_design(self, page, app_url):
        """Test that the UI is responsive across different screen sizes."""
        # Test desktop view
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(app_url)

        desktop_container = page.locator(".container")
        await expect(desktop_container).to_be_visible()

        # Test tablet view
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.reload()

        tablet_container = page.locator(".container")
        await expect(tablet_container).to_be_visible()

        # Test mobile view
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.reload()

        mobile_container = page.locator(".container")
        await expect(mobile_container).to_be_visible()

    @pytest.mark.asyncio
    async def test_error_handling(self, page, app_url):
        """Test error handling in the UI."""
        # Mock API error
        await page.route(
            "**/develop",
            lambda route: route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"error": "Internal Server Error"}),
            ),
        )

        await page.goto(app_url)

        # Try to submit a request
        input_field = page.locator("#taskInput")
        await input_field.fill("Test request")

        submit_button = page.locator('button:has-text("Start Development")')
        await submit_button.click()

        # Should handle error gracefully (check for error message or alert)
        # This depends on how errors are displayed in the UI
        await page.wait_for_timeout(1000)

    @pytest.mark.asyncio
    async def test_accessibility(self, page, app_url):
        """Test basic accessibility features."""
        await page.goto(app_url)

        # Check for proper heading hierarchy
        h1_elements = page.locator("h1")
        await expect(h1_elements).to_have_count(1)

        # Check for alt text on images (if any)
        images = page.locator("img")
        img_count = await images.count()
        for i in range(img_count):
            img = images.nth(i)
            alt_text = await img.get_attribute("alt")
            assert alt_text is not None and alt_text != ""

        # Check for label associations with form inputs
        input_field = page.locator("#taskInput")
        input_id = await input_field.get_attribute("id")
        label = page.locator(f'label[for="{input_id}"]')
        # Label might not exist, but input should have placeholder or aria-label
        if await label.count() == 0:
            placeholder = await input_field.get_attribute("placeholder")
            aria_label = await input_field.get_attribute("aria-label")
            assert placeholder or aria_label

    @pytest.mark.asyncio
    async def test_keyboard_navigation(self, page, app_url):
        """Test keyboard navigation through the UI."""
        await page.goto(app_url)

        # Tab to input field
        await page.keyboard.press("Tab")

        # Check if input is focused
        input_field = page.locator("#taskInput")
        await expect(input_field).to_be_focused()

        # Type in the field
        await page.keyboard.type("Test task")

        # Tab to submit button
        await page.keyboard.press("Tab")

        # Submit with Enter
        await page.keyboard.press("Enter")

    @pytest.mark.asyncio
    async def test_status_flashing_bug_regression(self, page, app_url):
        """Regression test for the agent status flashing bug."""
        status_updates = []

        async def track_status(route):
            """Track status updates to detect flashing."""
            nonlocal status_updates
            response_data = {
                "status": "ready",
                "agents_active": 6,
                "agents": [
                    {"name": "ProductManager", "status": "ready", "current_task": ""},
                    {"name": "Architect", "status": "ready", "current_task": ""},
                    {"name": "BackendDeveloper", "status": "ready", "current_task": ""},
                    {"name": "QAEngineer", "status": "ready", "current_task": ""},
                    {"name": "DevOpsEngineer", "status": "ready", "current_task": ""},
                    {
                        "name": "DocumentationAgent",
                        "status": "ready",
                        "current_task": "",
                    },
                ],
            }
            status_updates.append(response_data)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(response_data),
            )

        await page.route("**/status", track_status)
        await page.goto(app_url)

        # Wait for initial load and a few updates
        await page.wait_for_timeout(3000)

        # Check that agent cards maintain consistent state
        # (not flashing between different states)
        agent_cards = page.locator(".agent-card")

        # Take snapshots of agent states
        initial_states = []
        for i in range(6):
            card = agent_cards.nth(i)
            classes = await card.get_attribute("class")
            initial_states.append(classes)

        # Wait for another update cycle
        await page.wait_for_timeout(2000)

        # Check states again - they should be the same if no actual status change
        for i in range(6):
            card = agent_cards.nth(i)
            classes = await card.get_attribute("class")
            # States should remain consistent
            assert classes == initial_states[i], f"Agent {i} state changed unexpectedly"
