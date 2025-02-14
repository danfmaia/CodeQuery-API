import os
import time
import requests
from dotenv import load_dotenv

# TODO: Improve this test to make it rougher, including calls for other endpoints.
# TODO: Consider converting this to a proper pytest test if we need:
#       - Better test reporting
#       - Integration with CI/CD pipelines
#       - More granular test assertions
#       For now, keeping it as a script is simpler and works well for manual testing.

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
API_KEY = os.getenv("API_KEY")
NGROK_URL = None


def check_service_ready():
    """Check if the Core service is ready to accept requests."""
    try:
        response = requests.get("http://localhost:5001/", timeout=1)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_ngrok_url():
    """Check if the ngrok URL is correctly updated in the Gateway."""
    print(f"Checking the ngrok URL for API key: {API_KEY}...")
    try:
        # Instead of getting the URL from the Gateway, get it directly from ngrok
        response = requests.get(
            "http://localhost:4040/api/tunnels",
            timeout=10
        )
        response.raise_for_status()
        tunnels = response.json().get('tunnels', [])
        for tunnel in tunnels:
            if tunnel.get('proto') == 'https':
                ngrok_url = tunnel['public_url']
                print(f"ngrok URL successfully retrieved: {ngrok_url}")
                return ngrok_url
        print("No HTTPS tunnel found in ngrok response")
        return None
    except requests.RequestException as e:
        print(f"Failed to retrieve ngrok URL: {str(e)}")
        return None


def run_curl_test():
    """Run the main cURL test to validate /files/structure functionality."""
    print("Running the main cURL test for `/files/structure`...")
    headers = {"X-API-KEY": API_KEY}
    try:
        # Use the ngrok URL directly instead of going through the Gateway
        if not NGROK_URL:
            print("No ngrok URL available. Skipping test.")
            return
        endpoint = f"{NGROK_URL}/files/structure"
        print(f"Testing endpoint: {endpoint}")
        print(f"Headers: {headers}")
        # Add a timeout to prevent hanging requests
        response = requests.get(
            endpoint,
            headers=headers,
            timeout=10
        )
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        # Print first 200 chars
        print(f"Response text: {response.text[:200]}...")
        response.raise_for_status()
        print("Main cURL test passed successfully!")
        print(f"Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Main cURL test failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response status code: {e.response.status_code}")
            print(f"Error response headers: {dict(e.response.headers)}")
            print(f"Error response text: {e.response.text}")


def main():
    # Wait for the service to be ready
    print("Waiting for Core service to be ready...")
    retries = 30
    for attempt in range(retries):
        if check_service_ready():
            print("Core service is ready!")
            break
        print(f"Waiting for service to be ready... ({attempt + 1}/{retries})")
        time.sleep(1)
    else:
        print("Failed to connect to Core service. Exiting.")
        return

    # Check ngrok URL update
    global NGROK_URL
    for _ in range(5):  # Retry logic to check ngrok URL
        NGROK_URL = check_ngrok_url()
        if NGROK_URL:
            break
        print("Retrying ngrok URL check in 5 seconds...")
        time.sleep(5)

    # Run the main cURL test if ngrok URL is available
    if NGROK_URL:
        run_curl_test()
    else:
        print("Failed to get ngrok URL. Exiting.")


if __name__ == "__main__":
    main()
