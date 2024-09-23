from unittest.mock import mock_open, patch
import json
import pytest
from src.app import app, load_ignore_spec


PROJECT_PATH = "./"
AGENTIGNORE_FILE_1 = ".agentignore"


@pytest.fixture
def _client_():
    """Provides a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_load_ignore_spec():
    """Test that the load_ignore_spec function loads patterns correctly from multiple ignore files."""
    mock_ignore_content_agentignore = """
    # This is a comment
    venv/
    __pycache__/
    """
    mock_ignore_content_gitignore = """
    # Another comment
    .git/
    """

    # Mock file opening for both ignore files
    with patch('builtins.open', mock_open()) as mock_file:
        # Setup different mock responses for each file
        mock_file.side_effect = [
            mock_open(read_data=mock_ignore_content_agentignore).return_value,
            mock_open(read_data=mock_ignore_content_gitignore).return_value
        ]

        with patch('os.path.exists', return_value=True):
            load_ignore_spec()

            # Assert both ignore files were opened
            mock_file.assert_any_call('.agentignore', 'r', encoding='utf-8')
            mock_file.assert_any_call('.gitignore', 'r', encoding='utf-8')


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
        # Correct the file path to match the actual project structure
        '/files/content', json={"file_paths": ["src/app.py"]})
    assert response.status_code == 200


def test_retrieve_multiple_files(_client_):
    """Test the /files/content endpoint with multiple files."""
    response = _client_.post(
        '/files/content', json={"file_paths": ["src/app.py", "tests/test_app.py"]})
    assert response.status_code == 200


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
        assert "venv/" not in data[folder]['directories']

    # Check that '.pytest_cache/' is ignored and not included
    for folder in data:
        assert ".pytest_cache/" not in data[folder]['directories']

    # Check that '.agentignore' is not ignored and is present in the root directory
    assert ".agentignore" in data["."]["files"]


def test_nested_directories_ignored(_client_):
    """Test that nested directories listed in .agentignore or .gitignore are ignored by /files/structure."""
    # Send a request to the /files/structure endpoint
    response = _client_.get('/files/structure')

    assert response.status_code == 200
    data = json.loads(response.data)

    # Check that 'gateway/venv/' is ignored and not included in the file structure
    for folder in data:
        assert "gateway/venv/" not in data[folder]['directories']

    # Check that 'gateway/.terraform/' is ignored and not included in the file structure
    for folder in data:
        assert "gateway/.terraform/" not in data[folder]['directories']
