"""Test script to verify Claude integration works."""

import asyncio
from agents.product_manager import ProductManagerAgent


async def test_claude_integration():
    """Test that the agents can communicate with Claude."""
    print("Testing Claude integration...")

    # Create a product manager agent
    pm_agent = ProductManagerAgent()

    # Test with a simple requirements analysis request
    context = {
        "requirements": {
            "raw": "Build a simple todo app where users can add, edit, and delete tasks"
        }
    }

    try:
        # Test async version
        result = await pm_agent.process_request_async(
            "Analyze these requirements and create structured specifications", context
        )

        print(f"Agent: {result['agent']}")
        print(f"Status: {result['status']}")
        print(f"Response preview: {result['response'][:200]}...")

        return result["status"] == "success"

    except Exception as e:
        print(f"Error testing Claude integration: {e}")
        return False


def test_sync_integration():
    """Test synchronous wrapper."""
    print("Testing synchronous wrapper...")

    pm_agent = ProductManagerAgent()

    context = {"requirements": {"raw": "Build a simple todo app"}}

    try:
        result = pm_agent.process_request("Analyze these requirements briefly", context)

        print(f"Sync test - Agent: {result['agent']}, Status: {result['status']}")
        return result["status"] == "success"

    except Exception as e:
        print(f"Error in sync test: {e}")
        return False


if __name__ == "__main__":
    # Test async
    success_async = asyncio.run(test_claude_integration())
    print(f"Async test passed: {success_async}")

    # Test sync
    success_sync = test_sync_integration()
    print(f"Sync test passed: {success_sync}")

    if success_async and success_sync:
        print("✅ Claude integration working correctly!")
    else:
        print("❌ Claude integration needs debugging")
