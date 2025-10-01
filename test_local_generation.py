#!/usr/bin/env python3
"""Quick test to verify code generation works locally."""

import asyncio

from multi_agent_system import MultiAgentSystem


async def test_generation():
    print("🚀 Testing local code generation...")

    system = MultiAgentSystem()

    # Test simple project generation
    print("\n📝 Creating test project...")
    result = await system.process_development_request(
        "Build a simple FastAPI with a /hello endpoint that returns 'Hello World'",
        {"project_type": "simple_api"},
    )

    print(f"\n✅ Result: {result['status']}")
    print(f"📦 Project ID: {result.get('project_id')}")

    # Check if files were generated
    import os

    projects_dir = "projects"
    if os.path.exists(projects_dir):
        project_dirs = [
            d
            for d in os.listdir(projects_dir)
            if os.path.isdir(os.path.join(projects_dir, d))
        ]
        print(f"\n📁 Found {len(project_dirs)} project directories")

        if project_dirs:
            latest = sorted(project_dirs)[-1]
            project_path = os.path.join(projects_dir, latest)
            files = []
            for root, dirs, filenames in os.walk(project_path):
                for f in filenames:
                    if f.endswith((".py", ".txt", ".json")):
                        rel_path = os.path.relpath(os.path.join(root, f), project_path)
                        files.append(rel_path)

            print(f"📄 Files in {latest}:")
            for f in files:
                print(f"   - {f}")

    print("\n✨ Test complete!")


if __name__ == "__main__":
    asyncio.run(test_generation())
