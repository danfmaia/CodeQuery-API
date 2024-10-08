import os
import subprocess
import time
import requests
from dotenv import load_dotenv

# TODO: Improve this test to make it rougher, including calls for other endpoints.

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
API_KEY = os.getenv("API_KEY")
GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL")
GATEWAY_NGROK_URL = os.getenv("GATEWAY_BASE_URL") + '/ngrok-urls/'
# Extract base URL from the upload endpoint
NGROK_URL_ENDPOINT = f"{GATEWAY_NGROK_URL}{API_KEY}"
FILES_STRUCTURE_ENDPOINT = f"{GATEWAY_BASE_URL}/files/structure"
LOCAL_SCRIPT_COMMAND = ["python", "run.py"]


def run_local_script():
    """Start the `run.py` script and monitor its output."""
    print("Starting the local `run.py` script...")
    process = subprocess.Popen(
        LOCAL_SCRIPT_COMMAND, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return process


def check_ngrok_url():
    """Check if the ngrok URL is correctly updated in the Gateway."""
    print(f"Checking the ngrok URL for API key: {API_KEY}...")
    try:
        headers = {"x-api-key": API_KEY}
        # Add a timeout to prevent hanging requests
        response = requests.get(
            NGROK_URL_ENDPOINT, headers=headers, timeout=10)
        response.raise_for_status()
        ngrok_data = response.json()
        print(f"ngrok URL successfully retrieved: {ngrok_data['ngrok_url']}")
        return ngrok_data["ngrok_url"]
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve ngrok URL: {str(e)}")
        return None


def run_curl_test():
    """Run the main cURL test to validate /files/structure functionality."""
    print("Running the main cURL test for `/files/structure`...")
    headers = {"X-API-KEY": API_KEY}
    try:
        # Add a timeout to prevent hanging requests
        response = requests.get(FILES_STRUCTURE_ENDPOINT,
                                headers=headers, timeout=10)
        response.raise_for_status()
        print("Main cURL test passed successfully!")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Main cURL test failed: {str(e)}")


def main():
    # Step 1: Run the `run.py` script
    process = run_local_script()
    time.sleep(5)  # Allow some time for the ngrok tunnel to initialize

    # Step 2: Check ngrok URL update
    ngrok_url = None
    for _ in range(5):  # Retry logic to check ngrok URL
        ngrok_url = check_ngrok_url()
        if ngrok_url:
            break
        print("Retrying ngrok URL check in 5 seconds...")
        time.sleep(5)

    # Step 3: Run the main cURL test if ngrok URL is updated successfully
    if ngrok_url:
        run_curl_test()  # No longer passing `ngrok_url` as an argument
    else:
        print("Failed to update ngrok URL in the Gateway. Exiting.")

    # Step 4: Terminate the `run.py` script gracefully
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
    print("Integration test completed.")


if __name__ == "__main__":
    main()
