import logging
from functools import lru_cache
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
from dotenv import load_dotenv
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

        # Initialize logger
        self.logger = logging.getLogger("GatewayAPI")
        logging.basicConfig(level=logging.INFO)  # Set logging level

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
        print(f"DEBUG: Retrieving ngrok URL for API key {api_key}...")
        if api_key not in self.ngrok_url_cache:
            self.logger.warning(
                "API Key %s not found in cache. Attempting to update from S3...", api_key)
            self.update_ngrok_url_from_s3(api_key)
        ngrok_url = self.ngrok_url_cache.get(api_key)
        if not ngrok_url:
            self.logger.error(
                "Failed to update ngrok URL for %s. Cache state: %s", api_key, self.ngrok_url_cache)
        return ngrok_url

    def update_ngrok_url_from_s3(self, api_key: str) -> str:
        """Fetch and update the latest ngrok URL from S3 for the given API key."""
        ngrok_url = self.s3_manager.load_ngrok_url(api_key)
        if ngrok_url:
            # Forcefully update the cache with the latest ngrok URL
            self.ngrok_url_cache[api_key] = ngrok_url
            print(f"DEBUG: Updated ngrok URL cache for {api_key}: {ngrok_url}")
            self.logger.info(
                "Updated ngrok URL cache for %s: %s", api_key, ngrok_url)
            print(f"DEBUG: Current ngrok URL Cache: {self.ngrok_url_cache}")
            self.logger.info(
                "Current ngrok URL Cache state: %s", self.ngrok_url_cache)

            # Manually invalidate the LRU cache to ensure fresh values are used
            self.get_cached_ngrok_url.cache_clear()
        else:
            self.logger.error(
                "Failed to retrieve ngrok URL for %s from S3.", api_key)
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
            if request.url.path == "/":
                return await call_next(request)

            api_key = request.headers.get("x-api-key")
            if not api_key:
                return JSONResponse(status_code=401, content={"detail": "Missing API Key"})

            if api_key not in self.api_keys:
                return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})

            # Use ngrok URL cache for each request dynamically based on the API key
            self.update_ngrok_url_from_s3(api_key)
            # Retrieve the ngrok URL after updating
            ngrok_url = self.ngrok_url_cache.get(api_key)

            # Debug log for inspecting the ngrok URL
            self.logger.info(
                "Retrieved ngrok URL for API key %s: %s", api_key, ngrok_url)

            # Correctly update the request scope with the ngrok URL
            if ngrok_url and ngrok_url.startswith("https://"):
                # Ensure correct host format
                ngrok_host = ngrok_url.replace("https://", "").split("/")[0]
                self.logger.info(
                    "Updating request scope for server: %s", ngrok_host)
                request.scope["server"] = (ngrok_host, 443)
            else:
                self.logger.error("Invalid ngrok URL detected: %s", ngrok_url)
                return JSONResponse(status_code=500, content={"detail": "Invalid ngrok URL"})

            return await call_next(request)

    def invalidate_ngrok_cache(self, api_key: str):
        """Forcefully invalidate the in-memory cache for the given API key."""
        if api_key in self.ngrok_url_cache:
            print(f"DEBUG: Invalidating cache for API key: {api_key}")
            del self.ngrok_url_cache[api_key]

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

            # Debug log to check the value of ngrok_url before use
            self.logger.info(
                "Retrieved ngrok URL for API key '%s': %s", api_key, ngrok_url)

            if not ngrok_url or not ngrok_url.startswith("https://"):
                # If invalid, force a refresh from S3
                self.update_ngrok_url_from_s3(api_key)
                ngrok_url = self.ngrok_url_cache.get(api_key)
                self.logger.info(
                    "After forced refresh, ngrok URL for %s is: %s", api_key, ngrok_url)

                if not ngrok_url or not ngrok_url.startswith("https://"):
                    return JSONResponse(status_code=500, content={"detail": f"Invalid ngrok URL for API key {api_key} even after refresh."})

            # Debug log for tracing the request
            print(f"DEBUG: Making request to \
                  {ngrok_url}/files/structure with API key: {api_key}")

            # Use the ngrok URL dynamically updated by the middleware
            try:
                response = requests.get(
                    f"{ngrok_url}/files/structure", timeout=self.timeout)

                # Check if response is None or has no content
                if not response or response.status_code != 200:
                    raise HTTPException(
                        status_code=500, detail="Error retrieving file structure. Response is invalid or empty."
                    )

                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                # Add additional logging to capture the full error
                self.logger.error(
                    "Failed request to %s/files/structure with exception: %s", ngrok_url, e)
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving file structure: {str(e)}"
                ) from e

        @self.app.post("/files/content")
        async def get_file_content(request: Request, request_data: dict):
            """
            Retrieve the content of specified files from the Codebase Query API.
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
                response = requests.post(
                    f"{ngrok_url}/files/content", json=request_data, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(
                    status_code=500, detail=f"Error retrieving file content: {str(e)}"
                ) from e

        @self.app.post("/ngrok-urls/")
        async def update_ngrok_url_endpoint(request: Request):
            """Update or add a new ngrok URL for a given API key."""
            data = await request.json()
            api_key = data.get('api_key')
            ngrok_url = data.get('ngrok_url')

            if not api_key or not ngrok_url:
                raise HTTPException(
                    status_code=400, detail="api_key and ngrok_url are required"
                )

            # Use the S3Manager instance to update the ngrok URL
            update_response = self.s3_manager.update_ngrok_url(
                api_key, ngrok_url)

            # Invalidate the in-memory cache for the updated API key
            self.invalidate_ngrok_cache(api_key)

            return update_response

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
