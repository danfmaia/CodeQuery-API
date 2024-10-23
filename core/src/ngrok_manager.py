import os
import subprocess
import time
import requests


class NgrokManager:
    """
    Class responsible for managing ngrok tunnels, including starting the tunnel,
    uploading the URL to the gateway, and verifying the status of the ngrok connection.
    """

    def __init__(self):
        self.refresh_environment_variables()

    def refresh_environment_variables(self) -> None:
        """Refresh class attributes from the environment variables."""
        self.ngrok_api_url = os.getenv(
            "NGROK_API_URL", "http://localhost:4040/api/tunnels").strip('"').strip("'")
        self.gateway_base_url = os.getenv(
            "GATEWAY_BASE_URL", "").strip('"').strip("'")
        self.gateway_ngrok_url = f"{self.gateway_base_url}/ngrok-urls/"
        self.api_key = os.getenv("API_KEY", "").strip('"').strip("'")
        self.timeout = int(os.getenv("TIMEOUT", "10"))

    def check_ngrok_health(self) -> bool:
        """Basic health check to confirm ngrok's local API is reachable."""
        try:
            print(f"Performing health check on ngrok API: \
                  {self.ngrok_api_url}")
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            print(f"Health check response: {response.status_code}")
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"ngrok health check failed: {e}")
            return False

    def start_ngrok(self) -> str:
        """Start ngrok in the background and verify its initialization."""
        try:
            print("Starting ngrok...")
            local_port = os.getenv("LOCAL_PORT", "5001")
            ngrok_command = f"ngrok http {local_port}"

            # Start ngrok in the background without using a 'with' statement
            subprocess.Popen(
                ngrok_command.split(),
                stdout=subprocess.DEVNULL,  # Suppress output
                stderr=subprocess.DEVNULL  # Suppress error output
            )

            # Allow ngrok some time to start
            retries = 5
            for attempt in range(retries):
                print(f"Attempt {attempt + 1} to check ngrok health...")
                time.sleep(2)
                if self.check_ngrok_health():
                    response = requests.get(
                        self.ngrok_api_url, timeout=self.timeout)
                    tunnels = response.json().get('tunnels', [])
                    for tunnel in tunnels:
                        if tunnel.get('proto') == 'https':
                            ngrok_url = tunnel['public_url']
                            print(f"ngrok URL: {ngrok_url}")
                            return ngrok_url

            print("No valid ngrok URL found after retries.")
            return None

        except (subprocess.CalledProcessError, requests.RequestException) as e:
            print(f"Error starting ngrok: {e}")
            return None

    def setup_ngrok(self) -> None:
        """Initialize ngrok and upload the URL to the gateway."""
        print("Setting up ngrok...")
        ngrok_url = self.start_ngrok()

        if ngrok_url:
            print(f"ngrok started successfully with URL: {ngrok_url}")
            self.upload_ngrok_url_to_gateway(ngrok_url)
        else:
            print("Failed to start ngrok or retrieve the URL. Exiting setup.")

    def upload_ngrok_url_to_gateway(self, ngrok_url: str) -> bool:
        """Upload the ngrok URL to the gateway server."""
        gateway_url = self.gateway_ngrok_url
        api_key = self.api_key

        if not gateway_url or not api_key:
            print(f"Missing GATEWAY_NGROK_URL (\
                  {gateway_url}) or API_KEY ({api_key})")
            return False

        try:
            print(f"Uploading ngrok URL ({ngrok_url}) to Gateway (\
                  {gateway_url}) with API Key: {api_key}...")
            response = requests.post(
                gateway_url,
                json={'api_key': api_key, 'ngrok_url': ngrok_url},
                headers={'X-API-KEY': api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            print("Successfully uploaded ngrok URL to Gateway.")
            # Confirm Gateway has the new URL
            confirm_response = requests.get(
                f"{gateway_url}/{api_key}", headers={'X-API-KEY': api_key}, timeout=self.timeout)
            print(f"Confirmed Gateway cache update: {confirm_response.json()}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to upload ngrok URL to Gateway: {str(e)}")
            return False

    def check_ngrok_status(self) -> bool:
        """
        Verify if ngrok is running and the gateway is synchronized with the correct URL.
        Returns:
            bool: Whether ngrok is correctly set up and gateway is updated.
        """
        self.refresh_environment_variables()  # Ensure class variables are up-to-date
        print("Checking ngrok status...")
        try:
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            response.raise_for_status()
            tunnels = response.json().get("tunnels", [])
            print(f"Tunnel response: {tunnels}")

            if tunnels:
                ngrok_url = tunnels[0].get("public_url")
                print(f"ngrok is running: {ngrok_url}")

                if self.gateway_base_url is None:
                    print("Warning: GATEWAY_BASE_URL is not correctly set.")
                    return False

                if ngrok_url.strip().lower() == self.gateway_base_url.strip().lower():
                    print("ngrok URL is already synchronized with the gateway.")
                    return True

                print(f"ngrok URL has changed. Updating gateway with new URL: \
                      {ngrok_url}")
                return self.upload_ngrok_url_to_gateway(ngrok_url)

            print("No active ngrok tunnels found. Restarting ngrok...")
            self.setup_ngrok()
            return False

        except requests.exceptions.RequestException:
            print("ngrok is not running. Setting up ngrok...")
            self.setup_ngrok()
            return False
