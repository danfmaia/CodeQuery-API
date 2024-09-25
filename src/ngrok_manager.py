import subprocess
import time
import requests
import os

# Constants
NGROK_API_URL = "http://localhost:4040/api/tunnels"
# This will be the endpoint to upload the ngrok URL
GATEWAY_UPLOAD_URL = os.getenv("GATEWAY_UPLOAD_URL")
API_KEY = os.getenv("API_KEY")  # Your API key for the gateway
REQUEST_TIMEOUT = 10  # Timeout for HTTP requests in seconds

# Start ngrok and retrieve the public URL


def start_ngrok():
    try:
        # Start ngrok as a subprocess
        print("Starting ngrok...")
        subprocess.run(["ngrok", "http", "8080"], check=True)

        time.sleep(2)  # Give ngrok a moment to start

        # Request the ngrok tunnels with a timeout
        response = requests.get(NGROK_API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise an exception for bad status codes

        tunnels = response.json().get('tunnels', [])
        for tunnel in tunnels:
            if tunnel.get('proto') == 'https':
                ngrok_url = tunnel['public_url']
                print(f"ngrok URL: {ngrok_url}")
                return ngrok_url

        print("No valid ngrok URL found.")
        return None

    except (subprocess.CalledProcessError, requests.RequestException) as e:
        print(f"Error starting ngrok: {e}")
        return None

# Upload the ngrok URL to the gateway server


def upload_ngrok_url_to_gateway(ngrok_url: str) -> bool:
    gateway_url = os.getenv('GATEWAY_UPLOAD_URL')
    api_key = os.getenv('API_KEY')

    print(f"GATEWAY_UPLOAD_URL: {gateway_url}")  # Debugging
    print(f"API_KEY: {api_key}")  # Debugging

    if not gateway_url or not api_key:
        print("Missing GATEWAY_UPLOAD_URL or API_KEY")
        return False

    try:
        response = requests.post(
            gateway_url,
            json={'ngrok_url': ngrok_url},
            headers={'X-API-KEY': api_key},
            timeout=10
        )
        response.raise_for_status()
        print("Successfully uploaded ngrok URL to gateway.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to upload ngrok URL to gateway: {str(e)}")
        return False


# Full setup process for starting ngrok and uploading the URL


def setup_ngrok():
    ngrok_url = start_ngrok()

    if ngrok_url:
        upload_ngrok_url_to_gateway(ngrok_url)
    else:
        print("Failed to start ngrok or retrieve the URL. Exiting setup.")
