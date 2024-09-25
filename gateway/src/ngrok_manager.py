# gateway/ngrok_manager.py

import json
import os

# Path to the JSON DB (you can adjust this path as needed)
JSON_DB_PATH = "/home/ec2-user/gateway/ngrok_db.json"


def load_ngrok_url(api_key):
    """
    Load ngrok URL for the given API key from the JSON database.
    """
    with open(JSON_DB_PATH, 'r') as f:
        data = json.load(f)
    return data.get("users", {}).get(api_key, {}).get("ngrok_url")


def update_ngrok_url(api_key, new_ngrok_url):
    """
    Update ngrok URL for the given API key in the JSON database.
    """
    with open(JSON_DB_PATH, 'r+') as f:
        data = json.load(f)
        if "users" not in data:
            data["users"] = {}
        if api_key not in data["users"]:
            data["users"][api_key] = {}

        # Update the ngrok URL
        data["users"][api_key]["ngrok_url"] = new_ngrok_url

        # Move the file pointer to the beginning
        f.seek(0)
        json.dump(data, f)
        f.truncate()


def generate_new_ngrok_url():
    """
    Simulate generating a new ngrok URL. (You could use the actual ngrok API here)
    """
    # Simulated new URL (in actual use, you'll fetch this via the ngrok API)
    return "https://new-ngrok-url.ngrok-free.app"
