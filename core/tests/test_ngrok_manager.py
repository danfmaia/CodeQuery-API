# pylint: disable=C0116
import os
from unittest import mock
import responses
import requests
from src.ngrok_manager import NgrokManager


class TestNgrokManager:
    """
    Test suite for NgrokManager class, focusing on ngrok monitoring and URL synchronization.
    """

    def setup_method(self):
        """
        Setup method that runs before each test.
        Creates a new instance of the NgrokManager class.
        """
        self.ngrok_manager = NgrokManager()  # pylint: disable=W0201

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

        # Verify that both POST and GET requests were called as expected.
        assert len(responses.calls) == 2
        assert responses.calls[0].request.method == 'POST'
        assert responses.calls[0].request.url == 'http://mockserver/ngrok-url'
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

    def test_setup_ngrok_success(self):
        # Mock check_ngrok_health to return True
        with mock.patch.object(self.ngrok_manager, 'check_ngrok_health', return_value=True), \
                mock.patch.object(self.ngrok_manager, 'get_ngrok_url', return_value="https://abc123.ngrok-free.app"), \
                mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway', return_value=True):

            self.ngrok_manager.setup_ngrok()

    def test_setup_ngrok_failure_health_check(self):
        # Mock check_ngrok_health to return False
        with mock.patch.object(self.ngrok_manager, 'check_ngrok_health', return_value=False), \
                mock.patch.object(self.ngrok_manager, 'get_ngrok_url') as mock_get_url, \
                mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway') as mock_upload:

            self.ngrok_manager.setup_ngrok()

            mock_get_url.assert_not_called()
            mock_upload.assert_not_called()

    @mock.patch('src.ngrok_manager.requests.get')
    def test_check_ngrok_status_running_synchronized(self, mock_get):
        # Mock the ngrok status response
        mock_get.return_value.json.return_value = {
            "tunnels": [{"proto": "https", "public_url": "https://abc123.ngrok-free.app"}]}
        mock_get.return_value.status_code = 200

        # Set the environment variable for the new GATEWAY_BASE_URL
        with mock.patch.dict(os.environ, {"GATEWAY_BASE_URL": "https://abc123.ngrok-free.app"}):
            self.ngrok_manager.refresh_environment_variables()
            result = self.ngrok_manager.check_ngrok_status()

        # Assert the result and that no upload was triggered
        assert result is True

    @mock.patch('src.ngrok_manager.requests.get')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_check_ngrok_status_running_not_synchronized(self, mock_upload, mock_get):
        # Mock a different ngrok URL in the response
        mock_get.return_value.json.return_value = {
            "tunnels": [{"proto": "https", "public_url": "https://new-ngrok-url.ngrok-free.app"}]
        }
        mock_get.return_value.status_code = 200

        # Set the environment variable to simulate an out-of-sync gateway URL
        with mock.patch.dict(os.environ, {"GATEWAY_BASE_URL": "https://old-ngrok-url.ngrok-free.app"}):
            self.ngrok_manager.refresh_environment_variables()
            # Ensure that the upload_ngrok_url_to_gateway returns True to match the assertion
            mock_upload.return_value = True
            result = self.ngrok_manager.check_ngrok_status()

        # Assert the result and verify that the upload was called with the new URL
        assert result is True
        mock_upload.assert_called_once_with(
            "https://new-ngrok-url.ngrok-free.app")

    @mock.patch('src.ngrok_manager.requests.get')
    def test_check_ngrok_status_not_running(self, mock_get):
        mock_get.return_value.json.return_value = {"tunnels": []}
        mock_get.return_value.status_code = 200

        with mock.patch.dict(os.environ, {"GATEWAY_BASE_URL": "https://abc123.ngrok-free.app"}):
            self.ngrok_manager.refresh_environment_variables()
            result = self.ngrok_manager.check_ngrok_status()

        assert result is False
