import unittest
from unittest.mock import patch, MagicMock
from src.s3_manager import S3Manager
import json
from botocore.exceptions import ClientError


class TestS3Manager(unittest.TestCase):
    """Test suite for the S3Manager class."""

    def setUp(self):
        """Set up a mock S3Manager instance for each test."""
        # Mock the environment variable for the S3 bucket name
        with patch.dict('os.environ', {'S3_BUCKET_NAME': 'test-bucket'}):
            self.s3_manager = S3Manager()

    @patch('src.s3_manager.boto3.client')
    def test_get_s3_client(self, mock_boto_client):
        """Test that the S3 client is correctly initialized."""
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client

        # Test client initialization
        s3_client = self.s3_manager.get_s3_client()
        mock_boto_client.assert_called_once_with('s3', region_name='sa-east-1')
        self.assertEqual(s3_client, mock_s3_client)

    def test_load_ngrok_url(self):
        """Test loading ngrok URL from S3 bucket using instance-level patching."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            with patch('src.s3_manager.S3Manager.get_s3_bucket_and_key') as mock_get_bucket_and_key:
                mock_get_bucket_and_key.return_value = (
                    'test-bucket', 'ngrok_urls.json')

                # Mock the S3 response with a controlled initial state
                mock_response = MagicMock()
                mock_response['Body'].read.return_value = b'{"test-api-key": "https://example.ngrok.io"}'
                mock_s3_client.get_object.return_value = mock_response

                # Call the load_ngrok_url method
                ngrok_url = self.s3_manager.load_ngrok_url('test-api-key')
                self.assertEqual(ngrok_url, 'https://example.ngrok.io')

    def test_update_ngrok_url(self):
        """Test updating ngrok URL in S3 bucket using instance-level patching."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            with patch('src.s3_manager.S3Manager.get_s3_bucket_and_key') as mock_get_bucket_and_key:
                with patch.dict('os.environ', {'KMS_KEY_ID': 'test-kms-key-id'}):
                    mock_get_bucket_and_key.return_value = (
                        'test-bucket', 'ngrok_urls.json')

                    # Mock the S3 get_object response to simulate an initial empty state
                    mock_response = MagicMock()
                    # Empty JSON state
                    mock_response['Body'].read.return_value = b'{}'
                    mock_s3_client.get_object.return_value = mock_response

                    # Call the update_ngrok_url method
                    result = self.s3_manager.update_ngrok_url(
                        'test-api-key', 'https://new-example.ngrok.io')

                    # Check the updated content
                    expected_result = {
                        "status": "success", "message": "ngrok URL updated for API key test-api-key"}
                    self.assertEqual(result, expected_result)

                    # Verify that put_object was called with the correct updated data
                    mock_s3_client.put_object.assert_called_once_with(
                        Bucket='test-bucket',
                        Key='ngrok_urls.json',
                        Body='{"test-api-key": "https://new-example.ngrok.io"}',
                        ServerSideEncryption='aws:kms',
                        SSEKMSKeyId='test-kms-key-id',
                        ContentType='application/json'
                    )

    def test_load_encrypted_api_keys(self):
        """Test loading encrypted API keys from S3."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            # Test successful load with modern format
            mock_response = MagicMock()
            mock_response['Body'].read.return_value = json.dumps({
                'test-key': {
                    'created_at': '2024-02-14T00:00:00',
                    'last_used': None,
                    'expires_at': None,
                    'rate_limit': {
                        'requests_per_minute': 60,
                        'current_minute': None,
                        'minute_requests': 0
                    },
                    'total_requests': 0
                }
            }).encode()
            mock_s3_client.get_object.return_value = mock_response

            result = self.s3_manager.load_encrypted_api_keys()
            self.assertIsNotNone(result)
            self.assertIn('test-key', result)
            self.assertEqual(result['test-key']['total_requests'], 0)

            # Test legacy format conversion
            mock_response['Body'].read.return_value = json.dumps({
                'test-key': 'legacy-value'
            }).encode()
            result = self.s3_manager.load_encrypted_api_keys()
            self.assertIsNotNone(result)
            self.assertIn('test-key', result)
            self.assertEqual(result['test-key']['total_requests'], 0)
            self.assertIsNone(result['test-key']['created_at'])

            # Test file not found
            mock_s3_client.get_object.side_effect = ClientError(
                {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}},
                'GetObject'
            )
            result = self.s3_manager.load_encrypted_api_keys()
            self.assertIsNone(result)

            # Test other client error
            mock_s3_client.get_object.side_effect = ClientError(
                {'Error': {'Code': 'OtherError', 'Message': 'Other error'}},
                'GetObject'
            )
            with self.assertRaises(ClientError):
                self.s3_manager.load_encrypted_api_keys()

    def test_store_encrypted_api_keys(self):
        """Test storing encrypted API keys in S3."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            with patch.dict('os.environ', {'KMS_KEY_ID': 'test-kms-key-id'}):
                # Test successful store
                api_keys = {
                    'test-key': {
                        'created_at': '2024-02-14T00:00:00',
                        'last_used': None,
                        'expires_at': None,
                        'rate_limit': {
                            'requests_per_minute': 60,
                            'current_minute': None,
                            'minute_requests': 0
                        },
                        'total_requests': 0
                    }
                }
                result = self.s3_manager.store_encrypted_api_keys(api_keys)
                self.assertEqual(result['status'], 'success')
                mock_s3_client.put_object.assert_called_once_with(
                    Bucket=self.s3_manager.bucket_name,
                    Key='api_keys.json',
                    Body=json.dumps(api_keys, default=str),
                    ServerSideEncryption='aws:kms',
                    SSEKMSKeyId='test-kms-key-id',
                    ContentType='application/json'
                )

                # Test client error
                mock_s3_client.put_object.side_effect = ClientError(
                    {'Error': {'Code': 'InternalError', 'Message': 'Internal error'}},
                    'PutObject'
                )
                with self.assertRaises(ClientError):
                    self.s3_manager.store_encrypted_api_keys(api_keys)

    def test_error_handling(self):
        """Test error handling in various methods."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            # Test JSON decode error in load_ngrok_url
            mock_response = MagicMock()
            mock_response['Body'].read.return_value = b'invalid json'
            mock_s3_client.get_object.return_value = mock_response

            with self.assertRaises(json.JSONDecodeError):
                self.s3_manager.load_ngrok_url('test-key')

            # Test client error in update_ngrok_url
            mock_s3_client.get_object.side_effect = ClientError(
                {'Error': {'Code': 'InternalError', 'Message': 'Internal error'}},
                'GetObject'
            )
            with self.assertRaises(ClientError):
                self.s3_manager.update_ngrok_url(
                    'test-key', 'https://test.ngrok.io')

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and remaining error handling scenarios."""
        with patch.object(self.s3_manager, 's3_client', new_callable=MagicMock) as mock_s3_client:
            # Test JSON decode error in load_encrypted_api_keys
            mock_response = MagicMock()
            mock_response['Body'].read.return_value = b'invalid json'
            mock_s3_client.get_object.return_value = mock_response
            result = self.s3_manager.load_encrypted_api_keys()
            self.assertIsNone(result)

            # Test empty API keys dict
            mock_response['Body'].read.return_value = b'{}'
            mock_s3_client.get_object.return_value = mock_response
            result = self.s3_manager.load_encrypted_api_keys()
            self.assertEqual(result, {})

            # Test API keys with missing fields
            mock_response['Body'].read.return_value = json.dumps({
                'test-key': {
                    'created_at': '2024-02-14T00:00:00'
                }
            }).encode()
            result = self.s3_manager.load_encrypted_api_keys()
            self.assertIn('test-key', result)
            self.assertIn('rate_limit', result['test-key'])
            self.assertIn('total_requests', result['test-key'])

            # Test NoSuchKey error in load_ngrok_url
            mock_s3_client.get_object.side_effect = ClientError(
                {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}},
                'GetObject'
            )
            result = self.s3_manager.load_ngrok_url('test-key')
            self.assertIs(result, False)

            # Test NoSuchKey error in update_ngrok_url
            result = self.s3_manager.update_ngrok_url(
                'test-key', 'https://test.ngrok.io')
            self.assertEqual(result['status'], 'success')

    def tearDown(self):
        """Clear the state after each test."""
        self.s3_manager = None


if __name__ == '__main__':
    unittest.main()
