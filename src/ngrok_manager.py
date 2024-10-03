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
        self.ngrok_api_url = os.getenv("NGROK_API_URL")
        self.gateway_upload_url = os.getenv("GATEWAY_UPLOAD_URL")
        self.api_key = os.getenv("API_KEY")
        self.timeout = int(os.getenv("TIMEOUT", "10"))

    def start_ngrok(self) -> str:
        """Start ngrok and return the public URL."""
        try:
            # Start ngrok as a subprocess
            print("Starting ngrok...")
            subprocess.run(["ngrok", "http", "8080"], check=True)

            time.sleep(2)  # Give ngrok a moment to start

            # Request the ngrok tunnels with a timeout
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
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

    def upload_ngrok_url_to_gateway(self, ngrok_url: str) -> bool:
        """Upload the ngrok URL to the gateway server."""
        gateway_url = self.gateway_upload_url
        api_key = self.api_key

        if not gateway_url or not api_key:
            print(f"Missing GATEWAY_UPLOAD_URL ({
                  gateway_url}) or API_KEY ({api_key})")
            return False

        try:
            response = requests.post(
                gateway_url,
                json={'ngrok_url': ngrok_url},
                headers={'X-API-KEY': api_key},
                timeout=self.timeout
            )
            response.raise_for_status()
            print("Successfully uploaded ngrok URL to gateway.")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to upload ngrok URL to gateway: {str(e)}")
            return False

    def setup_ngrok(self) -> None:
        """Initialize ngrok and upload the URL to the gateway."""
        ngrok_url = self.start_ngrok()

        if ngrok_url:
            self.upload_ngrok_url_to_gateway(ngrok_url)
        else:
            print("Failed to start ngrok or retrieve the URL. Exiting setup.")

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
            if tunnels:
                ngrok_url = tunnels[0].get("public_url")
                print(f"ngrok is running: {ngrok_url}")

                # Debugging to check URL values
                print(f"ngrok_url: '{ngrok_url}', gateway_upload_url: '{
                      self.gateway_upload_url}'")

                # Check if gateway_upload_url is set before comparing
                if self.gateway_upload_url is None:
                    print("Warning: GATEWAY_UPLOAD_URL is not set.")
                    return False

                # Improved URL comparison with stripping and lowercasing
                if ngrok_url.strip().lower() == self.gateway_upload_url.strip().lower():
                    print("ngrok URL is already synchronized with the gateway.")
                    return True

                print(f"ngrok URL has changed. Updating gateway with new URL: {
                      ngrok_url}")
                return self.upload_ngrok_url_to_gateway(ngrok_url)

            print("No active ngrok tunnels found. Restarting ngrok...")
            self.setup_ngrok()
            return False

        except requests.exceptions.RequestException:
            print("ngrok is not running. Setting up ngrok...")
            self.setup_ngrok()
            return False
