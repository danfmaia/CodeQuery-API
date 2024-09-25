import os
import pytest
from unittest import mock
import requests
from src.ngrok_manager import start_ngrok, upload_ngrok_url_to_gateway, setup_ngrok

# Test ngrok starting successfully


@mock.patch('src.ngrok_manager.subprocess.run')
@mock.patch('src.ngrok_manager.requests.get')
def test_start_ngrok_success(mock_get, mock_subprocess):
    # Mock the subprocess call to succeed
    mock_subprocess.return_value = None

    # Mock the ngrok API response with a valid HTTPS tunnel
    mock_get.return_value.json.return_value = {
        'tunnels': [{'public_url': 'https://abc123.ngrok-free.app', 'proto': 'https'}]
    }

    ngrok_url = start_ngrok()

    assert ngrok_url == "https://abc123.ngrok-free.app"

# Test ngrok starting failure


@mock.patch('src.ngrok_manager.subprocess.run')
def test_start_ngrok_failure(mock_subprocess):
    # Simulate subprocess failure by raising an exception
    mock_subprocess.side_effect = Exception("Subprocess failed")

    # Use pytest to assert that the exception is raised
    with pytest.raises(Exception, match="Subprocess failed"):
        start_ngrok()

# Test uploading ngrok URL successfully


@mock.patch('src.ngrok_manager.requests.post')
@mock.patch.dict(os.environ, {'GATEWAY_UPLOAD_URL': 'https://your-gateway-url/ngrok-url', 'API_KEY': 'your-api-key'})
def test_upload_ngrok_url_success(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = mock.Mock()

    # Ensure that environment variables are set correctly
    assert os.getenv(
        'GATEWAY_UPLOAD_URL') == 'https://your-gateway-url/ngrok-url'
    assert os.getenv('API_KEY') == 'your-api-key'

    ngrok_url = "https://abc123.ngrok-free.app"

    # Call the function to upload the URL
    success = upload_ngrok_url_to_gateway(ngrok_url)

    # Assert that the function returned True for success
    assert success is True

    # Verify that the mock was called with the correct parameters
    mock_post.assert_called_once_with(
        'https://your-gateway-url/ngrok-url',
        json={'ngrok_url': ngrok_url},
        headers={'X-API-KEY': 'your-api-key'},
        timeout=10  # Ensure timeout is provided
    )


# Test failure to upload ngrok URL


@mock.patch('src.ngrok_manager.requests.post')
def test_upload_ngrok_url_failure(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException(
        "Request failed")

    ngrok_url = "https://abc123.ngrok-free.app"
    success = upload_ngrok_url_to_gateway(ngrok_url)

    assert success is False
    mock_post.assert_called_once()

# Test the complete ngrok setup process


@mock.patch('src.ngrok_manager.start_ngrok')
@mock.patch('src.ngrok_manager.upload_ngrok_url_to_gateway')
def test_setup_ngrok_success(mock_upload, mock_start):
    mock_start.return_value = "https://abc123.ngrok-free.app"
    mock_upload.return_value = True

    setup_ngrok()

    mock_start.assert_called_once()
    mock_upload.assert_called_once_with("https://abc123.ngrok-free.app")

# Test the setup process when ngrok fails to start


@mock.patch('src.ngrok_manager.start_ngrok')
@mock.patch('src.ngrok_manager.upload_ngrok_url_to_gateway')
def test_setup_ngrok_failure(mock_upload, mock_start):
    mock_start.return_value = None  # Simulate ngrok failing to start
    setup_ngrok()

    mock_start.assert_called_once()
    mock_upload.assert_not_called()
