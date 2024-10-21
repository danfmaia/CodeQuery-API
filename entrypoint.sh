#!/bin/bash

# Ensure ngrok is started and configured correctly
echo "Starting ngrok..."
ngrok http 5001 &

# Wait for ngrok to be ready
sleep 5

# Run the main application
echo "Starting the main application..."
exec "$@"
