from functools import lru_cache
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
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
        self.ngrok_url_cache = {}
        self.ngrok_url = None
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

    @lru_cache(maxsize=128)
    def get_cached_ngrok_url(self, api_key):
        """Retrieve ngrok URL from cache or update it if not present."""
        if api_key not in self.ngrok_url_cache:
            self.update_ngrok_url_from_s3(api_key)
        return self.ngrok_url_cache.get(api_key)

    def update_ngrok_url_from_s3(self, api_key: str) -> str:
        """Fetch and update the latest ngrok URL from S3 for the given API key."""
        ngrok_url = self.s3_manager.load_ngrok_url(api_key)
        if ngrok_url:
            self.ngrok_url_cache[api_key] = ngrok_url
            print(f"DEBUG: Updated ngrok URL cache for {api_key}: {ngrok_url}")
            print(f"DEBUG: Current ngrok URL Cache: {self.ngrok_url_cache}")
            return ngrok_url  # <-- Return the updated ngrok URL
        else:
            raise HTTPException(
                status_code=404, detail=f"No ngrok URL found for API key {api_key}"
            )

    def setup_middleware(self):
        """Configure the middleware for API key validation."""

        @self.app.middleware("http")
        async def api_key_validator(request: Request, call_next):
            """
            Middleware to validate API keys and dynamically set the ngrok URL for each request.
            """
            # Bypass API key validation for root health check
            if request.url.path == "/":
                return await call_next(request)

            api_key = request.headers.get("x-api-key")

            # Print the state before validation
            print(f"DEBUG: Validating API Key: {
                api_key} | Available API Keys: {self.api_keys}")

            if not api_key:
                print("DEBUG: No API Key provided.")
                return JSONResponse(status_code=401, content={"detail": "Missing API Key"})

            if api_key not in self.api_keys:
                print("DEBUG: Invalid API Key provided.")
                return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})

            # Use ngrok URL cache for each request dynamically based on the API key
            ngrok_url = self.update_ngrok_url_from_s3(api_key)

            # Rewrite the base URL using the ngrok URL
            request.scope["server"] = (ngrok_url.replace("https://", ""), 443)
            print(f"DEBUG: Rewritten server for {
                api_key}: {request.scope['server']}")

            return await call_next(request)

    def setup_routes(self):
        """Define all the routes for the gateway."""

        @self.app.get("/")
        def read_root():
            """
            Server health check.
            """
            return {"message": "FastAPI is running"}

        @self.app.get("/files/structure")
        async def get_file_structure(request: Request):
            """
            Retrieve the file structure from the Codebase Query API via the ngrok URL.
            """
            api_key = request.headers.get("x-api-key")
            if not api_key:
                raise HTTPException(status_code=401, detail="API Key missing")

            # Retrieve the ngrok URL based on the API key
            ngrok_url = self.ngrok_url_cache.get(api_key)
            if not ngrok_url:
                raise HTTPException(
                    status_code=404, detail=f"No ngrok URL found for API key {api_key}")

            print(f"DEBUG: Retrieved ngrok URL for {api_key}: {ngrok_url}")
            print(f"DEBUG: Current ngrok URL Cache: {self.ngrok_url_cache}")

            # Use the ngrok URL dynamically updated by the middleware
            try:
                response = requests.get(
                    f"{ngrok_url}/files/structure", timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving file structure: {str(e)}"
                ) from e

        @self.app.post("/files/content")
        async def get_file_content(request: Request, request_data: dict):
            """
            Retrieve the content of specified files from the Codebase Query API.
            """
            try:
                # Use the ngrok URL dynamically updated by the middleware
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
