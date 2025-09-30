# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with this multi-agent software development system.

## Project Overview

This is a sophisticated Python-based multi-agent AI system that simulates an entire software development team using AutoGen framework with Anthropic Claude integration. The system orchestrates multiple specialized AI agents to collaboratively build software applications from requirements through deployment.

## Quick Setup (New Computer)

```bash
# 1. Clone repository
git clone https://github.com/jeremymatthewwerner/autogen-sw-agents-practice.git
cd autogen-sw-agents-practice

# 2. Create Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install uv package manager
pip install uv

# 4. Install all required dependencies
uv pip install pyautogen anthropic python-dotenv langchain langchain-anthropic langchain-community langgraph

# 5. Create .env file with your API key
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env

# 6. Test the installation
python hello_agents.py  # Simple demo
python multi_agent_system.py  # Full system
```

## Complete Dependency List

```python
# Core dependencies (install with uv)
pyautogen           # Multi-agent framework
anthropic          # Claude API access
python-dotenv      # Environment variable management
langchain          # AI orchestration
langchain-anthropic # Claude integration for LangChain
langchain-community # Community integrations
langgraph          # Graph-based workflows
```

## Project Structure

```
sw-agents/
├── agents/                 # Individual agent implementations
│   ├── base_agent.py      # Base class for all agents
│   ├── orchestrator.py    # Project manager agent
│   ├── requirements_agent.py  # Requirements analysis
│   ├── architect.py       # System design agent
│   ├── backend_developer.py   # Backend implementation
│   ├── qa_engineer.py     # Testing and quality assurance
│   ├── devops_engineer.py # Deployment and infrastructure
│   └── documentation_agent.py # User documentation
├── config/
│   ├── agent_config.py    # Agent configurations and prompts
│   └── llm_config.py       # Claude model configuration
├── utils/
│   ├── claude_client.py   # Claude API wrapper
│   └── logging.py         # Logging utilities
├── infrastructure/         # Cloud deployment files
│   ├── cloudformation.yaml
│   └── terraform/
├── projects/              # Generated project outputs
├── hello_agents.py        # Simple AutoGen demo
├── multi_agent_system.py  # Main orchestration system
├── test_claude_integration.py  # Claude integration tests
├── test_intelligent_agents.py  # Agent intelligence tests
└── .env                   # API keys (create this locally)
```

## Agent Roles and Responsibilities

### 1. **OrchestratorAgent** (Project Manager)
- Coordinates all other agents
- Creates project plans and task assignments
- Manages workflow between agents
- Ensures quality gates are met

### 2. **RequirementsAgent** (Business Analyst)
- Analyzes user requirements
- Creates user stories and acceptance criteria
- Estimates project complexity
- Defines success metrics

### 3. **ArchitectAgent** (System Designer)
- Designs system architecture
- Selects appropriate technologies
- Creates API specifications
- Defines database schemas

### 4. **BackendDeveloperAgent** (Implementation)
- Writes backend code
- Implements business logic
- Creates database models
- Builds API endpoints

### 5. **QAEngineerAgent** (Quality Assurance)
- Writes unit and integration tests
- Creates test plans
- Validates functionality
- Ensures code quality

### 6. **DevOpsEngineerAgent** (Infrastructure)
- Creates deployment configurations
- Sets up CI/CD pipelines
- Manages cloud infrastructure
- Handles containerization

### 7. **DocumentationAgent** (Technical Writer)
- Generates user documentation
- Creates API documentation
- Writes installation guides
- Develops troubleshooting guides

## Development Commands

### Running the System

```bash
# Activate environment
source .venv/bin/activate

# Run simple AutoGen demo
python hello_agents.py

# Run full multi-agent system
python multi_agent_system.py

# Test Claude integration
python test_claude_integration.py

# Test intelligent agents
python test_intelligent_agents.py
```

### Package Management

```bash
# Install new package
uv pip install <package-name>

# List installed packages
uv pip freeze

# Update package
uv pip install --upgrade <package-name>
```

### Git Workflow

```bash
# Check status
git status

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Description of changes"

# Push to remote
git push origin main
```

## Configuration Details

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
```

### Claude Model Configuration
- Model: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- Temperature: 0.7 for creativity, 0.3 for precision
- Max tokens: 8192 for detailed responses

### Agent Communication
- Agents communicate through structured JSON messages
- Each agent has specialized prompts in `config/agent_config.py`
- Workflow managed by orchestrator using task dependencies

## Testing Approach

Currently no formal testing framework is configured, but you can:
1. Run `test_claude_integration.py` to verify Claude connectivity
2. Run `test_intelligent_agents.py` to test agent intelligence
3. Use `hello_agents.py` for basic AutoGen functionality testing

## Important Implementation Notes

1. **No requirements.txt**: Dependencies are managed in virtual environment using `uv`
2. **API Key Security**: Never commit `.env` file to git
3. **Python Version**: Requires Python 3.11+ (tested with 3.11.13)
4. **Package Manager**: Use `uv` instead of pip for consistency
5. **Async Operations**: Agents support both sync and async operations
6. **Error Handling**: Each agent has fallback responses if Claude fails
7. **Logging**: Comprehensive logging throughout the system

## Common Tasks

### Adding a New Agent
1. Create new file in `agents/` directory
2. Extend `BaseAgent` class
3. Add configuration in `config/agent_config.py`
4. Register in `multi_agent_system.py`
5. Update orchestrator workflow if needed

### Modifying Agent Behavior
1. Edit prompts in `config/agent_config.py`
2. Adjust temperature/max_tokens in `config/llm_config.py`
3. Update agent's process_request method

### Debugging Issues
1. Check `.env` file has valid API key
2. Verify virtual environment is activated
3. Ensure all dependencies installed with `uv pip freeze`
4. Check logs for detailed error messages
5. Run test files to isolate issues

## Cloud Deployment

The system includes AWS deployment infrastructure:
- `infrastructure/cloudformation.yaml` - AWS CloudFormation template
- `deploy.sh` - Deployment script
- `Dockerfile.cloud` - Container configuration
- See `DEPLOYMENT.md` for detailed deployment instructions

## Project Status

This is an active development project demonstrating:
- Multi-agent AI orchestration
- Claude integration with AutoGen
- Automated software development workflow
- Intelligent agent communication
- Cloud-ready deployment architecture