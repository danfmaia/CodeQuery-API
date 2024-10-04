import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from gateway import GatewayAPI


gateway_instance = GatewayAPI()


class TestGatewayAPI(unittest.TestCase):
    """Test suite for the GatewayAPI class."""

    @classmethod
    def setUpClass(cls):
        """Set up the TestClient for the FastAPI app and initialize API keys."""
        with patch.dict('os.environ', {'API_KEYS': 'test-key,other-valid-key'}):
            cls.gateway_instance = GatewayAPI()
            cls.client = TestClient(cls.gateway_instance.app)

    def setUp(self):
        """Set up mock S3 data before each test."""
        self.mock_s3_data = {
            "test-api-key": "https://example.ngrok.io"
        }

    @patch('gateway.requests.get')
    def test_get_file_structure(self, mock_get):
        """Test the /files/structure endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "structure": ["file1.py", "file2.py"]}
        mock_get.return_value = mock_response

        headers = {"x-api-key": "test-key"}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
                         "structure": ["file1.py", "file2.py"]})

    @patch('gateway.requests.post')
    def test_get_file_content(self, mock_post):
        """Test the /files/content endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"file1.py": "print('Hello World')"}
        mock_post.return_value = mock_response

        headers = {"x-api-key": "test-key"}
        response = self.client.post(
            "/files/content", json={"file_paths": ["file1.py"]}, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"file1.py": "print('Hello World')"})

    @patch.object(gateway_instance, 's3_manager')
    def test_get_ngrok_url_endpoint(self, mock_s3_manager):
        """Test the /ngrok-urls/{api_key} endpoint."""
        self.mock_s3_data["test-api-key"] = "https://example.ngrok.io"
        mock_s3_manager.load_ngrok_url.side_effect = lambda api_key: self.mock_s3_data.get(
            api_key, "")

        headers = {"x-api-key": "test-key"}
        response = self.client.get("/ngrok-urls/test-api-key", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
                         "api_key": "test-api-key", "ngrok_url": "https://example.ngrok.io"})

    @patch.object(gateway_instance, 's3_manager')
    def test_update_ngrok_url_endpoint(self, mock_s3_manager):
        """Test the /ngrok-urls/ POST endpoint."""
        mock_s3_manager.update_ngrok_url.side_effect = lambda api_key, url: self.mock_s3_data.update({
                                                                                                     api_key: url})

        headers = {"x-api-key": "test-key"}
        response = self.client.post(
            "/ngrok-urls/", json={"api_key": "test-api-key", "ngrok_url": "https://example.ngrok.io"}, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
                         "status": "success", "message": "ngrok URL updated for API key test-api-key"})

    # @patch.dict('os.environ', {'API_KEYS': 'test-key,other-valid-key'})
    # def test_api_key_validator_middleware(self):
    #     """Test the API key validator middleware with a valid and invalid key."""
    #     # Reinitialize `self.gateway_instance.api_keys` based on the patched environment variable
    #     self.gateway_instance.api_keys = {
    #         key: f"User{index + 1}" for index, key in enumerate(os.getenv("API_KEYS").split(","))
    #     }

    #     # Debug print to verify the correct keys are set
    #     print(f"DEBUG: Current API Keys: {self.gateway_instance.api_keys}")

    #     # Test with a valid API key
    #     headers = {"x-api-key": "test-key"}
    #     response = self.client.get("/files/structure", headers=headers)
    #     # Should not return Unauthorized
    #     self.assertNotEqual(response.status_code, 401)

    #     # Test with another valid API key
    #     headers = {"x-api-key": "other-valid-key"}
    #     response = self.client.get("/files/structure", headers=headers)
    #     # Should not return Unauthorized
    #     self.assertNotEqual(response.status_code, 401)

    #     # Test with an invalid API key (not in `self.api_keys`)
    #     headers = {"x-api-key": "invalid-key"}
    #     response = self.client.get("/files/structure", headers=headers)
    #     # Should return Unauthorized
    #     self.assertEqual(response.status_code, 401)

    def test_health_check(self):
        """Test the root health check endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "FastAPI is running"})
