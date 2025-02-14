# CodeQuery Gateway

## Overview

**CodeQuery™ Gateway** is a FastAPI-based service that acts as a secure entry point for managing access to the CodeQuery Core component. It serves as a proxy layer, handling API key validation, ngrok URL management, and secure request forwarding to the Core component. The Gateway is designed to operate within an AWS infrastructure, using S3 for dynamic URL synchronization and an EC2 instance to host the application.

The Gateway is an optional but recommended component for scenarios requiring secure and public access to the Core. Users can set up their own Gateway, using Terraform scripts provided in this repository to deploy a fully configured infrastructure, including EC2 instances, an Application Load Balancer, and DNS setup through Route 53.

## Features

- **Secure Request Forwarding**: Manages access to the Core component's `/files/structure` and `/files/content` endpoints using API key validation.
- **Dynamic ngrok URL Management**: Synchronizes the Core's ngrok URLs dynamically using S3, allowing seamless updates without downtime.
- **API Key Authentication**: Ensures secure access to all endpoints using predefined API keys.
- **Infrastructure as Code**: Fully deployable via Terraform, with modular configurations for EC2, S3, and Load Balancer setups.
- **Enhanced Security**: Server-side encryption for all S3 objects using AWS KMS, bucket-level encryption, and public access blocking.
- **API Key Management**: Secure storage and management of API keys using AWS KMS for encryption.

## Prerequisites

- Python 3.8+
- AWS account with permissions for EC2, S3, KMS, and Route 53
- Terraform installed locally
- A configured `.env` file with relevant AWS and application variables

## Setup and Deployment

### 1. Navigate to the Gateway Directory

After cloning the **CodeQuery-API** repository as described in the main README, switch to the `gateway/` folder:

```bash
cd CodeQuery-API/gateway
```

### 2. Configure Environment Variables

Create a `.env` file in the `gateway/` directory with the following variables:

```bash
# API keys that will be used for authentication
API_KEYS=test-key,other-valid-key,O8i5EVRqYI+0OGjPgoXI5Ey2CQzfJ+uIyI7e7yn8j0A=

# SSH and EC2 configuration for managing the remote Gateway server
EC2_USER="ec2-user"
EC2_HOST="<Your-EC2-Host-URL>"    # Replace with your EC2 public DNS or IP
KEY_PATH="./secrets/codequery-keypair.pem"  # Path to your SSH private key file

# AWS Configuration
AWS_REGION="sa-east-1"  # Your AWS region
KMS_KEY_ID="arn:aws:kms:sa-east-1:YOUR_ACCOUNT_ID:key/YOUR_KEY_ID"  # Your KMS key ARN
```

**Important**: Replace the placeholders with your actual values:

- `<Your-EC2-Host-URL>`: Your EC2 instance's public DNS (e.g., `ec2-xx-xx-xxx-xxx.region-id.compute.amazonaws.com`)
- `YOUR_ACCOUNT_ID`: Your AWS account ID
- `YOUR_KEY_ID`: The ID of your KMS key

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Terraform Setup

#### a. Configure Terraform Variables

Fill out the `terraform/terraform.tfvars` file with your AWS-specific values (region, AMI ID, etc.). This configuration will be used for the deployment of the Gateway infrastructure.

#### b. Initialize, Plan, and Apply Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will provision:

- EC2 instance with necessary IAM roles
- S3 bucket with server-side encryption and public access blocking
- KMS key for encrypting API keys and other sensitive data
- Security groups and other required resources

### 5. API Key Management

The Gateway provides a secure way to manage API keys using the `manage_api_keys.sh` script:

```bash
# Add a new API key
./scripts/manage_api_keys.sh add "your-api-key" "User1"

# List all API keys (usernames only)
./scripts/manage_api_keys.sh list

# Remove an API key
./scripts/manage_api_keys.sh remove "your-api-key"
```

All API keys are stored in S3 with server-side encryption using AWS KMS.

### 5. Start the Application Locally (Optional)

You can start the Gateway locally for testing:

```bash
uvicorn gateway:app --reload
```

### 6. Deploying to EC2

Once the Gateway infrastructure is set up using Terraform, follow these steps to deploy the application files to the EC2 instance and manage the service:

1. **Access the EC2 Instance via SSH**

   Make sure you have the environment variables configured (`EC2_USER`, `EC2_HOST`, and `KEY_PATH`) in your `.env` file.

   ```bash
   source .env && ssh -i $KEY_PATH $EC2_USER@$EC2_HOST
   ```

2. **Upload the Gateway Files to the EC2 Instance**

   Use `rsync` to upload all necessary files:

   ```bash
   rsync -av -e "ssh -i $KEY_PATH" --relative \
       .env \
       requirements.txt \
       gateway.py \
       src/__init__.py \
       src/s3_manager.py \
       conftest.py \
       tests/test_gateway.py \
       tests/test_s3_manager.py \
       $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway/
   ```

   Alternatively, you can use `scp` to upload individual files:

   ```bash
   scp -i $KEY_PATH gateway.py $EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway
   ```

3. **Restart the FastAPI Service**

   After uploading the files, restart the FastAPI service:

   ```bash
   ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo systemctl daemon-reload && sudo systemctl restart fastapi && sudo systemctl status fastapi"
   ```

4. **Check the Service Status**

   Verify that the service is running correctly:

   ```bash
   ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo systemctl status fastapi"
   ```

5. **Retrieve Logs (Optional)**

   To check the latest logs, run:

   ```bash
   ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo journalctl -u fastapi -n 50"
   ```

   To save the logs to your local machine:

   ```bash
   ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo journalctl -u fastapi -n 50" > logs/journalctl.txt
   ```

6. **Clear Logs and Restart (If Needed)**

   If you need to clear old logs and restart the service:

   ```bash
   ssh -i $KEY_PATH $EC2_USER@$EC2_HOST "sudo journalctl --rotate && sudo journalctl --vacuum-time=1s && sudo systemctl daemon-reload && sudo systemctl restart fastapi && sudo systemctl status fastapi"
   ```

This ensures the Gateway application is correctly deployed, managed, and monitored on the EC2 instance.

## API Endpoints

### 1. **Health Check**

- **Endpoint**: `/`
- **Method**: `GET`
- **Description**: Confirms that the Gateway component is running.

  **Example Request**:

  ```bash
  curl -X GET https://your-gateway-url.com/
  ```

  **Example Response**:

  ```json
  {
    "message": "FastAPI is running"
  }
  ```

### 2. **Retrieve Project Structure**

- **Endpoint**: `/files/structure`
- **Method**: `GET`
- **Description**: Retrieves the file structure from the Core component.

  **Example Request**:

  ```bash
  curl -H "X-API-KEY: <your-api-key>" https://your-gateway-url.com/files/structure
  ```

  **Example Response**:

  ```json
  {
    ".": {
      "directories": ["src", "tests"],
      "files": ["README.md", "requirements.txt"]
    }
  }
  ```

### 3. **Retrieve File Content**

- **Endpoint**: `/files/content`
- **Method**: `POST`
- **Description**: Fetches the content of specified files from the Core component.

  **Example Request**:

  ```bash
  curl -X POST -H "X-API-KEY: <your-api-key>" -H "Content-Type: application/json" -d '{
    "file_paths": ["README.md", "src/app.py"]
  }' https://your-gateway-url.com/files/content
  ```

  **Example Response**:

  ```json
  {
    "README.md": {
      "content": "# CodeQuery Project"
    },
    "src/app.py": {
      "content": "# Main application file for the CodeQuery Core API."
    }
  }
  ```

### 4. **ngrok URL Management**

#### Retrieve ngrok URL for an API Key

- **Endpoint**: `/ngrok-urls/{api_key}`
- **Method**: `GET`
- **Description**: Retrieves the current ngrok URL associated with a specific API key.

  **Example Request**:

  ```bash
  curl -X GET https://your-gateway-url.com/ngrok-urls/<your-api-key>
  ```

  **Example Response**:

  ```json
  {
    "api_key": "your-api-key",
    "ngrok_url": "https://example.ngrok-free.app"
  }
  ```

#### Update ngrok URL for an API Key

- **Endpoint**: `/ngrok-urls/`
- **Method**: `POST`
- **Description**: Updates the ngrok URL for a given API key.

  **Example Request**:

  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{
    "api_key": "your-api-key",
    "ngrok_url": "https://example.ngrok-free.app"
  }' https://your-gateway-url.com/ngrok-urls/
  ```

  **Example Response**:

  ```json
  {
    "message": "ngrok URL updated successfully"
  }
  ```

## Troubleshooting

- **API Key Issues**: Ensure that the API key is correctly set in your environment variables and the `.env` file on the EC2 instance.
- **ngrok URL Mismatch**: If the Core's ngrok URL is not synchronizing correctly, check the S3 bucket for the current values and verify that the Gateway exposed URL is configured properly, and correctly set in `GATEWAY_BASE_URL` (Core-side variable).
- **Permission Errors**: Verify that the EC2 instance and S3 bucket have the correct IAM roles and permissions.

## License

This project is licensed under the Apache License, Version 2.0.  
You may obtain a copy of the License at:

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
