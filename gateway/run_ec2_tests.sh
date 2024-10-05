#!/bin/bash

# Start the EC2 test automation script
echo "Starting the EC2 test automation script..."

# Load environment variables
source .env

# Check if required environment variables are set
if [[ -z "$KEY_PATH" || -z "$EC2_USER" || -z "$EC2_HOST" ]]; then
    echo "Error: One or more required environment variables are not set!"
    echo "Please ensure KEY_PATH, EC2_USER, and EC2_HOST are correctly configured."
    exit 1
fi

# Compare local and remote requirements.txt before syncing files
echo "Checking if requirements installation is needed on EC2..."
# Sync the local requirements.txt file to a temporary location on the EC2
scp -i "$KEY_PATH" requirements.txt "$EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway/requirements_local.txt"

# Compare local and remote requirements.txt files
requirements_diff=$(ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "diff /home/$EC2_USER/gateway/requirements_local.txt /home/$EC2_USER/gateway/requirements.txt")

# If there's a difference, install requirements
if [[ ! -z "$requirements_diff" ]]; then
    echo "Requirements have changed. Installing updated requirements on EC2..."
    ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "pip install -r /home/$EC2_USER/gateway/requirements_local.txt"
else
    echo "Requirements on EC2 are already up-to-date. Skipping installation."
fi

# Sync project files to EC2 instance
echo "Syncing project files to EC2 instance..."
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

# Run tests on EC2
echo "Running tests on EC2..."
ssh -i "$KEY_PATH" "$EC2_USER@$EC2_HOST" "cd /home/$EC2_USER/gateway && pytest tests/ | tee tests/results.txt"

# Download test results from EC2
echo "Downloading test results from EC2..."
scp -i "$KEY_PATH" "$EC2_USER@$EC2_HOST:/home/$EC2_USER/gateway/tests/results.txt" tests/ec2_results.txt

# Complete
echo "Test automation script completed successfully."
