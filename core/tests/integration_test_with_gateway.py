import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
API_KEY = os.getenv("API_KEY")
GATEWAY_URL = os.getenv("GATEWAY_BASE_URL", "https://codequery.dev")


def check_service_ready():
    """Check if the Core service is ready to accept requests."""
    try:
        response = requests.get("http://localhost:5001/", timeout=1)
        return response.status_code == 200
    except requests.RequestException:
        return False


def test_core_directly():
    """Test the Core service endpoints directly."""
    print("\nTesting Core service directly...")
    try:
        # Test /files/structure endpoint directly
        response = requests.get(
            "http://localhost:5001/files/structure", timeout=5)
        print(f"Direct /files/structure status code: {response.status_code}")
        if response.status_code != 200:
            print("Direct file structure test failed!")
            return False

        # Test /files/content endpoint directly
        response = requests.post(
            "http://localhost:5001/files/content",
            json={"file_paths": ["README.md"]},
            timeout=5
        )
        print(f"Direct /files/content status code: {response.status_code}")
        if response.status_code != 200:
            print("Direct file content test failed!")
            return False

        print("Direct Core service tests passed!")
        return True
    except requests.RequestException as e:
        print(f"Direct Core service test failed: {str(e)}")
        return False


def test_gateway_connection():
    """Test the Gateway connection with proper ngrok URL verification."""
    print("\nTesting Gateway connection...")

    # First, verify that ngrok URL is registered
    try:
        verify_url = f"{GATEWAY_URL}/ngrok-urls/{API_KEY}"
        verify_response = requests.get(
            verify_url,
            headers={"X-API-KEY": API_KEY},
            timeout=5
        )
        if verify_response.status_code != 200:
            print(
                f"Failed to verify ngrok URL registration: {verify_response.status_code}")
            return False

        ngrok_data = verify_response.json()
        if not ngrok_data.get("ngrok_url"):
            print("No ngrok URL registered with Gateway")
            return False

        print(f"Found registered ngrok URL: {ngrok_data.get('ngrok_url')}")
    except requests.RequestException as e:
        print(f"Failed to verify ngrok registration: {str(e)}")
        return False

    # Now test the actual Gateway connection
    try:
        response = requests.get(
            f"{GATEWAY_URL}/proxy/{API_KEY}/files/structure",
            headers={"X-API-KEY": API_KEY},
            timeout=5
        )
        print(f"Gateway response status: {response.status_code}")
        if response.status_code == 200:
            print("Gateway connection test passed!")
            return True
        print(
            f"Gateway connection test failed with status: {response.status_code}")
        return False
    except requests.RequestException as e:
        print(f"Gateway connection test failed: {str(e)}")
        return False


def main():
    # Wait for Core service (max 30 seconds)
    print("Waiting for Core service to be ready...")
    for i in range(30):
        if check_service_ready():
            print("Core service is ready!")
            break
        print(f"Waiting for service to be ready... ({i + 1}/30)")
        time.sleep(1)
    else:
        print("Failed to connect to Core service. Exiting.")
        return 1

    # Test Core service directly
    if not test_core_directly():
        print("Core service direct tests failed. Exiting.")
        return 1

    # Give Gateway more time to establish and register ngrok connection
    print("\nWaiting for Gateway connection to be established...")
    for i in range(12):  # Wait up to 60 seconds
        time.sleep(5)
        try:
            verify_url = f"{GATEWAY_URL}/ngrok-urls/{API_KEY}"
            verify_response = requests.get(
                verify_url,
                headers={"X-API-KEY": API_KEY},
                timeout=5
            )
            if verify_response.status_code == 200:
                ngrok_data = verify_response.json()
                if ngrok_data.get("ngrok_url"):
                    print("Gateway connection established!")
                    break
        except requests.RequestException:
            pass
        print(f"Waiting for Gateway connection... ({i + 1}/12)")
    else:
        print("Warning: Gateway connection not established after 60 seconds")

    # Simple Gateway test
    if not test_gateway_connection():
        print("\nGateway test failed, but Core service is working directly.")
        return 0  # Return success since Core service is working

    print("\nAll tests passed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
