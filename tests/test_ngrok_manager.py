# pylint: disable=C0116
import os
from unittest import mock
import responses
import pytest
import requests
from src.ngrok_manager import NgrokManager


class TestNgrokManager:
    """
    Test suite for NgrokManager class, focusing on ngrok setup, URL uploads, and status checks.
    """

    def setup_method(self):
        """
        Setup method that runs before each test.
        Creates a new instance of the NgrokManager class.
        """
        self.ngrok_manager = NgrokManager()  # pylint: disable=W0201

    @mock.patch('src.ngrok_manager.subprocess.run')
    @mock.patch('src.ngrok_manager.requests.get')
    def test_start_ngrok_success(self, mock_get, mock_subprocess):
        # Mock the subprocess call to succeed
        mock_subprocess.return_value = None

        # Mock the ngrok API response with a valid HTTPS tunnel
        mock_get.return_value.json.return_value = {
            'tunnels': [{'public_url': 'https://abc123.ngrok-free.app', 'proto': 'https'}]
        }

        ngrok_url = self.ngrok_manager.start_ngrok()
        assert ngrok_url == "https://abc123.ngrok-free.app"

    @mock.patch('src.ngrok_manager.subprocess.Popen')
    def test_start_ngrok_failure(self, mock_popen):
        # Simulate subprocess failure by raising an exception when Popen is called
        mock_popen.side_effect = Exception("Subprocess failed")

        # Create an instance of NgrokManager
        ngrok_manager = NgrokManager()

        # Use pytest.raises to ensure the exception is correctly raised
        with pytest.raises(Exception, match="Subprocess failed"):
            ngrok_manager.start_ngrok()

    @responses.activate
    def test_upload_ngrok_url_success(self):
        # Mock the request URL and response.
        self.ngrok_manager.gateway_ngrok_url = 'http://mockserver/ngrok-url'
        self.ngrok_manager.api_key = 'your-api-key'

        # Mock the POST request to simulate a successful ngrok URL upload.
        responses.add(
            responses.POST,
            'http://mockserver/ngrok-url',
            json={"status": "success"},
            status=200
        )

        # Mock the GET request to simulate a successful confirmation check.
        responses.add(
            responses.GET,
            'http://mockserver/ngrok-url/your-api-key',
            json={"ngrok_url": "https://abc123.ngrok-free.app"},
            status=200
        )

        ngrok_url = "https://abc123.ngrok-free.app"
        success = self.ngrok_manager.upload_ngrok_url_to_gateway(ngrok_url)

        assert success is True

        # Verify that the POST request was called as expected.
        assert len(responses.calls) == 2
        assert responses.calls[0].request.method == 'POST'
        assert responses.calls[0].request.url == 'http://mockserver/ngrok-url'

        # Verify that the GET request was called as expected.
        assert responses.calls[1].request.method == 'GET'
        assert responses.calls[1].request.url == 'http://mockserver/ngrok-url/your-api-key'

    @mock.patch('src.ngrok_manager.requests.post')
    def test_upload_ngrok_url_failure(self, mock_post):
        # Directly override the attributes in the NgrokManager instance
        self.ngrok_manager.gateway_ngrok_url = 'https://your-gateway-url/ngrok-url'
        self.ngrok_manager.api_key = 'your-api-key'

        mock_post.side_effect = requests.exceptions.RequestException(
            "Request failed")

        ngrok_url = "https://abc123.ngrok-free.app"
        success = self.ngrok_manager.upload_ngrok_url_to_gateway(ngrok_url)

        assert success is False
        mock_post.assert_called_once()

    @mock.patch('src.ngrok_manager.NgrokManager.start_ngrok')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_setup_ngrok_success(self, mock_upload, mock_start):
        mock_start.return_value = "https://abc123.ngrok-free.app"
        mock_upload.return_value = True

        self.ngrok_manager.setup_ngrok()

        mock_start.assert_called_once()
        mock_upload.assert_called_once_with("https://abc123.ngrok-free.app")

    @mock.patch('src.ngrok_manager.NgrokManager.start_ngrok')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_setup_ngrok_failure(self, mock_upload, mock_start):
        mock_start.return_value = None  # Simulate ngrok failing to start
        self.ngrok_manager.setup_ngrok()

        mock_start.assert_called_once()
        mock_upload.assert_not_called()

    @mock.patch('src.ngrok_manager.requests.get')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_check_ngrok_status_running_synchronized(self, mock_upload, mock_get):
        # Mock the ngrok status response
        mock_get.return_value.json.return_value = {
            "tunnels": [{"public_url": "https://abc123.ngrok-free.app"}]
        }
        mock_get.return_value.status_code = 200

        # Set the environment variable for the current gateway upload URL
        with mock.patch.dict(os.environ, {"GATEWAY_UPLOAD_URL": "https://abc123.ngrok-free.app"}):
            result = self.ngrok_manager.check_ngrok_status()

        # Assert the result and that no upload was triggered
        assert result is True
        mock_upload.assert_not_called()

    @mock.patch('src.ngrok_manager.requests.get')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_check_ngrok_status_running_not_synchronized(self, mock_upload, mock_get):
        # Mock a different ngrok URL in the response
        mock_get.return_value.json.return_value = {
            "tunnels": [{"public_url": "https://new-ngrok-url.ngrok-free.app"}]
        }
        mock_get.return_value.status_code = 200

        # Set the environment variable to simulate an out-of-sync gateway URL
        with mock.patch.dict(os.environ, {"GATEWAY_UPLOAD_URL": "https://old-ngrok-url.ngrok-free.app"}):
            # Ensure that the upload_ngrok_url_to_gateway returns True to match the assertion
            mock_upload.return_value = True
            result = self.ngrok_manager.check_ngrok_status()

        # Assert the result and verify that the upload was called with the new URL
        assert result is True
        mock_upload.assert_called_once_with(
            "https://new-ngrok-url.ngrok-free.app")

    @mock.patch('src.ngrok_manager.NgrokManager.setup_ngrok')
    @mock.patch('src.ngrok_manager.requests.get')
    def test_check_ngrok_status_not_running(self, mock_get, mock_setup):
        mock_get.return_value.json.return_value = {"tunnels": []}
        mock_get.return_value.status_code = 200

        with mock.patch.dict(os.environ, {"GATEWAY_UPLOAD_URL": "https://abc123.ngrok-free.app"}):
            result = self.ngrok_manager.check_ngrok_status()

        assert result is False
        mock_setup.assert_called_once()
