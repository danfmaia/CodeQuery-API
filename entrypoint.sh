#!/bin/bash

# Function to check if ngrok is ready
check_ngrok() {
    curl -s http://localhost:4040/api/tunnels > /dev/null
    return $?
}

# Start ngrok
echo "Starting ngrok..."
ngrok http 5001 > /dev/null 2>&1 &

# Wait for ngrok to be ready with timeout
echo "Waiting for ngrok to be ready..."
TIMEOUT=30
COUNTER=0
while ! check_ngrok && [ $COUNTER -lt $TIMEOUT ]; do
    echo "Waiting for ngrok... ($(($TIMEOUT - $COUNTER)) seconds remaining)"
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if ! check_ngrok; then
    echo "Failed to start ngrok after $TIMEOUT seconds"
    exit 1
fi

echo "ngrok is ready!"

# Run the main application with proper logging
echo "Starting the main application..."
exec "$@" 2>&1
