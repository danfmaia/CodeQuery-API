import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from gateway import GatewayAPI


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

    def test_health_check(self):
        """Test the root health check endpoint."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "FastAPI is running"})

    @patch('gateway.requests.get')
    def test_get_file_structure(self, mock_get):
        """Test the /files/structure endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "structure": ["file1.py", "file2.py"]}
        mock_get.return_value = mock_response

        headers = {"x-api-key": "test-key"}

        # Debug logs for cache verification before making the request
        print(f"DEBUG: Current ngrok URL Cache: \
              {self.gateway_instance.ngrok_url_cache}")

        # Perform the request and check the response
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

    @patch('gateway.gateway_instance.s3_manager')
    def test_get_ngrok_url_endpoint(self, mock_s3_manager):
        """Test the /ngrok-urls/{api_key} endpoint."""
        self.mock_s3_data["test-api-key"] = "https://example.ngrok.io"
        mock_s3_manager.load_ngrok_url.side_effect = self.mock_s3_data.get

        headers = {"x-api-key": "test-key"}
        response = self.client.get("/ngrok-urls/test-api-key", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
                         "api_key": "test-api-key", "ngrok_url": "https://example.ngrok.io"})

    @patch('gateway.gateway_instance.s3_manager')
    def test_update_ngrok_url_endpoint(self, mock_s3_manager):
        """Test the /ngrok-urls/ POST endpoint."""
        mock_s3_manager.update_ngrok_url.side_effect = self.mock_s3_data.update

        headers = {"x-api-key": "test-key"}
        response = self.client.post(
            "/ngrok-urls/", json={"api_key": "test-api-key", "ngrok_url": "https://example.ngrok.io"}, headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
                         "status": "success", "message": "ngrok URL updated for API key test-api-key"})

    def test_dynamic_s3_update(self):
        """Test middleware's ability to handle dynamic changes in S3."""
        # Set initial ngrok URL in the mock data
        self.mock_s3_data["test-key"] = "https://initial-ngrok-url.ngrok.io"
        with patch.object(self.gateway_instance.s3_manager, 'load_ngrok_url', side_effect=self.mock_s3_data.get):

            # Validate the initial ngrok URL
            headers = {"x-api-key": "test-key"}
            response = self.client.get("/files/structure", headers=headers)
            self.assertNotEqual(response.status_code, 401)
            print(f"Initial ngrok URL: \
                  {self.gateway_instance.ngrok_url_cache.get('test-key', '')}")
            self.assertIn("initial-ngrok-url.ngrok.io",
                          self.gateway_instance.ngrok_url_cache.get("test-key", ""))

            # Simulate dynamic update in S3
            self.mock_s3_data["test-key"] = "https://updated-ngrok-url.ngrok.io"
            print(f"DEBUG: Simulated S3 Update: {self.mock_s3_data}")

            # Call the update method to refresh the cache
            self.gateway_instance.update_ngrok_url_from_s3("test-key")

            # Validate that the ngrok URL was updated
            print(f"Updated ngrok URL: \
                  {self.gateway_instance.ngrok_url_cache.get('test-key', '')}")
            self.assertIn("updated-ngrok-url.ngrok.io",
                          self.gateway_instance.ngrok_url_cache.get("test-key", ""))

    @patch('gateway.GatewayAPI.update_ngrok_url_from_s3')
    @patch('gateway.requests.get')
    @patch.dict('os.environ', {'API_KEYS': 'test-key,other-valid-key'})
    def test_api_key_validator_middleware(self, mock_requests_get, mock_update_ngrok_urls):
        """Test the API key validator middleware using ngrok URL cache validation."""

        # Set up a reusable mock response for requests.get to simulate the /files/structure endpoint
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "structure": ["file1.py", "file2.py"]
        }
        mock_requests_get.return_value = mock_response

        # Prevent the real method from updating URLs during the test
        mock_update_ngrok_urls.return_value = "https://mocked-url-during-test.ngrok.io"

        # Re-initialize the gateway instance after setting environment variables
        self.gateway_instance = GatewayAPI()
        self.client = TestClient(self.gateway_instance.app)

        # Manually set the ngrok URL for each key in the cache using a common helper function
        mock_urls = {
            "test-key": "https://1234-5678-abcdef.ngrok-free.app",
            "other-valid-key": "https://5678-1234-ghijkl.ngrok-free.app"
        }
        self.gateway_instance.ngrok_url_cache.update(mock_urls)

        # Debugging log to inspect the cache state before running tests
        print(f"DEBUG: Updated ngrok URL Cache: \
              {self.gateway_instance.ngrok_url_cache}")

        # Define test cases
        test_cases = [
            ("test-key", 200, {"structure": ["file1.py", "file2.py"]}),
            ("other-valid-key", 200, {"structure": ["file1.py", "file2.py"]}),
            ("invalid-key", 401, {"detail": "Invalid API Key"}),
        ]

        # Run the test cases using a loop
        for api_key, expected_status, expected_response in test_cases:
            headers = {"x-api-key": api_key}

            # Refresh the cache to avoid stale data
            self.gateway_instance.ngrok_url_cache[api_key] = mock_urls.get(
                api_key, '')

            # Debugging log to show URL before request
            print(f"DEBUG: Using ngrok URL for {api_key}: \
                  {self.gateway_instance.ngrok_url_cache[api_key]}")

            response = self.client.get("/files/structure", headers=headers)

            # Debugging log to print the status code and response for each test case
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")

            self.assertEqual(response.status_code, expected_status)
