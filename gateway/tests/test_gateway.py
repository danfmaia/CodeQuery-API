import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from gateway import GatewayAPI
import datetime


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
        # Mock S3 data with proper API key structure
        self.mock_s3_data = {
            "test-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": None,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            },
            "other-valid-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": None,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            }
        }

        # Mock ngrok URLs
        self.mock_ngrok_urls = {
            "test-key": "https://example.ngrok.io",
            "other-valid-key": "https://other.ngrok.io"
        }

        # Set up S3 manager mock
        patcher = patch.object(self.gateway_instance, 's3_manager')
        self.mock_s3_manager = patcher.start()
        self.mock_s3_manager.load_encrypted_api_keys.return_value = self.mock_s3_data
        self.mock_s3_manager.load_ngrok_url.side_effect = self.mock_ngrok_urls.get
        self.addCleanup(patcher.stop)

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

    @patch('gateway.S3Manager.load_ngrok_url')
    def test_get_ngrok_url_endpoint(self, mock_load_ngrok_url):
        """Test the /ngrok-urls/{api_key} endpoint."""
        # Mock the ngrok URL data
        mock_load_ngrok_url.return_value = "https://example.ngrok.io"

        headers = {"x-api-key": "test-key"}
        response = self.client.get("/ngrok-urls/test-key", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "api_key": "test-key",
            "ngrok_url": "https://example.ngrok.io"
        })

    @patch('gateway.S3Manager.update_ngrok_url')
    def test_update_ngrok_url_endpoint(self, mock_update_ngrok_url):
        """Test the /ngrok-urls/ POST endpoint."""
        # Mock the update response
        mock_update_ngrok_url.return_value = {
            "status": "success",
            "message": "ngrok URL updated for API key test-key"
        }

        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.update_ngrok_url.return_value = mock_update_ngrok_url.return_value
        mock_s3_manager.load_encrypted_api_keys.return_value = {  # Add API key data for middleware
            "test-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": None,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            }
        }
        # Add ngrok URL for middleware
        mock_s3_manager.load_ngrok_url.return_value = "https://example.ngrok.io"
        self.addCleanup(patcher.stop)

        headers = {"x-api-key": "test-key"}
        response = self.client.post(
            "/ngrok-urls/",
            json={"api_key": "test-key", "ngrok_url": "https://example.ngrok.io"},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "success",
            "message": "ngrok URL updated for API key test-key"
        })

    def test_dynamic_s3_update(self):
        """Test middleware's ability to handle dynamic changes in S3."""
        # Set initial ngrok URL in the mock data
        initial_url = "https://initial-ngrok-url.ngrok.io"
        updated_url = "https://updated-ngrok-url.ngrok.io"

        # Mock the API key data with proper structure
        self.mock_s3_data["test-key"] = {
            "created_at": "2024-02-14T10:00:00",
            "last_used": None,
            "expires_at": None,
            "rate_limit": {
                "requests_per_minute": 60,
                "current_minute": None,
                "minute_requests": 0
            },
            "total_requests": 0
        }

        # Mock the ngrok URLs
        self.mock_ngrok_urls = {
            "test-key": initial_url
        }

        with patch.object(self.gateway_instance.s3_manager, 'load_ngrok_url', side_effect=self.mock_ngrok_urls.get):
            # Validate the initial ngrok URL
            headers = {"x-api-key": "test-key"}
            response = self.client.get("/files/structure", headers=headers)
            self.assertNotEqual(response.status_code, 401)
            self.assertIn(
                initial_url, self.gateway_instance.ngrok_url_cache.get("test-key", ""))

            # Simulate dynamic update in S3
            self.mock_ngrok_urls["test-key"] = updated_url

            # Call the update method to refresh the cache
            self.gateway_instance.update_ngrok_url_from_s3("test-key")

            # Validate that the ngrok URL was updated
            self.assertIn(
                updated_url, self.gateway_instance.ngrok_url_cache.get("test-key", ""))

    @patch('gateway.GatewayAPI.update_ngrok_url_from_s3')
    @patch('gateway.requests.get')
    @patch.dict('os.environ', {'API_KEYS': 'test-key,other-valid-key'})
    def test_api_key_validator_middleware(self, mock_requests_get, mock_update_ngrok_urls):
        """Test the API key validator middleware using ngrok URL cache validation."""
        # Set up a reusable mock response for requests.get to simulate the /files/structure endpoint
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "structure": ["file1.py", "file2.py"]}
        mock_requests_get.return_value = mock_response

        # Prevent the real method from updating URLs during the test
        mock_update_ngrok_urls.return_value = None

        # Re-initialize the gateway instance after setting environment variables
        self.gateway_instance = GatewayAPI()
        self.client = TestClient(self.gateway_instance.app)

        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = self.mock_s3_data
        mock_s3_manager.load_ngrok_url.side_effect = self.mock_ngrok_urls.get
        self.addCleanup(patcher.stop)

        # Manually set the ngrok URL for each key in the cache
        mock_urls = {
            "test-key": "https://1234-5678-abcdef.ngrok-free.app",
            "other-valid-key": "https://5678-1234-ghijkl.ngrok-free.app"
        }
        self.gateway_instance.ngrok_url_cache.update(mock_urls)

        # Debugging log to inspect the cache state before running tests
        print(
            f"DEBUG: Current ngrok URL Cache: {self.gateway_instance.ngrok_url_cache}")

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
            print(
                f"DEBUG: Using ngrok URL for {api_key}: {self.gateway_instance.ngrok_url_cache[api_key]}")

            response = self.client.get("/files/structure", headers=headers)

            # Debugging log to print the status code and response for each test case
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")

            self.assertEqual(response.status_code, expected_status)

    @patch('gateway.S3Manager.store_encrypted_api_keys')
    @patch('gateway.S3Manager.load_encrypted_api_keys')
    def test_generate_api_key(self, mock_load_keys, mock_store_keys):
        """Test the API key generation endpoint."""
        # Mock the existing API keys
        mock_load_keys.return_value = {
            "test-key": {  # Add test-key to allow middleware validation
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": None,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            },
            "existing-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": None,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            }
        }

        # Mock successful storage
        mock_store_keys.return_value = {
            "status": "success", "message": "API keys stored securely in S3"}

        # Test with custom settings
        headers = {"x-api-key": "test-key", "content-type": "application/json"}
        custom_settings = {
            "expiration_days": 60,
            "requests_per_minute": 120
        }

        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = mock_load_keys.return_value
        mock_s3_manager.store_encrypted_api_keys.return_value = mock_store_keys.return_value
        # Add ngrok URL for middleware
        mock_s3_manager.load_ngrok_url.return_value = "https://example.ngrok.io"
        self.addCleanup(patcher.stop)

        response = self.client.post(
            "/api-keys/generate", headers=headers, json=custom_settings)

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("api_key", response_data)
        self.assertIn("expires_at", response_data)
        self.assertIn("rate_limit", response_data)
        self.assertEqual(response_data["rate_limit"], 120)

        # Verify the new key format and settings
        new_key = response_data["api_key"]
        # Base64 encoded 32 bytes should be longer
        self.assertTrue(len(new_key) > 32)

        # Verify S3 storage was called at least once
        self.assertGreater(
            mock_s3_manager.store_encrypted_api_keys.call_count, 0)

        # Verify that the last call to store_encrypted_api_keys contains the new key
        last_call_args = mock_s3_manager.store_encrypted_api_keys.call_args_list[-1]
        stored_keys = last_call_args[0][0]
        self.assertIn(new_key, stored_keys)
        key_data = stored_keys[new_key]
        self.assertIn("created_at", key_data)
        self.assertIn("expires_at", key_data)
        self.assertEqual(key_data["rate_limit"]["requests_per_minute"], 120)

    @patch('gateway.S3Manager.load_encrypted_api_keys')
    def test_key_expiration(self, mock_load_keys):
        """Test that expired keys are rejected."""
        current_time = datetime.datetime.utcnow()
        expired_time = (current_time - datetime.timedelta(days=1)).isoformat()

        # Mock expired API key
        mock_load_keys.return_value = {
            "test-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": None,
                "expires_at": expired_time,
                "rate_limit": {
                    "requests_per_minute": 60,
                    "current_minute": None,
                    "minute_requests": 0
                },
                "total_requests": 0
            }
        }

        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = mock_load_keys.return_value
        self.addCleanup(patcher.stop)

        # Attempt request with expired key
        headers = {"x-api-key": "test-key"}
        response = self.client.get("/files/structure", headers=headers)

        # Verify expiration response
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "API Key has expired"})

    @patch('gateway.S3Manager.load_encrypted_api_keys')
    def test_rate_limit_enforcement(self, mock_load_keys):
        """Test that rate limits are properly enforced."""
        current_time = datetime.datetime.utcnow()
        current_minute = current_time.strftime("%Y-%m-%d %H:%M")

        # Mock API key with rate limit
        mock_load_keys.return_value = {
            "test-key": {
                "created_at": "2024-02-14T10:00:00",
                "last_used": current_time.isoformat(),
                "expires_at": (current_time + datetime.timedelta(days=30)).isoformat(),
                "rate_limit": {
                    "requests_per_minute": 2,  # Low limit for testing
                    "current_minute": current_minute,
                    "minute_requests": 2  # Already at limit
                },
                "total_requests": 2
            }
        }

        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = mock_load_keys.return_value
        self.addCleanup(patcher.stop)

        # Attempt request with rate-limited key
        headers = {"x-api-key": "test-key"}
        response = self.client.get("/files/structure", headers=headers)

        # Verify rate limit response
        self.assertEqual(response.status_code, 429)
        response_data = response.json()
        self.assertIn("detail", response_data)
        self.assertIn("limit", response_data)
        self.assertIn("reset_at", response_data)
        self.assertEqual(response_data["limit"], 2)
