#!/usr/bin/env python3
"""
Simple test script to verify multi-agent system functionality
before AWS deployment.
"""

import os
import asyncio
from dotenv import load_dotenv
from multi_agent_system import MultiAgentSystem

# Load environment variables
load_dotenv()

def test_system_locally():
    """Test the multi-agent system with a simple request."""

    print("🚀 Testing Multi-Agent System Locally")
    print("-" * 50)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in .env file")
        return False

    print("✅ API key found")

    # Initialize the system
    try:
        system = MultiAgentSystem()
        print("✅ Multi-agent system initialized")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return False

    # Test with a simple request
    project_name = "Simple To-Do API"
    test_requirements = """
    Create a simple to-do list application with the following requirements:
    - Users can add tasks
    - Users can mark tasks as complete
    - Tasks are stored in memory
    - Simple REST API with 3 endpoints
    """

    print("\n📝 Test Project:")
    print(f"Project Name: {project_name}")
    print(f"Requirements: {test_requirements}")
    print("\n🔄 Processing request through agent pipeline...")
    print("-" * 50)

    try:
        # Process the request
        result = system.develop_application(project_name, test_requirements)

        if result:
            print("\n✅ System processed request successfully!")
            print("\nProject Status:")
            print("-" * 50)

            # Display project results
            if isinstance(result, dict):
                for key, value in result.items():
                    if key == 'tasks':
                        print(f"\nTasks created: {len(value) if isinstance(value, list) else 'N/A'}")
                        if isinstance(value, list) and value:
                            for task in value[:3]:  # Show first 3 tasks
                                if isinstance(task, dict):
                                    print(f"  - {task.get('name', 'Unknown task')}: {task.get('status', 'pending')}")
                    else:
                        value_str = str(value)
                        if len(value_str) > 100:
                            print(f"{key}: {value_str[:100]}...")
                        else:
                            print(f"{key}: {value_str}")
        else:
            print("\n⚠️ System returned no results")

        print("\n" + "=" * 50)
        print("✅ Local test completed successfully!")
        print("=" * 50)

        return True

    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = test_system_locally()

    if success:
        print("\n🎉 System is ready for AWS deployment!")
        print("\nNext steps:")
        print("1. Review the AWS costs in CLAUDE.md (~$200-250/month)")
        print("2. Run ./deploy.sh to deploy to AWS")
        print("3. The script will guide you through the deployment")
    else:
        print("\n⚠️  Please fix the issues before deploying to AWS")
        print("Check that:")
        print("1. ANTHROPIC_API_KEY is set in .env")
        print("2. All dependencies are installed (uv pip freeze)")
        print("3. Virtual environment is activated")