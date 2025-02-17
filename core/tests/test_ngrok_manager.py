# pylint: disable=C0116
import os
import unittest
from unittest import mock
import responses
import requests
from src.ngrok_manager import NgrokManager


class TestNgrokManager(unittest.TestCase):
    """
    Test suite for NgrokManager class, focusing on ngrok monitoring and URL synchronization.
    """

    def setUp(self):
        """
        Set up a new NgrokManager instance for each test.
        Creates a new instance of the NgrokManager class.
        """
        self.ngrok_manager = NgrokManager()

    @responses.activate
    def test_upload_ngrok_url_success(self):
        """
        Test successful upload of ngrok URL.
        """
        with mock.patch('src.ngrok_manager.requests.post') as mock_post, \
                mock.patch('src.ngrok_manager.requests.get') as mock_get:
            # Mock successful POST response
            mock_post.return_value.status_code = 200
            # Mock successful GET verification response
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                'ngrok_url': 'https://abc123.ngrok-free.app'
            }

            # Set required attributes
            self.ngrok_manager.gateway_ngrok_url = 'https://gateway-url/ngrok-urls'
            self.ngrok_manager.api_key = 'test-api-key'

            success = self.ngrok_manager.upload_ngrok_url_to_gateway(
                'https://abc123.ngrok-free.app')

            assert success is True
            mock_post.assert_called_once()
            mock_get.assert_called_once()

    @mock.patch('src.ngrok_manager.requests.post')
    def test_upload_ngrok_url_failure(self, mock_post):
        """
        Test failed upload of ngrok URL with retries.
        """
        # Directly override the attributes in the NgrokManager instance
        self.ngrok_manager.gateway_ngrok_url = 'https://your-gateway-url/ngrok-url'
        self.ngrok_manager.api_key = 'your-api-key'

        mock_post.side_effect = requests.exceptions.RequestException(
            "Request failed")

        ngrok_url = "https://abc123.ngrok-free.app"
        success = self.ngrok_manager.upload_ngrok_url_to_gateway(ngrok_url)

        assert success is False
        # Verify it was called max_retries times
        assert mock_post.call_count == self.ngrok_manager.max_retries

    def test_setup_ngrok_success(self):
        """
        Test successful ngrok setup.
        """
        with mock.patch.object(self.ngrok_manager, 'check_ngrok_health', return_value=True), \
                mock.patch.object(self.ngrok_manager, 'get_ngrok_url', return_value='https://abc123.ngrok-free.app'), \
                mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway', return_value=True):

            # This should not raise any exceptions
            self.ngrok_manager.setup_ngrok()

    def test_setup_ngrok_failure_health_check(self):
        """
        Test ngrok setup failure due to health check.
        """
        with mock.patch.object(self.ngrok_manager, 'check_ngrok_health', return_value=False), \
                mock.patch.object(self.ngrok_manager, 'get_ngrok_url') as mock_get_url, \
                mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway') as mock_upload:

            # Reduce timeout for faster test
            self.ngrok_manager.registration_timeout = 1

            with self.assertRaises(RuntimeError) as context:
                self.ngrok_manager.setup_ngrok()

            assert "Failed to setup and register ngrok URL with Gateway" in str(
                context.exception)
            mock_get_url.assert_not_called()
            mock_upload.assert_not_called()

    @mock.patch('src.ngrok_manager.requests.get')
    def test_check_ngrok_status_running_synchronized(self, mock_get):
        """
        Test ngrok status check when running and synchronized.
        """
        with mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway', return_value=True):
            # Mock the ngrok status response
            mock_get.return_value.json.return_value = {
                "tunnels": [{"proto": "https", "public_url": "https://abc123.ngrok-free.app"}]}
            mock_get.return_value.status_code = 200

            result = self.ngrok_manager.check_ngrok_status()
            assert result is True

    @mock.patch('src.ngrok_manager.requests.get')
    @mock.patch('src.ngrok_manager.NgrokManager.upload_ngrok_url_to_gateway')
    def test_check_ngrok_status_running_not_synchronized(self, mock_upload, mock_get):
        """
        Test ngrok status check when running but not synchronized.
        """
        with mock.patch.object(self.ngrok_manager, 'upload_ngrok_url_to_gateway', return_value=False):
            # Mock the ngrok status response
            mock_get.return_value.json.return_value = {
                "tunnels": [{"proto": "https", "public_url": "https://abc123.ngrok-free.app"}]}
            mock_get.return_value.status_code = 200

            result = self.ngrok_manager.check_ngrok_status()
            assert result is False

    @mock.patch('src.ngrok_manager.requests.get')
    def test_check_ngrok_status_not_running(self, mock_get):
        """
        Test ngrok status check when not running.
        """
        with mock.patch('src.ngrok_manager.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(
                "Connection refused")

            result = self.ngrok_manager.check_ngrok_status()
            assert result is False
