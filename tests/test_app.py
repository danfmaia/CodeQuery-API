import os
from unittest.mock import mock_open, patch
import json
import pytest
from app import app, load_agentignore, app_config

PROJECT_PATH = "./"
AGENTIGNORE_FILE = ".agentignore"


@pytest.fixture
def _client_():
    """Provides a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_load_agentignore():
    """Test that the load_agentignore function loads patterns correctly from .agentignore."""
    mock_ignore_content = """
    # This is a comment
    venv/
    
    __pycache__/
    .git/
    # Another comment
    """

    # Reset app_config.ignored_patterns to avoid interference from previous tests
    app_config.ignored_patterns = []

    # Mock file opening and existence check
    with patch('builtins.open', mock_open(read_data=mock_ignore_content)) as mock_file:
        with patch('os.path.exists', return_value=True):
            # Call the function to load the mocked .agentignore
            load_agentignore()

            # Ensure that the file was opened correctly, with 'encoding=utf-8'
            mock_file.assert_called_once_with(
                os.path.join(PROJECT_PATH, AGENTIGNORE_FILE), 'r', encoding='utf-8')

    # Check that app_config.ignored_patterns has been loaded correctly
    assert app_config.ignored_patterns == [
        'venv/', '__pycache__/', '.git/'], "Patterns were not loaded correctly"


def test_filestructure(_client_):
    """Test the /files/structure endpoint."""
    response = _client_.get('/files/structure')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "directories" in data["."]
    assert "files" in data["."]


def test_retrieve_single_file(_client_):
    """Test the /files/content endpoint with a single file."""
    response = _client_.post(
        # Use a file that exists in your project
        '/files/content', json={"file_paths": ["app.py"]})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "app.py" in data


def test_retrieve_multiple_files(_client_):
    """Test the /files/content endpoint with multiple files."""
    response = _client_.post(
        # Use files that exist in your project
        '/files/content', json={"file_paths": ["app.py", "tests/test_src/app.py"]})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "app.py" in data
    assert "tests/test_src/app.py" in data


def test_retrieve_nonexistent_file(_client_):
    """Test the /files/content endpoint with a nonexistent file."""
    response = _client_.post(
        '/files/content', json={"file_paths": ["nonexistentfile.tsx"]})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


def test_ignored_files_in_structure(_client_):
    """Test that directories and files listed in .agentignore are ignored by /files/structure."""
    # Send a request to the /files/structure endpoint
    response = _client_.get('/files/structure')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Check that 'venv/' is ignored and not included in the file structure
    for folder in data:
        assert "venv" not in data[folder]['directories']

    # Check that '__pycache__/' is ignored and not included
    for folder in data:
        assert "src/__pycache__" not in data[folder]['directories']

    # Check that '.agentignore' is not ignored and is present in the root directory
    assert ".agentignore" in data["."]["files"]
