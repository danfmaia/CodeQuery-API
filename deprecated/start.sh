#!/bin/bash

# Load environment variables from .env
export $(grep -v '^#' .env | xargs)

# Function to stop Flask app and ngrok processes on Ctrl+C or error
cleanup() {
    echo "Stopping Flask app and ngrok..."
    kill $FLASK_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    echo "Flask app and ngrok stopped."
    exit 0  # Ensure the script exits after cleanup
}

# Set trap to stop processes on Ctrl+C (SIGINT) or error (ERR)
trap cleanup SIGINT ERR

# Generate a timestamp for the log filenames
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Step 1: Activate the virtual environment and start Flask app
source ~/miniconda3/bin/activate venv/
mkdir -p logs  # Ensure the logs directory exists
nohup python src/app.py > "logs/nohup_start_flask_${TIMESTAMP}.out" 2>&1 &  # Run Flask app in the background
FLASK_PID=$!  # Store Flask app's PID
echo "Flask app started with PID: $FLASK_PID."

# Step 2: Check if there is an existing ngrok tunnel
# Add '|| true' to prevent the script from exiting due to an error in the curl command
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || true)

# Debugging info: Check if ngrok URL retrieval failed
if [ -z "$NGROK_URL" ]; then
    echo "No existing ngrok tunnel found. Starting a new ngrok tunnel..."

    # Start ngrok and retrieve the HTTPS URL
    ngrok http http://localhost:5001 > /dev/null &
    NGROK_PID=$!  # Store ngrok's PID
    sleep 5  # Wait for ngrok to start

    # Retrieve the new ngrok URL and handle failure scenarios
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url' 2>/dev/null || true)
    if [ -z "$NGROK_URL" ]; then
        echo "ngrok URL could not be retrieved. Exiting setup."
        kill $FLASK_PID  # Ensure Flask app is stopped before exiting
        exit 1
    fi
    echo "New ngrok URL: $NGROK_URL"
else
    echo "Existing ngrok tunnel found. Using URL: $NGROK_URL"
    
    # Improved process detection: Find any ngrok process
    NGROK_PID=$(pgrep -f "ngrok" || true)

    if [ -z "$NGROK_PID" ]; then
        echo "Warning: Could not find an active ngrok process. Starting a new ngrok process..."
        
        # Start a new ngrok process to ensure consistency
        ngrok http http://localhost:5001 > /dev/null &
        NGROK_PID=$!
        sleep 5
    else
        echo "ngrok process found with PID: $NGROK_PID"
    fi
fi

# Step 3: Update the .env file with the new ngrok URL
cd gateway/ || exit 1
sed -i "s|^NGROK_URL=.*|NGROK_URL=${NGROK_URL}|" .env
echo "Updated .env file with new ngrok URL."

# Step 4: Copy the .env file to the EC2 instance
source .env && scp -i "${KEY_PATH}" .env "${EC2_USER}@${EC2_HOST}:/home/${EC2_USER}/gateway"
if [ $? -ne 0 ]; then
    echo "Failed to copy .env to the server. Exiting setup."
    kill $FLASK_PID
    [ -n "$NGROK_PID" ] && kill $NGROK_PID  # Stop ngrok if running
    exit 1
fi
echo ".env file copied to EC2 instance."

# Step 5: SSH into the EC2 instance and manually source the updated .env file
ssh -i "${KEY_PATH}" "${EC2_USER}@${EC2_HOST}" "cd /home/${EC2_USER}/gateway && source .env && sudo systemctl restart fastapi && sudo systemctl status fastapi"
if [ $? -ne 0 ]; then
    echo "Failed to restart FastAPI service on the EC2 instance. Exiting setup."
    kill $FLASK_PID
    [ -n "$NGROK_PID" ] && kill $NGROK_PID  # Stop ngrok if running
    exit 1
fi
echo "FastAPI service restarted successfully."

cd ../

# Keep script running and wait for Ctrl+C (SIGINT)
echo "Deployment complete. Flask app and ngrok are running. Press Ctrl+C to stop."
while true; do
    sleep 60  # Sleep indefinitely until Ctrl+C is pressed
done
