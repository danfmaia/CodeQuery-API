import json
import logging
import os
import boto3
from botocore.exceptions import ClientError


class S3Manager:
    """
    A class to handle S3 operations for storing and retrieving ngrok URLs.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.s3_client = self.get_s3_client()
        self.kms_client = self.get_kms_client()
        self.bucket_name, self.object_key = self.get_s3_bucket_and_key()

    def get_s3_client(self):
        """Initialize and return a new S3 client."""
        region = os.getenv('AWS_REGION', 'us-east-1')
        return boto3.client('s3', region_name=region)

    def get_kms_client(self):
        """Initialize and return a new KMS client."""
        region = os.getenv('AWS_REGION', 'us-east-1')
        return boto3.client('kms', region_name=region)

    def get_s3_bucket_and_key(self):
        """Get the S3 bucket name and object key."""
        bucket_name = os.getenv('S3_BUCKET_NAME', 'codequery-gateway-storage')
        object_key = 'ngrok_urls.json'
        return bucket_name, object_key

    def load_encrypted_api_keys(self):
        """
        Load API keys from the S3 bucket. The data is automatically decrypted by S3
        when using server-side encryption with KMS.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key='api_keys.json'
            )
            # S3 automatically decrypts the data when using SSE-KMS
            raw_data = response['Body'].read().decode('utf-8')
            api_keys = json.loads(raw_data)

            # Convert legacy format if needed
            if api_keys and isinstance(next(iter(api_keys.values())), str):
                updated_keys = {}
                for key, value in api_keys.items():
                    updated_keys[key] = {
                        "created_at": None,  # Legacy keys don't have creation time
                        "last_used": None,
                        "expires_at": None,  # No expiration for legacy keys
                        "rate_limit": {
                            "requests_per_minute": 60,  # Default rate limit
                            "current_minute": None,
                            "minute_requests": 0
                        },
                        "total_requests": 0
                    }
                api_keys = updated_keys
            elif api_keys:
                # Update existing keys with new fields if they don't exist
                for key in api_keys:
                    if "expires_at" not in api_keys[key]:
                        api_keys[key]["expires_at"] = None
                    if "rate_limit" not in api_keys[key]:
                        api_keys[key]["rate_limit"] = {
                            "requests_per_minute": 60,
                            "current_minute": None,
                            "minute_requests": 0
                        }
                    if "total_requests" not in api_keys[key]:
                        api_keys[key]["total_requests"] = 0

            return api_keys

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.warning("API keys file not found in S3.")
                return None
            self.logger.error("ClientError while accessing S3: %s", str(e))
            raise e

        except json.JSONDecodeError as e:
            self.logger.error("Error decoding JSON data: %s", str(e))
            return None

    def store_encrypted_api_keys(self, api_keys):
        """
        Store API keys in the S3 bucket using server-side encryption with KMS.
        """
        try:
            # Convert API keys dictionary to JSON
            # Handle datetime serialization
            raw_data = json.dumps(api_keys, default=str)

            # Store the data in S3 with server-side encryption
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key='api_keys.json',
                Body=raw_data,
                ServerSideEncryption='aws:kms',
                SSEKMSKeyId=os.getenv('KMS_KEY_ID'),
                ContentType='application/json'
            )
            return {"status": "success", "message": "API keys stored securely in S3"}

        except ClientError as e:
            self.logger.error("Error storing API keys in S3: %s", str(e))
            raise e

    def load_ngrok_url(self, api_key):
        """
        Load the ngrok URL for a given API key from the S3 bucket.
        Returns:
            - The URL string if it exists
            - None if the key exists but has no URL
            - False if the key doesn't exist in the ngrok_urls.json file
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.object_key)
            raw_data = response['Body'].read().decode('utf-8')
            ngrok_data = json.loads(raw_data)

            # Log the number of ngrok URLs without exposing sensitive data
            self.logger.debug(
                "Retrieved %d ngrok URL mappings from S3", len(ngrok_data))

            # If the key exists in the data, return its value (which may be None)
            if api_key in ngrok_data:
                return ngrok_data[api_key]

            # Key doesn't exist in the file
            return False

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return False
            raise e

    def update_ngrok_url(self, api_key, new_ngrok_url):
        """
        Update or add a new ngrok URL for a given API key in the S3 bucket.
        If new_ngrok_url is None, initializes an empty entry for the API key.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.object_key)
            ngrok_data = json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                ngrok_data = {}  # Initialize an empty dictionary if the file does not exist
            else:
                raise e

        # Update or insert the new URL
        if new_ngrok_url is None:
            # Only add the key if it doesn't exist yet
            if api_key not in ngrok_data:
                ngrok_data[api_key] = None
        else:
            ngrok_data[api_key] = new_ngrok_url

        # Put the updated object back to S3 with server-side encryption
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.object_key,
            Body=json.dumps(ngrok_data),
            ServerSideEncryption='aws:kms',
            SSEKMSKeyId=os.getenv('KMS_KEY_ID'),
            ContentType='application/json'
        )

        return {"status": "success", "message": f"ngrok URL {'initialized' if new_ngrok_url is None else 'updated'} for API key {api_key}"}
