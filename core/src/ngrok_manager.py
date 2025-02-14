import os
import time
import requests


class NgrokManager:
    """
    Class responsible for managing ngrok tunnels, including monitoring the tunnel,
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
            print(f"Checking ngrok API: {self.ngrok_api_url}")
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"ngrok health check failed: {e}")
            return False

    def get_ngrok_url(self) -> str:
        """Get the current ngrok URL."""
        try:
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            tunnels = response.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
            return None
        except requests.RequestException:
            return None

    def setup_ngrok(self) -> None:
        """Wait for ngrok to be ready and upload the URL to the gateway."""
        print("Waiting for ngrok to be ready...")
        retries = 30
        for attempt in range(retries):
            if self.check_ngrok_health():
                ngrok_url = self.get_ngrok_url()
                if ngrok_url:
                    print(f"ngrok is ready with URL: {ngrok_url}")
                    self.upload_ngrok_url_to_gateway(ngrok_url)
                    return
            print(f"Waiting... ({attempt + 1}/{retries})")
            time.sleep(1)
        print("Failed to connect to ngrok after retries.")

    def upload_ngrok_url_to_gateway(self, ngrok_url: str) -> bool:
        """Upload the ngrok URL to the gateway server."""
        gateway_url = self.gateway_ngrok_url
        api_key = self.api_key

        if not gateway_url or not api_key:
            print(
                f"Missing GATEWAY_NGROK_URL ({gateway_url}) or API_KEY ({api_key})")
            return False

        try:
            print(
                f"Uploading ngrok URL ({ngrok_url}) to Gateway ({gateway_url})")
            response = requests.post(
                gateway_url,
                json={'api_key': api_key, 'ngrok_url': ngrok_url},
                headers={'X-API-KEY': api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            print("Successfully uploaded ngrok URL to Gateway.")
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
        self.refresh_environment_variables()
        print("Checking ngrok status...")

        if not self.check_ngrok_health():
            print("ngrok is not responding. Please check if it's running.")
            return False

        ngrok_url = self.get_ngrok_url()
        if not ngrok_url:
            print("No active ngrok tunnels found.")
            return False

        print(f"ngrok is running: {ngrok_url}")
        return self.upload_ngrok_url_to_gateway(ngrok_url)
