#!/bin/bash

# TODO: Add error handling, and include 

# Generate a timestamp for the log filenames
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Kill the existing local server
pkill -f "python src/app.py"

# Restart local server in the background with a unique nohup output file
nohup python src/app.py > "logs/nohup_restart_flask_${TIMESTAMP}.out" 2>&1 &
echo "Local server restarted."
