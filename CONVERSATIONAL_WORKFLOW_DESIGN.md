# Conversational Project Workflow Design

## Overview
Transform the multi-agent system into a conversational development assistant where users can iteratively refine applications through natural language.

**Alignment with PRD:**
- ✅ Section 4.1: Iterative refinement through clarification dialogues
- ✅ Section 5.2: Persistent state management across sessions
- ✅ Section 4.4: Real-time visibility and progress tracking
- ✅ Section 6.1: Project-specific context and decisions

**Project Standards Compliance:**
- Every generated project must have CI/CD pipeline
- Unit + Integration + E2E tests (if UI)
- Deploy to cloud automatically
- Full verification before declaring success

## User Experience Flow

### 1. Initial Project Creation
```
User: "Build me a task management API"
System:
  → ProductManager analyzes requirements
  → Architect designs system
  → Shows plan and asks for confirmation/changes
User: "Add user authentication"
System:
  → Updates requirements
  → Revises architecture
  → Shows updated plan
User: "Looks good, build it"
System:
  → BackendDeveloper writes code
  → QA writes tests and runs them
  → DevOps creates deployment config
  → Actually deploys to cloud
  → Returns deployment URL
```

### 2. Project Refinement
```
User: [selects existing project]
User: "Add a feature to export tasks to CSV"
System:
  → Loads project context
  → Updates code
  → Re-runs tests
  → Redeploys
  → Returns updated deployment URL
```

## Technical Architecture

### Database Schema
```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deployment_url VARCHAR(500),
    git_repo_url VARCHAR(500)
);

-- Conversations table (thread per project)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    role VARCHAR(20),  -- 'user' or 'assistant'
    content TEXT,
    metadata JSONB,  -- agent responses, file changes, etc.
    created_at TIMESTAMP
);

-- Project artifacts (generated code, configs, etc.)
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    type VARCHAR(50),  -- 'code', 'test', 'config', 'deployment'
    path VARCHAR(500),
    content TEXT,
    version INT,
    created_at TIMESTAMP
);
```

### API Endpoints

```python
# Conversational endpoints
POST   /api/projects/create          # Create new project from description
GET    /api/projects                  # List all projects
GET    /api/projects/{id}            # Get project details
POST   /api/projects/{id}/message    # Send message to project (refine/iterate)
GET    /api/projects/{id}/conversation  # Get conversation history
DELETE /api/projects/{id}            # Delete project

# Deployment endpoints
POST   /api/projects/{id}/deploy     # Deploy project
GET    /api/projects/{id}/deployment # Get deployment status
GET    /api/projects/{id}/logs       # Get deployment logs
```

### Agent Workflow Enhancement

#### Current (Fire-and-Forget)
```
User request → Create project → Execute tasks → Done
```

#### New (Conversational)
```
User message → Load/Create project →
  ↓
  Orchestrator decides intent:
    - NEW: Requirements gathering (ProductManager)
    - REFINE: Code changes (BackendDeveloper)
    - TEST: QA execution
    - DEPLOY: DevOps deployment
    - QUESTION: Answer from context
  ↓
  Execute agent(s) →
  ↓
  Update project artifacts →
  ↓
  Return response with:
    - What changed
    - Test results
    - Deployment status
    - Next steps/questions
```

## Implementation Plan

### Phase 1: Conversational Infrastructure
1. Add PostgreSQL for project/conversation persistence
2. Create conversation API endpoints
3. Update UI with project selector and chat interface
4. Store all agent interactions in conversation history

### Phase 2: Real Code Generation
1. Enhance CodeGenerator to create full project structure
2. Generate requirements.txt, Dockerfile, tests
3. Initialize git repo for each project
4. Commit changes with each iteration

### Phase 3: Real Deployment
1. DevOps agent creates:
   - Dockerfile
   - GitHub Actions workflow
   - Terraform/CloudFormation for AWS
2. Auto-deploy to isolated environment per project
3. Return deployment URL to user

### Phase 4: Real Testing
1. QA agent generates pytest tests
2. Actually runs tests using subprocess
3. Reports failures to user
4. Can iterate to fix test failures

### Phase 5: Refinement Loop
1. User can select existing project
2. Send messages like "add feature X"
3. System loads context and makes incremental changes
4. Redeploys automatically
5. Full conversation history preserved

## UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│ Multi-Agent Development System                          │
├─────────────────┬───────────────────────────────────────┤
│ My Projects     │ Project: Task Management API          │
│                 │ Status: ✓ Deployed                    │
│ ✓ Task Mgmt API │ URL: https://task-api-abc.aws.com    │
│   Todo App      │                                       │
│   Blog Platform │ ┌───────────────────────────────────┐ │
│ + New Project   │ │ Conversation                      │ │
│                 │ │                                   │ │
│                 │ │ User: Build a task management API │ │
│                 │ │                                   │ │
│                 │ │ Assistant: I'll help you build... │ │
│                 │ │ [Architecture diagram]            │ │
│                 │ │                                   │ │
│                 │ │ User: Add CSV export              │ │
│                 │ │                                   │ │
│                 │ │ Assistant: Added CSV export...    │ │
│                 │ │ Tests: ✓ 12/12 passing           │ │
│                 │ │ Deployed: task-api-abc.aws.com   │ │
│                 │ └───────────────────────────────────┘ │
│                 │                                       │
│                 │ [Type your message...]        [Send]  │
└─────────────────┴───────────────────────────────────────┘
```

## Key Differentiators

1. **Stateful**: Projects persist and can be refined
2. **Conversational**: Natural back-and-forth dialogue
3. **Real Output**: Actual deployed applications, not just plans
4. **Testable**: Tests written and executed automatically
5. **Iterative**: Easy to add features/fix bugs through chat
6. **Transparent**: Full history of all changes and decisions

## Success Criteria

1. User can describe an app and get a working deployment URL
2. User can refine app through multiple messages
3. All code changes are tested before deployment
4. Each project gets isolated cloud resources
5. Full conversation history accessible
6. Projects can be deleted (including cloud resources)
