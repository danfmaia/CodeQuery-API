# tests/test_file_service.py

import json
import pytest
from src.app import CodeQueryAPI
from src.file_service import FileService

PROJECT_PATH = "."
AGENTIGNORE_FILE_1 = ".agentignore"


@pytest.fixture
def _client_():
    """Provides a test client for the Flask application."""
    api_instance = CodeQueryAPI()  # Create a new instance of the CodeQueryAPI class
    api_instance.app.config['TESTING'] = True
    with api_instance.app.test_client() as client:
        yield client


@pytest.fixture
def file_service_instance():
    """Provides an instance of FileService for testing."""
    return FileService(PROJECT_PATH, ".agentignore,.gitignore")


class TestFileService:
    """Test suite for the FileService class."""

    def test_filestructure(self, _client_):
        """Test the /files/structure endpoint."""
        response = _client_.get('/files/structure')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "directories" in data["."]
        assert "files" in data["."]

    def test_retrieve_single_file(self, _client_):
        """Test the /files/content endpoint with a single file."""
        response = _client_.post(
            '/files/content', json={"file_paths": ["core/src/app.py"]})
        assert response.status_code == 200

    def test_retrieve_multiple_files(self, _client_):
        """Test the /files/content endpoint with multiple files."""
        response = _client_.post(
            '/files/content', json={"file_paths": ["core/src/app.py", "core/tests/test_app.py"]})
        assert response.status_code == 200

    def test_retrieve_nonexistent_file(self, _client_):
        """Test the /files/content endpoint with a nonexistent file."""
        response = _client_.post(
            '/files/content', json={"file_paths": ["nonexistentfile.tsx"]})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_ignored_files_in_structure(self, _client_):
        """Test that directories and files listed in .agentignore are ignored by /files/structure."""
        response = _client_.get('/files/structure')
        assert response.status_code == 200
        data = json.loads(response.data)

        for folder in data:
            assert "venv/" not in data[folder]['directories']
            assert ".pytest_cache/" not in data[folder]['directories']

        assert ".agentignore" in data["."]["files"]

    def test_nested_directories_ignored(self, _client_):
        """Test that nested directories listed in .agentignore or .gitignore are ignored by /files/structure."""
        response = _client_.get('/files/structure')
        assert response.status_code == 200
        data = json.loads(response.data)

        for folder in data:
            assert "gateway/venv/" not in data[folder]['directories']
            assert "gateway/.terraform/" not in data[folder]['directories']
