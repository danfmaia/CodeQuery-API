import unittest
from unittest.mock import patch, MagicMock
from src.s3_manager import S3Manager


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
        mock_boto_client.assert_called_once_with('s3')
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
                    ContentType='application/json'
                )

    def tearDown(self):
        """Clear the state after each test."""
        self.s3_manager = None


if __name__ == '__main__':
    unittest.main()
