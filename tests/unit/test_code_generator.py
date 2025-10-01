"""Unit tests for the CodeGenerator utility."""

import tempfile
from pathlib import Path

import pytest

from utils.code_generator import CodeGenerator


class TestCodeGenerator:
    """Test suite for CodeGenerator class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def code_generator(self, temp_dir):
        """Create a CodeGenerator instance with temp directory."""
        return CodeGenerator(base_output_dir=temp_dir)

    def test_create_project_directory(self, code_generator, temp_dir):
        """Test creating a project directory."""
        project_id = "test-123"
        project_name = "Test Project"

        project_dir = code_generator.create_project_directory(project_id, project_name)

        assert project_dir.exists()
        assert project_dir.is_dir()
        assert "test_project" in str(project_dir)

    def test_extract_code_blocks_pattern1(self, code_generator):
        """Test extracting code blocks with pattern: ```language:filename"""
        text = """
        Here is a file:
        ```python:main.py
        print("Hello World")
        ```
        """

        files = code_generator.extract_code_blocks(text)

        assert "main.py" in files
        assert 'print("Hello World")' in files["main.py"]

    def test_extract_code_blocks_pattern2(self, code_generator):
        """Test extracting code blocks with pattern: **filename**"""
        text = """
        **app.py**
        ```python
        def main():
            pass
        ```
        """

        files = code_generator.extract_code_blocks(text)

        assert "app.py" in files
        assert "def main():" in files["app.py"]

    def test_extract_code_blocks_pattern3(self, code_generator):
        """Test extracting code blocks with pattern: filename on its own line."""
        text = """
        models.py
        ```python
        class User:
            pass
        ```
        """

        files = code_generator.extract_code_blocks(text)

        assert "models.py" in files
        assert "class User:" in files["models.py"]

    def test_extract_multiple_files(self, code_generator):
        """Test extracting multiple files from text."""
        text = """
        **main.py**
        ```python
        print("main")
        ```

        **config.py**
        ```python
        DEBUG = True
        ```
        """

        files = code_generator.extract_code_blocks(text)

        assert len(files) == 2
        assert "main.py" in files
        assert "config.py" in files

    def test_parse_file_structure_from_dict(self, code_generator):
        """Test parsing file structure from dict output."""
        agent_output = {
            "files": {
                "main.py": "print('hello')",
                "test.py": "def test(): pass",
            }
        }

        files = code_generator.parse_file_structure(agent_output)

        assert len(files) == 2
        assert "main.py" in files
        assert "test.py" in files

    def test_parse_file_structure_from_string(self, code_generator):
        """Test parsing file structure from string with code blocks."""
        agent_output = {
            "response": """
            **main.py**
            ```python
            def main():
                print("test")
            ```
            """
        }

        files = code_generator.parse_file_structure(agent_output)

        assert "main.py" in files
        assert "def main():" in files["main.py"]

    def test_write_file(self, code_generator, temp_dir):
        """Test writing a single file."""
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()

        content = "print('hello world')"
        written_path = code_generator.write_file(project_dir, "main.py", content)

        assert written_path.exists()
        assert written_path.read_text() == content

    def test_write_file_with_subdirectory(self, code_generator, temp_dir):
        """Test writing a file in a subdirectory."""
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()

        content = "def test(): pass"
        written_path = code_generator.write_file(
            project_dir, "tests/test_main.py", content
        )

        assert written_path.exists()
        assert (project_dir / "tests").exists()
        assert written_path.read_text() == content

    def test_write_files(self, code_generator, temp_dir):
        """Test writing multiple files."""
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()

        files = {
            "main.py": "print('main')",
            "config.py": "DEBUG=True",
            "tests/test_main.py": "def test(): pass",
        }

        written_paths = code_generator.write_files(project_dir, files)

        assert len(written_paths) == 3
        assert (project_dir / "main.py").exists()
        assert (project_dir / "config.py").exists()
        assert (project_dir / "tests" / "test_main.py").exists()

    def test_generate_project_from_agent_output(self, code_generator, temp_dir):
        """Test generating a complete project from agent outputs."""
        agent_outputs = {
            "BackendDeveloper": {
                "response": """
                **main.py**
                ```python
                from fastapi import FastAPI
                app = FastAPI()
                ```

                **requirements.txt**
                ```
                fastapi==0.104.1
                ```
                """
            }
        }

        result = code_generator.generate_project_from_agent_output(
            "test-123", "Test Project", agent_outputs
        )

        assert result["success"]
        assert result["files_generated"] == 2
        assert "main.py" in result["file_list"]
        assert "requirements.txt" in result["file_list"]

        # Check files actually exist
        project_dir = Path(result["project_dir"])
        assert (project_dir / "main.py").exists()
        assert (project_dir / "requirements.txt").exists()

    def test_create_default_structure(self, code_generator, temp_dir):
        """Test creating default project structure."""
        project_dir = Path(temp_dir) / "test_project"
        project_dir.mkdir()

        code_generator.create_default_structure(project_dir)

        # Check directories exist
        assert (project_dir / "src").exists()
        assert (project_dir / "tests").exists()
        assert (project_dir / "docs").exists()
        assert (project_dir / "config").exists()

        # Check default files exist
        assert (project_dir / ".gitignore").exists()
        assert (project_dir / "README.md").exists()

        # Check content
        gitignore_content = (project_dir / ".gitignore").read_text()
        assert "__pycache__" in gitignore_content
        assert ".env" in gitignore_content

    def test_sanitize_project_name(self, code_generator, temp_dir):
        """Test that project names are properly sanitized."""
        project_id = "test-123"
        project_name = "My Project! With @ Special #Characters"

        project_dir = code_generator.create_project_directory(project_id, project_name)

        # Should not contain special characters
        dir_name = project_dir.name
        assert "@" not in dir_name
        assert "!" not in dir_name
        assert "#" not in dir_name
        assert "_" in dir_name  # Spaces should be converted to underscores
