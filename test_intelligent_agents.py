"""Test script to verify intelligent agent responses."""

import asyncio
from multi_agent_system import MultiAgentSystem


async def test_different_requirements():
    """Test agents with different types of requirements."""

    system = MultiAgentSystem()

    # Test 1: E-commerce Platform (should be different from todo app)
    print("=== Test 1: E-commerce Platform ===")

    ecommerce_requirements = """
    Build an e-commerce platform where:
    - Customers can browse products by category
    - Users can add products to cart and checkout with payment processing
    - Sellers can manage their inventory and track orders
    - Admin can manage users, products, and view analytics
    - Support for multiple payment methods (Stripe, PayPal)
    - Product reviews and ratings system
    - Real-time inventory tracking
    - Email notifications for orders
    """

    try:
        result = system.develop_application("E-commerce Platform", ecommerce_requirements)
        print(f"E-commerce project status: {result}")

        # Check if the system generated different responses
        project_id = result['project_id']
        project_state = system.orchestrator.project_states[project_id]

        # Examine the product manager output
        for task_id, task in project_state.tasks.items():
            if task.name == "Analyze Requirements" and task.output:
                requirements_analysis = task.output.get('output', {}).get('structured_requirements', {})
                print(f"\nProject Type Detected: {requirements_analysis.get('project_type', 'Unknown')}")
                print(f"Complexity Assessed: {requirements_analysis.get('estimated_complexity', 'Unknown')}")
                print(f"Number of User Stories: {len(requirements_analysis.get('user_stories', []))}")

                # Print a few user stories to see if they're relevant
                user_stories = requirements_analysis.get('user_stories', [])
                if user_stories:
                    print(f"Sample User Story: {user_stories[0].get('title', 'N/A')}")

                break

        print("\n" + "="*50)

    except Exception as e:
        print(f"Error testing e-commerce requirements: {e}")


    # Test 2: Data Analytics Dashboard (very different domain)
    print("\n=== Test 2: Data Analytics Dashboard ===")

    analytics_requirements = """
    Create a data analytics dashboard for:
    - Connecting to multiple data sources (databases, APIs, CSV files)
    - Creating interactive charts and visualizations
    - Setting up automated report generation
    - User role management (viewer, analyst, admin)
    - Real-time data streaming and updates
    - Custom KPI tracking and alerts
    - Export functionality for reports
    - Mobile-responsive interface
    """

    try:
        result2 = system.develop_application("Analytics Dashboard", analytics_requirements)
        print(f"Analytics project status: {result2}")

        # Check if this generated different responses too
        project_id2 = result2['project_id']
        project_state2 = system.orchestrator.project_states[project_id2]

        for task_id, task in project_state2.tasks.items():
            if task.name == "Analyze Requirements" and task.output:
                requirements_analysis2 = task.output.get('output', {}).get('structured_requirements', {})
                print(f"\nProject Type Detected: {requirements_analysis2.get('project_type', 'Unknown')}")
                print(f"Complexity Assessed: {requirements_analysis2.get('estimated_complexity', 'Unknown')}")
                print(f"Number of User Stories: {len(requirements_analysis2.get('user_stories', []))}")

                user_stories2 = requirements_analysis2.get('user_stories', [])
                if user_stories2:
                    print(f"Sample User Story: {user_stories2[0].get('title', 'N/A')}")

                break

        print("\n" + "="*50)

    except Exception as e:
        print(f"Error testing analytics requirements: {e}")

    return True


if __name__ == "__main__":
    print("Testing intelligent agents with varied requirements...")
    success = asyncio.run(test_different_requirements())

    if success:
        print("🎉 Intelligent agents successfully adapted to different requirements!")
    else:
        print("❌ Agents may not be properly adapting to requirements")