import os
from fastapi import FastAPI, Request, HTTPException
import requests
from dotenv import load_dotenv
# Import the S3Manager class instead of individual functions
from src.s3_manager import S3Manager


class GatewayAPI:
    """
    GatewayAPI is a FastAPI-based gateway application to interact with ngrok
    tunnels and file operations.
    """

    def __init__(self):
        load_dotenv()
        self.ngrok_url = os.getenv("NGROK_URL")
        self.timeout = 10

        # Load API keys from environment variables (comma-separated keys)
        self.api_keys = {
            key: f"User{index + 1}" for index, key in enumerate(os.getenv("API_KEYS").split(","))
        }

        # Create an S3Manager instance to handle S3 operations
        self.s3_manager = S3Manager()

        # Initialize the FastAPI app
        self.app = FastAPI()

        # Register routes and middleware
        self.setup_routes()
        self.setup_middleware()

    def setup_middleware(self):
        """Configure the middleware for API key validation."""

        @self.app.middleware("http")
        async def api_key_validator(request: Request, call_next):
            """
            Middleware to validate API Key, excluding certain endpoints.
            """
            if request.url.path == "/":  # Exclude the root health check endpoint
                return await call_next(request)

            api_key = request.headers.get("x-api-key", None)

            # Add debug print to verify current state of self.api_keys
            print(f"DEBUG: Current API Keys in middleware: {self.api_keys}")

            if not api_key or api_key not in self.api_keys:
                raise HTTPException(status_code=401, detail="Invalid API Key")

            response = await call_next(request)
            return response

    def setup_routes(self):
        """Define all the routes for the gateway."""

        @self.app.get("/")
        def read_root():
            """
            Server health check.
            """
            return {"message": "FastAPI is running"}

        @self.app.get("/files/structure")
        async def get_file_structure():
            """
            Retrieve the file structure from the Codebase Query API via the ngrok URL.
            """
            try:
                response = requests.get(
                    f"{self.ngrok_url}/files/structure", timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving file structure: {str(e)}") from e

        @self.app.post("/files/content")
        async def get_file_content(request_data: dict):
            """
            Retrieve the content of specified files from the Codebase Query API.
            """
            try:
                response = requests.post(
                    f"{self.ngrok_url}/files/content", json=request_data, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving file content: {str(e)}") from e

        # New Endpoint: Update ngrok URL
        @self.app.post("/ngrok-urls/")
        async def update_ngrok_url_endpoint(request: Request):
            """
            Update or add a new ngrok URL for a given API key.
            Expects a JSON payload with 'api_key' and 'ngrok_url'.
            """
            data = await request.json()
            api_key = data.get('api_key')
            ngrok_url = data.get('ngrok_url')

            if not api_key or not ngrok_url:
                raise HTTPException(
                    status_code=400, detail="api_key and ngrok_url are required")

            # Use the S3Manager instance to update the ngrok URL
            update_response = self.s3_manager.update_ngrok_url(
                api_key, ngrok_url)
            return update_response

        # New Endpoint: Get ngrok URL
        @self.app.get("/ngrok-urls/{api_key}")
        async def get_ngrok_url_endpoint(api_key: str):
            """
            Retrieve the ngrok URL for a given API key.
            """
            ngrok_url = self.s3_manager.load_ngrok_url(api_key)
            if not ngrok_url:
                raise HTTPException(
                    status_code=404, detail=f"No ngrok URL found for API key {api_key}")
            return {"api_key": api_key, "ngrok_url": ngrok_url}


# Create an instance of the GatewayAPI class
gateway_instance = GatewayAPI()

# Set the FastAPI app to use the class-based instance
app = gateway_instance.app
