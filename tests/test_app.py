import pytest
from src.app import app  # Import your Flask app here
import json

# Fixture to provide the test client


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_filestructure(client):
    """Test the /filestructure endpoint."""
    response = client.get('/filestructure')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "directories" in data["."]
    assert "files" in data["."]


def test_retrieve_single_file(client):
    """Test the /retrievefiles endpoint with a single file."""
    response = client.post('/retrievefiles', json={"file_paths": ["App.tsx"]})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "App.tsx" in data


def test_retrieve_multiple_files(client):
    """Test the /retrievefiles endpoint with multiple files."""
    response = client.post(
        '/retrievefiles', json={"file_paths": ["App.tsx", "components/Header.tsx"]})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "App.tsx" in data
    assert "components/Header.tsx" in data


def test_retrieve_nonexistent_file(client):
    """Test the /retrievefiles endpoint with a nonexistent file."""
    response = client.post(
        '/retrievefiles', json={"file_paths": ["nonexistentfile.tsx"]})
    assert response.status_code == 404  # Assuming you return 404 for missing files
    data = json.loads(response.data)
    assert "error" in data


def test_retrieve_mixed_files(client):
    """Test the /retrievefiles endpoint with a mix of existing and nonexistent files."""
    response = client.post(
        '/retrievefiles', json={"file_paths": ["App.tsx", "nonexistentfile.tsx"]})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "App.tsx" in data
    # Assuming you handle errors per file
    assert "error" in data["nonexistentfile.tsx"]
