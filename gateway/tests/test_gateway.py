import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from gateway import GatewayAPI
import datetime
import requests


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
    @patch('gateway.S3Manager.update_ngrok_url')
    def test_generate_api_key_initializes_ngrok_url(self, mock_update_ngrok_url, mock_load_keys, mock_store_keys):
        """Test that generating a new API key initializes an empty ngrok URL entry."""
        # Set up S3 manager mock for this test
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = {
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
        mock_s3_manager.store_encrypted_api_keys.return_value = {
            "status": "success", "message": "API keys stored securely in S3"}
        mock_s3_manager.update_ngrok_url.return_value = {
            "status": "success", "message": "ngrok URL initialized for API key"}
        self.addCleanup(patcher.stop)

        # Test with default settings
        response = self.client.post("/api-keys/generate")

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("api_key", response_data)

        # Verify that update_ngrok_url was called with None
        new_key = response_data["api_key"]
        mock_s3_manager.update_ngrok_url.assert_called_once_with(new_key, None)

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

    def test_api_key_expiration(self):
        """Test API key expiration handling."""
        # Set up expired key data
        expired_key = "expired-key"
        self.mock_s3_data[expired_key] = {
            "created_at": "2024-02-14T10:00:00",
            "last_used": None,
            "expires_at": "2024-02-14T11:00:00",  # Set to a past time
            "rate_limit": {
                "requests_per_minute": 60,
                "current_minute": None,
                "minute_requests": 0
            },
            "total_requests": 0
        }

        headers = {"x-api-key": expired_key}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "API Key has expired"})

    def test_rate_limit_exceeded(self):
        """Test rate limit handling."""
        # Set up key data with rate limit exceeded
        rate_limited_key = "rate-limited-key"
        current_minute = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        self.mock_s3_data[rate_limited_key] = {
            "created_at": "2024-02-14T10:00:00",
            "last_used": None,
            "expires_at": None,
            "rate_limit": {
                "requests_per_minute": 60,
                "current_minute": current_minute,
                "minute_requests": 60  # Set to limit
            },
            "total_requests": 100
        }

        headers = {"x-api-key": rate_limited_key}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 429)
        self.assertIn("rate limit exceeded", response.json()["detail"].lower())

    def test_invalid_expiration_date(self):
        """Test handling of invalid expiration date format."""
        # Set up key data with invalid expiration date
        invalid_exp_key = "invalid-exp-key"
        self.mock_s3_data[invalid_exp_key] = {
            "created_at": "2024-02-14T10:00:00",
            "last_used": None,
            "expires_at": "invalid-date",  # Invalid date format
            "rate_limit": {
                "requests_per_minute": 60,
                "current_minute": None,
                "minute_requests": 0
            },
            "total_requests": 0
        }

        headers = {"x-api-key": invalid_exp_key}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {
                         "detail": "Error checking key expiration"})

    def test_s3_storage_error(self):
        """Test handling of S3 storage errors."""
        # Mock S3 storage to raise an exception
        self.mock_s3_manager.store_encrypted_api_keys.side_effect = Exception(
            "S3 error")

        # Mock requests.get to return an error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(
                "Connection error")

            # Set up the test key with rate limit data
            test_key = "test-key"
            current_minute = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            self.mock_s3_data[test_key]["rate_limit"] = {
                "requests_per_minute": 60,
                "current_minute": current_minute,
                "minute_requests": 30
            }

            headers = {"x-api-key": test_key}
            response = self.client.get("/files/structure", headers=headers)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {
                             "detail": "Error retrieving file structure: Connection error"})

    def test_file_structure_request_error(self):
        """Test handling of errors in file structure requests."""
        headers = {"x-api-key": "test-key"}
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException(
                "Connection error")
            response = self.client.get("/files/structure", headers=headers)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {
                             "detail": "Error retrieving file structure: Connection error"})

    def test_file_structure_invalid_response(self):
        """Test handling of invalid response from file structure endpoint."""
        headers = {"x-api-key": "test-key"}
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_response
            response = self.client.get("/files/structure", headers=headers)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {
                             "detail": "Error updating ngrok URL"})

    def test_file_content_invalid_response(self):
        """Test handling of invalid response from file content endpoint."""
        headers = {"x-api-key": "test-key"}
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_response
            response = self.client.post(
                "/files/content",
                json={"file_paths": ["test.py"]},
                headers=headers
            )
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {
                             "detail": "Error updating ngrok URL"})

    def test_file_content_missing_paths(self):
        """Test handling of missing file paths in content request."""
        headers = {"x-api-key": "test-key"}
        # Mock the update_ngrok_url_from_s3 method to avoid S3 calls
        with patch.object(self.gateway_instance, 'update_ngrok_url_from_s3') as mock_update:
            with patch('requests.post') as mock_post:
                # Set up the mock response
                mock_response = MagicMock()
                mock_response.status_code = 404
                mock_response.text = "Not Found"
                mock_response.json.return_value = {
                    "detail": "No file paths provided"}
                mock_post.return_value = mock_response

                # Set up the mock update method
                mock_update.return_value = None
                self.gateway_instance.ngrok_url_cache["test-key"] = "https://example.ngrok.io"

                # Make the request
                response = self.client.post(
                    "/files/content", json={}, headers=headers)
                # Gateway passes through the response
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {
                                 "detail": "No file paths provided"})

                # Verify the mock was called correctly
                mock_post.assert_called_once_with(
                    "https://example.ngrok.io/files/content",
                    json={},  # Empty JSON object is passed through
                    timeout=self.gateway_instance.timeout
                )

    def test_ngrok_url_update_missing_data(self):
        """Test handling of missing data in ngrok URL update request."""
        headers = {"x-api-key": "test-key"}
        # Mock the update_ngrok_url_from_s3 method to avoid S3 calls
        with patch.object(self.gateway_instance, 'update_ngrok_url_from_s3') as mock_update:
            # Clear the ngrok URL cache to trigger the invalid URL error
            self.gateway_instance.ngrok_url_cache.clear()
            response = self.client.post(
                "/ngrok-urls/", json={}, headers=headers)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {
                             "detail": "Failed to update ngrok URL: "})

    def test_middleware_general_error(self):
        """Test handling of general errors in middleware."""
        # Mock load_encrypted_api_keys to raise an unexpected exception
        self.mock_s3_manager.load_encrypted_api_keys.side_effect = Exception(
            "Unexpected error")

        headers = {"x-api-key": "test-key"}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal server error"})

    def test_file_content_request_error(self):
        """Test handling of errors in file content requests."""
        headers = {"x-api-key": "test-key"}
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(
                "Connection error")
            response = self.client.post(
                "/files/content",
                json={"file_paths": ["test.py"]},
                headers=headers
            )
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.json()["detail"].lower())

    def test_api_key_generation(self):
        """Test API key generation endpoint."""
        response = self.client.post("/api-keys/generate")
        self.assertEqual(response.status_code, 200)
        self.assertIn("api_key", response.json())
        generated_key = response.json()["api_key"]
        self.assertTrue(len(generated_key) > 0)

    def test_ngrok_url_cache_invalidation(self):
        """Test ngrok URL cache invalidation."""
        # Set up initial cache state
        test_key = "test-key"
        self.gateway_instance.ngrok_url_cache[test_key] = "https://test.ngrok.io"

        # Invalidate cache
        self.gateway_instance.invalidate_ngrok_cache(test_key)

        # Verify cache was cleared
        self.assertNotIn(test_key, self.gateway_instance.ngrok_url_cache)

    def test_invalid_ngrok_url(self):
        """Test handling of invalid ngrok URL format."""
        # Set up invalid ngrok URL
        invalid_url_key = "invalid-url-key"
        self.mock_ngrok_urls[invalid_url_key] = "not-a-valid-url"
        self.mock_s3_data[invalid_url_key] = {
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

        headers = {"x-api-key": invalid_url_key}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Invalid ngrok URL"})

    def test_ngrok_url_update_error(self):
        """Test handling of errors during ngrok URL update."""
        # Mock update_ngrok_url_from_s3 to raise an exception
        error_key = "error-key"
        self.mock_s3_data[error_key] = {
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
        self.mock_s3_manager.load_ngrok_url.side_effect = Exception(
            "Update error")

        headers = {"x-api-key": error_key}
        response = self.client.get("/files/structure", headers=headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {
                         "detail": "Error updating ngrok URL"})

    @patch.dict('os.environ', {'ADMIN_API_KEY': 'admin-key'})
    def test_purge_api_key(self):
        """Test API key purge endpoint."""
        # Set up test data
        test_key = "test-key-to-purge"
        test_key_data = {
            "created_at": "2024-02-14T10:00:00",
            "last_used": "2024-02-14T11:00:00",
            "expires_at": None,
            "rate_limit": {
                "requests_per_minute": 60,
                "current_minute": None,
                "minute_requests": 0
            },
            "total_requests": 10
        }

        # Set up S3 manager mock
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = {
            test_key: test_key_data,
            "admin-key": {
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
        self.addCleanup(patcher.stop)

        # Test successful self-purge by user
        headers = {"x-api-key": test_key}
        response = self.client.delete(f"/api-keys/{test_key}", headers=headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["purged_data"]["total_requests"], 10)

        # Verify S3 manager calls for self-purge
        mock_s3_manager.store_encrypted_api_keys.assert_called()
        mock_s3_manager.update_ngrok_url.assert_called_with(test_key, None)

        # Reset call counts and mock data
        mock_s3_manager.store_encrypted_api_keys.reset_mock()
        mock_s3_manager.update_ngrok_url.reset_mock()
        mock_s3_manager.load_encrypted_api_keys.return_value = {
            test_key: test_key_data,
            "admin-key": {
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

        # Test successful purge by admin
        headers = {"x-api-key": "admin-key"}
        response = self.client.delete(f"/api-keys/{test_key}", headers=headers)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["status"], "success")
        self.assertEqual(response_data["purged_data"]["total_requests"], 10)

        # Verify S3 manager calls
        mock_s3_manager.store_encrypted_api_keys.assert_called()
        mock_s3_manager.update_ngrok_url.assert_called_with(test_key, None)

    @patch.dict('os.environ', {'ADMIN_API_KEY': 'admin-key'})
    def test_purge_api_key_unauthorized(self):
        """Test API key purge endpoint with unauthorized access."""
        # Set up test data
        test_key = "test-key-to-purge"
        other_key = "other-key"
        test_key_data = {
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

        # Set up S3 manager mock
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = {
            test_key: test_key_data,
            other_key: test_key_data
        }
        self.addCleanup(patcher.stop)

        # Test with another user's key (not admin, not self)
        headers = {"x-api-key": other_key}
        response = self.client.delete(f"/api-keys/{test_key}", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"], "Unauthorized. You can only purge your own API key.")

        # Test without API key
        response = self.client.delete(f"/api-keys/{test_key}")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Missing API Key")

    @patch.dict('os.environ', {'ADMIN_API_KEY': 'admin-key'})
    def test_purge_admin_key(self):
        """Test attempt to purge admin API key."""
        # Set up S3 manager mock
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = {
            "admin-key": {
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
        self.addCleanup(patcher.stop)

        # Test attempt to purge admin key
        headers = {"x-api-key": "admin-key"}
        response = self.client.delete("/api-keys/admin-key", headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"], "Cannot purge admin API key")

    @patch.dict('os.environ', {'ADMIN_API_KEY': 'admin-key'})
    def test_purge_nonexistent_key(self):
        """Test attempt to purge a non-existent API key."""
        # Set up S3 manager mock
        patcher = patch.object(self.gateway_instance, 's3_manager')
        mock_s3_manager = patcher.start()
        mock_s3_manager.load_encrypted_api_keys.return_value = {}
        self.addCleanup(patcher.stop)

        # Test purge of non-existent key
        headers = {"x-api-key": "admin-key"}
        response = self.client.delete(
            "/api-keys/nonexistent-key", headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"], "API key nonexistent-key not found")
