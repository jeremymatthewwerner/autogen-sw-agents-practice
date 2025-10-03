"""Project template generator for creating deployable applications."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ProjectTemplate:
    """Generates complete project templates with all necessary files."""

    @staticmethod
    def generate_fastapi_project(
        project_name: str,
        description: str,
        features: List[str] = None
    ) -> Dict[str, str]:
        """Generate a complete FastAPI project template.

        Args:
            project_name: Project name
            description: Project description
            features: List of features to include

        Returns:
            Dictionary mapping file paths to content
        """
        safe_name = project_name.lower().replace(" ", "_").replace("-", "_")
        features = features or []

        files = {}

        # Main application file
        files["main.py"] = f'''"""
{description}
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="{project_name}",
    description="{description}",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class HealthResponse(BaseModel):
    status: str
    message: str


# Routes
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint."""
    return HealthResponse(
        status="success",
        message="{project_name} is running"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Service is operational"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        # Requirements.txt
        files["requirements.txt"] = '''fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.4
python-dotenv==1.0.1
pytest==8.3.4
httpx==0.28.1
'''

        # Dockerfile
        files["Dockerfile"] = f'''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

        # .dockerignore
        files[".dockerignore"] = '''__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
.pytest_cache/
.git/
.gitignore
README.md
tests/
'''

        # README.md
        files["README.md"] = f'''# {project_name}

{description}

## Features

{chr(10).join(f"- {feature}" for feature in features) if features else "- RESTful API\\n- Health check endpoint"}

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

```bash
pytest tests/
```

## Docker

```bash
# Build image
docker build -t {safe_name} .

# Run container
docker run -p 8000:8000 {safe_name}
```

## Deployment

This application is ready to deploy to:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Apps
- Kubernetes

See deployment/ directory for configuration files.
'''

        # Test file
        files["tests/__init__.py"] = ""
        files["tests/test_main.py"] = '''"""Tests for main application."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
'''

        # GitHub Actions workflow
        files[".github/workflows/ci-cd.yml"] = f'''name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        pytest tests/ -v --tb=short

    - name: Run linting
      run: |
        pip install black flake8
        black --check .
        flake8 . --max-line-length=100

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v4

    - name: Build Docker image
      run: |
        docker build -t {safe_name}:latest .

    # Add deployment steps here based on target platform
'''

        # .env.example
        files[".env.example"] = '''# Environment variables
DEBUG=False
LOG_LEVEL=INFO
'''

        # .gitignore
        files[".gitignore"] = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
'''

        return files

    @staticmethod
    def add_database_support(files: Dict[str, str], db_type: str = "sqlite") -> Dict[str, str]:
        """Add database support to project files.

        Args:
            files: Existing project files
            db_type: Database type (sqlite, postgresql, mysql)

        Returns:
            Updated files dictionary
        """
        # Add database dependencies to requirements.txt
        if "requirements.txt" in files:
            files["requirements.txt"] += f'''
sqlalchemy==2.0.43
alembic==1.14.0
'''
            if db_type == "postgresql":
                files["requirements.txt"] += "psycopg2-binary==2.9.10\n"
            elif db_type == "mysql":
                files["requirements.txt"] += "pymysql==1.1.1\n"

        # Add database module
        files["database.py"] = f'''"""Database configuration."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={{"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {{}}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

        # Add models example
        files["models.py"] = '''"""Database models."""

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database import Base


class Item(Base):
    """Example item model."""
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
'''

        return files

    @staticmethod
    def add_authentication(files: Dict[str, str]) -> Dict[str, str]:
        """Add JWT authentication to project.

        Args:
            files: Existing project files

        Returns:
            Updated files dictionary
        """
        # Add auth dependencies
        if "requirements.txt" in files:
            files["requirements.txt"] += '''python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
'''

        # Add auth module
        files["auth.py"] = '''"""Authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    return token_data
'''

        return files
