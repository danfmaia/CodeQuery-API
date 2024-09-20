#!/bin/bash

# Generate a timestamp for the log filenames
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Kill the existing local server
pkill -f "python app.py"

# Restart local server in the background with a unique nohup output file
nohup python app.py > "logs/nohup_restart_flask_${TIMESTAMP}.out" 2>&1 &
echo "Local server restarted."
