# gateway/src/s3_manager.py

import json
import os
import boto3
from botocore.exceptions import ClientError


class S3Manager:
    """
    A class to handle S3 operations for storing and retrieving ngrok URLs.
    """

    def __init__(self):
        self.s3_client = self.get_s3_client()
        self.bucket_name, self.object_key = self.get_s3_bucket_and_key()

    def get_s3_client(self):
        """Initialize and return a new S3 client."""
        return boto3.client('s3')

    def get_s3_bucket_and_key(self):
        """Get the S3 bucket name and object key."""
        bucket_name = os.getenv('S3_BUCKET_NAME', 'codequery-gateway-storage')
        object_key = 'ngrok_urls.json'
        return bucket_name, object_key

    def load_ngrok_url(self, api_key):
        """
        Load the ngrok URL for a given API key from the S3 bucket.
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=self.object_key)
            raw_data = response['Body'].read().decode('utf-8')
            # Debug statement to verify raw data
            print(f"DEBUG: Raw S3 Response: {raw_data}")
            ngrok_data = json.loads(raw_data)
            return ngrok_data.get(api_key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise e

    def update_ngrok_url(self, api_key, new_ngrok_url):
        """
        Update or add a new ngrok URL for a given API key in the S3 bucket.
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
        ngrok_data[api_key] = new_ngrok_url

        # Put the updated object back to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=self.object_key,
            Body=json.dumps(ngrok_data),
            ContentType='application/json'
        )
        return {"status": "success", "message": f"ngrok URL updated for API key {api_key}"}
