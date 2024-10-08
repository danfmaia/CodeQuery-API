# CodeQuery Gateway

## Overview

CodeQuery™ Gateway is a FastAPI-based application designed to interact with a codebase by exposing APIs that can fetch file structures and content from remote servers via an ngrok tunnel. The infrastructure for this gateway is deployed on AWS using Terraform, with an EC2 instance running the FastAPI app and a load balancer for handling requests.

## Features

- **File Structure API**: Retrieve the file structure of the project.
- **File Content API**: Fetch the content of specified files.
- **API Key Authentication**: Secure access to the APIs using API keys.
- **AWS Infrastructure**: Fully configured AWS EC2 instance, security groups, and load balancer via Terraform.

## Prerequisites

- Python 3.x
- AWS account with the necessary permissions
- Terraform installed locally

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/CodeQuery-Gateway.git
cd CodeQuery-Gateway
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file with the following variables:

```bash
NGROK_URL=<your-ngrok-url>
API_KEYS=<your-comma-separated-api-keys>
```

### 4. Terraform Setup

#### a. Configure `terraform.tfvars`

Fill out the `terraform.tfvars_template` with your AWS-specific values (region, AMI ID, etc.) and save it as `terraform.tfvars`.

#### b. Initialize, Plan and Apply Terraform

```bash
terraform init
terraform plan
terraform apply
```

This will set up the EC2 instance, security groups, load balancer, and related resources on AWS.

### 5. Start the Application

To start or restart the application, use the following commands directly:

#### Refresh the `.env` File:

```bash
scp -i ../secrets/codequery-keypair.pem .env ec2-user@<your-ec2-host>:/home/ec2-user/gateway
```

#### Restart the FastAPI Server:

```bash
ssh -i ../secrets/codequery-keypair.pem ec2-user@<your-ec2-host> "sudo systemctl restart fastapi && sudo systemctl status fastapi"
```

#### Deploy or Copy Application Files:

```bash
scp -i ../secrets/codequery-keypair.pem app.py ec2-user@<your-ec2-host>:/home/ec2-user/gateway
scp -i ../secrets/codequery-keypair.pem requirements.txt ec2-user@<your-ec2-host>:/home/ec2-user/gateway
```

## Testing

You can start the FastAPI application locally with:

```bash
uvicorn app:app --reload
```

### File Structure API

To test the file structure endpoint, make the following request:

```bash
curl -H "X-API-KEY: <your-api-key>" http://<your-ec2-url>:8080/files/structure
```

### File Content API

To test the file content endpoint, use the following:

```bash
curl -X POST -H "X-API-KEY: <your-api-key>" -d '{"file_paths": ["app.py", "requirements.txt"]}' http://<your-ec2-url>:8080/files/content
```

## Deployment

### Restarting the FastAPI Service

You can restart the FastAPI service on the EC2 instance using SSH:

```bash
ssh -i ../secrets/codequery-keypair.pem ec2-user@<your-ec2-url> "sudo systemctl restart fastapi && sudo systemctl status fastapi"
```

## License

This project is licensed under the Apache 2.0 License. See the `LICENSE` file for details.
