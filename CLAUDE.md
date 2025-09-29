# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based multi-agent AI system using the AutoGen framework with Anthropic Claude integration. The project demonstrates agent-based conversations and AI orchestration.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (using uv package manager)
uv pip install <package-name>

# List installed packages
uv pip freeze
```

### Running the Application
```bash
# Run the main agent demo
python hello_agents.py
```

Note: Ensure `ANTHROPIC_API_KEY` is set in the `.env` file before running.

## Architecture

### Core Components
- **hello_agents.py**: Main entry point demonstrating AutoGen agent setup with:
  - UserProxyAgent for human interaction
  - AssistantAgent configured with Claude 3.5 Sonnet
  - Simple conversation initiation pattern

### Key Dependencies
- **AutoGen** (`pyautogen`): Multi-agent conversation framework
- **LangChain** & **LangGraph**: Additional AI orchestration capabilities
- **Anthropic SDK**: Direct Claude API integration

### Technology Stack
- Python 3.11.13 (via Homebrew)
- Virtual environment managed with `uv` (v0.8.22)
- Environment variables managed via `.env` file (using python-dotenv)

## Important Notes

- No testing framework is currently configured
- API keys are stored in `.env` file (excluded from git)
- Project uses `uv` as the primary package manager instead of pip
- No requirements.txt file exists - dependencies are managed in the virtual environment