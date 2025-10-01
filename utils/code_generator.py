"""Code generation utility for writing actual project files to disk."""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeGenerator:
    """Handles generation and writing of code files to disk."""

    def __init__(self, base_output_dir: str = "projects"):
        """Initialize the code generator.

        Args:
            base_output_dir: Base directory where projects will be created
        """
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def create_project_directory(self, project_id: str, project_name: str) -> Path:
        """Create a project directory structure.

        Args:
            project_id: Unique project identifier
            project_name: Human-readable project name

        Returns:
            Path to the created project directory
        """
        # Sanitize project name for filesystem
        safe_name = re.sub(r"[^\w\s-]", "", project_name.lower())
        safe_name = re.sub(r"[-\s]+", "_", safe_name)

        project_dir = self.base_output_dir / f"{safe_name}_{project_id[:8]}"
        project_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created project directory: {project_dir}")
        return project_dir

    def extract_code_blocks(self, text: str) -> Dict[str, str]:
        """Extract code blocks from markdown-style text.

        Looks for patterns like:
        ```python:filename.py
        code here
        ```
        or
        **filename.py**
        ```python
        code here
        ```

        Args:
            text: Text containing code blocks

        Returns:
            Dictionary mapping filename to code content
        """
        files = {}

        # Pattern 1: ```language:filename
        pattern1 = r"```(?:\w+):([^\n]+)\n(.*?)```"
        matches1 = re.finditer(pattern1, text, re.DOTALL)
        for match in matches1:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            files[filename] = code

        # Pattern 2: **filename** followed by code block
        pattern2 = r"\*\*([^\*]+\.\w+)\*\*\s*```(?:\w+)?\n(.*?)```"
        matches2 = re.finditer(pattern2, text, re.DOTALL)
        for match in matches2:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            if filename not in files:  # Don't override pattern1 matches
                files[filename] = code

        # Pattern 3: Filename on its own line followed by code block
        # Look for filename.ext at start of line (with possible whitespace), then code block
        pattern3 = r"\n\s*([a-zA-Z0-9_\-/]+\.\w+)\s*\n\s*```(?:\w+)?\n(.*?)```"
        matches3 = re.finditer(pattern3, text, re.DOTALL)
        for match in matches3:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            if filename not in files:
                files[filename] = code

        return files

    def parse_file_structure(self, agent_output: Dict[str, Any]) -> Dict[str, str]:
        """Parse agent output to extract file structure.

        Args:
            agent_output: Agent response containing generated code

        Returns:
            Dictionary mapping file paths to content
        """
        files = {}

        # Try different keys where code might be stored
        possible_keys = [
            "response",
            "generated_code",
            "code",
            "files",
            "output",
        ]

        for key in possible_keys:
            if key in agent_output:
                content = agent_output[key]

                # If it's a dict of files, use directly
                if isinstance(content, dict) and all(
                    isinstance(v, str) for v in content.values()
                ):
                    files.update(content)

                # If it's a string, try to extract code blocks
                elif isinstance(content, str):
                    extracted = self.extract_code_blocks(content)
                    files.update(extracted)

        # Also check for fallback_code or basic_files
        if "basic_files" in agent_output:
            files.update(agent_output["basic_files"])

        return files

    def write_file(self, project_dir: Path, filepath: str, content: str) -> Path:
        """Write a single file to disk.

        Args:
            project_dir: Base project directory
            filepath: Relative path of file to write
            content: File content

        Returns:
            Path to the written file
        """
        full_path = project_dir / filepath

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        full_path.write_text(content, encoding="utf-8")

        logger.info(f"Wrote file: {full_path}")
        return full_path

    def write_files(self, project_dir: Path, files: Dict[str, str]) -> List[Path]:
        """Write multiple files to disk.

        Args:
            project_dir: Base project directory
            files: Dictionary mapping file paths to content

        Returns:
            List of paths to written files
        """
        written_files = []

        for filepath, content in files.items():
            try:
                written_path = self.write_file(project_dir, filepath, content)
                written_files.append(written_path)
            except Exception as e:
                logger.error(f"Failed to write {filepath}: {e}")

        logger.info(f"Wrote {len(written_files)} files to {project_dir}")
        return written_files

    def generate_project_from_agent_output(
        self, project_id: str, project_name: str, agent_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a complete project from agent outputs.

        Args:
            project_id: Unique project identifier
            project_name: Human-readable project name
            agent_outputs: Dictionary of agent outputs by agent name

        Returns:
            Dictionary with generation results
        """
        # Create project directory
        project_dir = self.create_project_directory(project_id, project_name)

        all_files = {}
        written_files = []

        # Parse outputs from each agent
        for agent_name, output in agent_outputs.items():
            if not isinstance(output, dict):
                continue

            files = self.parse_file_structure(output)
            all_files.update(files)

            logger.info(f"Extracted {len(files)} files from {agent_name}")

        # Write all files
        if all_files:
            written_files = self.write_files(project_dir, all_files)

        result = {
            "project_dir": str(project_dir),
            "files_generated": len(written_files),
            "file_list": [str(f.relative_to(project_dir)) for f in written_files],
            "success": len(written_files) > 0,
        }

        logger.info(
            f"Project generation complete: {len(written_files)} files in {project_dir}"
        )
        return result

    def create_default_structure(self, project_dir: Path, project_type: str = "api"):
        """Create default project structure with boilerplate files.

        Args:
            project_dir: Project directory path
            project_type: Type of project (api, web_app, etc.)
        """
        # Create standard directories
        dirs = ["src", "tests", "docs", "config"]
        for dir_name in dirs:
            (project_dir / dir_name).mkdir(exist_ok=True)

        # Create .gitignore
        gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
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

# Virtual environments
venv/
env/
ENV/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment variables
.env
.env.local

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
""".strip()

        self.write_file(project_dir, ".gitignore", gitignore_content)

        # Create basic README.md
        readme_content = f"""# Project

Generated by Multi-Agent Software Development System

## Setup

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

## Running

```bash
# Add run instructions here
```

## Testing

```bash
pytest
```
"""
        self.write_file(project_dir, "README.md", readme_content)

        logger.info(f"Created default project structure in {project_dir}")
