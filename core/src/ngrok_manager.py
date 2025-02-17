import os
import time
import logging
import requests


class NgrokManager:
    """
    Class responsible for managing ngrok tunnels, including monitoring the tunnel,
    uploading the URL to the gateway, and verifying the status of the ngrok connection.
    """

    def __init__(self):
        self.logger = logging.getLogger('ngrok_manager')
        self.refresh_environment_variables()
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.registration_timeout = 120  # seconds
        self.backoff_factor = 1.5  # exponential backoff multiplier
        self.last_known_url = None
        self.last_successful_registration = 0

    def refresh_environment_variables(self) -> None:
        """Refresh class attributes from the environment variables."""
        self.ngrok_api_url = os.getenv(
            "NGROK_API_URL", "http://localhost:4040/api/tunnels").strip('"').strip("'")
        self.gateway_base_url = os.getenv(
            "GATEWAY_BASE_URL", "").strip('"').strip("'")
        self.gateway_ngrok_url = f"{self.gateway_base_url}/ngrok-urls"
        self.api_key = os.getenv("API_KEY", "").strip('"').strip("'")
        self.timeout = int(os.getenv("TIMEOUT", "10"))

    def check_ngrok_health(self) -> bool:
        """Basic health check to confirm ngrok's local API is reachable."""
        try:
            self.logger.info(f"Checking ngrok API: {self.ngrok_api_url}")
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            return response.status_code == 200
        except requests.RequestException as e:
            self.logger.error(f"ngrok health check failed: {e}")
            return False

    def get_ngrok_url(self) -> str:
        """Get the current ngrok URL."""
        try:
            response = requests.get(self.ngrok_api_url, timeout=self.timeout)
            tunnels = response.json().get('tunnels', [])
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    return tunnel['public_url']
            self.logger.warning("No HTTPS tunnel found in ngrok tunnels")
            return None
        except requests.RequestException as e:
            self.logger.error(f"Error getting ngrok URL: {e}")
            return None

    def setup_ngrok(self) -> None:
        """Wait for ngrok to be ready and upload the URL to the gateway with retries."""
        self.logger.info("Waiting for ngrok to be ready...")
        start_time = time.time()
        current_delay = self.retry_delay

        while time.time() - start_time < self.registration_timeout:
            if self.check_ngrok_health():
                ngrok_url = self.get_ngrok_url()
                if ngrok_url:
                    self.logger.info(f"ngrok is ready with URL: {ngrok_url}")
                    try:
                        if self.upload_ngrok_url_to_gateway(ngrok_url):
                            self.logger.info(
                                "Successfully registered ngrok URL with Gateway")
                            self.last_known_url = ngrok_url
                            self.last_successful_registration = time.time()
                            return
                        else:
                            self.logger.warning(
                                "Failed to register with Gateway, but continuing...")
                            self.last_known_url = ngrok_url
                            return
                    except Exception as e:
                        self.logger.error(
                            f"Error registering with Gateway: {str(e)}")
                        self.last_known_url = ngrok_url
                        return

            self.logger.info(
                f"Waiting {current_delay} seconds before next attempt...")
            time.sleep(current_delay)
            current_delay = min(current_delay * self.backoff_factor, 30)

        error_msg = "Failed to setup ngrok URL"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)

    def upload_ngrok_url_to_gateway(self, ngrok_url: str) -> bool:
        """Upload the ngrok URL to the gateway server with retries."""
        gateway_url = self.gateway_ngrok_url
        api_key = self.api_key

        if not gateway_url or not api_key:
            self.logger.error(
                f"Missing GATEWAY_NGROK_URL ({gateway_url}) or API_KEY ({api_key})")
            return False

        current_delay = self.retry_delay
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Attempt {attempt + 1}/{self.max_retries}: Uploading ngrok URL ({ngrok_url}) to Gateway ({gateway_url})")

                # Upload URL
                response = requests.post(
                    f"{gateway_url}/",  # Add trailing slash for POST endpoint
                    json={'api_key': api_key, 'ngrok_url': ngrok_url},
                    headers={'X-API-KEY': api_key},
                    timeout=self.timeout
                )
                response.raise_for_status()

                # Verify the upload with retries
                for verify_attempt in range(3):
                    # Correct URL format for verification
                    verify_url = f"{gateway_url}/{api_key}"
                    verify_response = requests.get(
                        verify_url,
                        headers={'X-API-KEY': api_key},
                        timeout=self.timeout
                    )
                    verify_response.raise_for_status()

                    verify_data = verify_response.json()
                    if verify_data.get('ngrok_url') == ngrok_url:
                        self.logger.info(
                            "Successfully uploaded and verified ngrok URL with Gateway.")
                        return True

                    self.logger.warning(
                        f"URL mismatch on verification attempt {verify_attempt + 1}. Retrying verification...")
                    time.sleep(1)

                self.logger.error(
                    f"URL mismatch after all verification attempts. Expected: {ngrok_url}, Got: {verify_data.get('ngrok_url')}")

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    current_delay = min(
                        current_delay * self.backoff_factor, 30)
                    self.logger.info(f"Retrying in {current_delay} seconds...")
                    time.sleep(current_delay)
                continue

        self.logger.error(
            "Failed to upload ngrok URL to Gateway after all retries.")
        return False

    def check_ngrok_status(self) -> bool:
        """
        Verify if ngrok is running and the gateway is synchronized with the correct URL.
        Returns:
            bool: Whether ngrok is correctly set up and gateway is updated.
        """
        self.refresh_environment_variables()
        self.logger.info("Checking ngrok status...")

        if not self.check_ngrok_health():
            self.logger.error(
                "ngrok is not responding. Please check if it's running.")
            return False

        ngrok_url = self.get_ngrok_url()
        if not ngrok_url:
            self.logger.error("No active ngrok tunnels found.")
            return False

        self.logger.info(f"ngrok is running: {ngrok_url}")

        # Check if URL has changed or if it's been too long since last successful registration
        if (ngrok_url != self.last_known_url or
                time.time() - self.last_successful_registration > 300):  # Re-register every 5 minutes
            self.logger.info(
                "URL changed or registration expired. Re-registering with Gateway...")
            if self.upload_ngrok_url_to_gateway(ngrok_url):
                self.last_known_url = ngrok_url
                self.last_successful_registration = time.time()
                return True
            return False

        return True
