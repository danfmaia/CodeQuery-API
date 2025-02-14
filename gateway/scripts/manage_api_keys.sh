#!/bin/bash

# Configuration
BUCKET_NAME="codequery-gateway-storage"
API_KEYS_FILE="api_keys.json"
KMS_KEY_ID="arn:aws:kms:sa-east-1:796973484576:key/2caae67f-7fe1-4555-82f0-6f6942320426"

# Function to add an API key
add_key() {
    local api_key=$1
    local user_name=$2
    
    # Download current keys
    aws s3 cp s3://$BUCKET_NAME/$API_KEYS_FILE .tmp_keys.json || echo "{}" > .tmp_keys.json
    
    # Add new key
    jq --arg key "$api_key" --arg user "$user_name" '. + {($key): $user}' .tmp_keys.json > .tmp_keys_new.json
    
    # Upload back to S3 with encryption using specific KMS key
    aws s3 cp .tmp_keys_new.json s3://$BUCKET_NAME/$API_KEYS_FILE --sse aws:kms --sse-kms-key-id $KMS_KEY_ID
    
    # Clean up
    rm -f .tmp_keys.json .tmp_keys_new.json
    
    echo "API key added for user: $user_name"
}

# Function to list all keys (usernames only for security)
list_keys() {
    aws s3 cp s3://$BUCKET_NAME/$API_KEYS_FILE - | jq 'to_entries | map(.value)'
}

# Function to remove a key
remove_key() {
    local api_key=$1
    
    # Download current keys
    aws s3 cp s3://$BUCKET_NAME/$API_KEYS_FILE .tmp_keys.json
    
    # Remove key
    jq --arg key "$api_key" 'del(.[$key])' .tmp_keys.json > .tmp_keys_new.json
    
    # Upload back to S3 with encryption using specific KMS key
    aws s3 cp .tmp_keys_new.json s3://$BUCKET_NAME/$API_KEYS_FILE --sse aws:kms --sse-kms-key-id $KMS_KEY_ID
    
    # Clean up
    rm -f .tmp_keys.json .tmp_keys_new.json
    
    echo "API key removed"
}

# Usage instructions
usage() {
    echo "Usage:"
    echo "  $0 add <api_key> <user_name>    - Add a new API key"
    echo "  $0 list                         - List all users with API keys"
    echo "  $0 remove <api_key>             - Remove an API key"
}

# Main script
case "$1" in
    "add")
        if [ -z "$2" ] || [ -z "$3" ]; then
            usage
            exit 1
        fi
        add_key "$2" "$3"
        ;;
    "list")
        list_keys
        ;;
    "remove")
        if [ -z "$2" ]; then
            usage
            exit 1
        fi
        remove_key "$2"
        ;;
    *)
        usage
        exit 1
        ;;
esac 