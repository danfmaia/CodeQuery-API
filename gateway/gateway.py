import logging
from functools import lru_cache
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests
from dotenv import load_dotenv
from src.s3_manager import S3Manager
import secrets
import base64
import datetime


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
            # Skip authentication for root and API key generation endpoints
            if request.url.path == "/" or request.url.path == "/api-keys/generate":
                return await call_next(request)

            api_key = request.headers.get("x-api-key")
            if not api_key:
                return JSONResponse(status_code=401, content={"detail": "Missing API Key"})

            try:
                # First check in-memory keys for faster validation
                if api_key not in self.api_keys:
                    # If not in memory, try loading from S3
                    api_keys = self.s3_manager.load_encrypted_api_keys() or {}
                    if api_key not in api_keys:
                        return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})

                    # Add to in-memory cache if found in S3
                    self.api_keys[api_key] = f"User{len(self.api_keys) + 1}"

                # Load the latest key data from S3 for expiration and rate limit checks
                api_keys = self.s3_manager.load_encrypted_api_keys() or {}
                if api_key not in api_keys:
                    return JSONResponse(status_code=401, content={"detail": "Invalid API Key"})

                key_data = api_keys[api_key]
                current_time = datetime.datetime.utcnow()

                # Check expiration
                if key_data.get("expires_at"):
                    try:
                        expiration = datetime.datetime.fromisoformat(
                            key_data["expires_at"])
                        if current_time > expiration:
                            return JSONResponse(status_code=401, content={"detail": "API Key has expired"})
                    except (ValueError, TypeError) as e:
                        self.logger.error(
                            f"Error parsing expiration date: {str(e)}")
                        return JSONResponse(status_code=500, content={"detail": "Error checking key expiration"})

                # Check rate limit
                rate_limit = key_data.get("rate_limit", {})
                if rate_limit:
                    try:
                        current_minute = current_time.strftime(
                            "%Y-%m-%d %H:%M")
                        if current_minute != rate_limit.get("current_minute"):
                            # Reset counter for new minute
                            rate_limit["current_minute"] = current_minute
                            rate_limit["minute_requests"] = 0

                        if rate_limit["minute_requests"] >= rate_limit.get("requests_per_minute", 60):
                            next_minute = datetime.datetime.strptime(
                                current_minute, "%Y-%m-%d %H:%M") + datetime.timedelta(minutes=1)
                            return JSONResponse(
                                status_code=429,
                                content={
                                    "detail": "Rate limit exceeded. Please try again in the next minute.",
                                    "limit": rate_limit["requests_per_minute"],
                                    "reset_at": next_minute.isoformat()
                                }
                            )

                        # Update rate limit counters
                        rate_limit["minute_requests"] += 1
                        key_data["total_requests"] = key_data.get(
                            "total_requests", 0) + 1
                        key_data["last_used"] = current_time.isoformat()

                        # Store updated key data
                        try:
                            self.s3_manager.store_encrypted_api_keys(api_keys)
                        except Exception as e:
                            self.logger.error(
                                f"Error storing updated key data: {str(e)}")
                            # Continue processing even if storage fails
                    except Exception as e:
                        self.logger.error(
                            f"Error checking rate limit: {str(e)}")
                        return JSONResponse(status_code=500, content={"detail": "Error checking rate limit"})

                # Use ngrok URL cache for each request dynamically based on the API key
                try:
                    self.update_ngrok_url_from_s3(api_key)
                    # Retrieve the ngrok URL after updating
                    ngrok_url = self.ngrok_url_cache.get(api_key)

                    # Debug log for inspecting the ngrok URL
                    self.logger.info(
                        "Retrieved ngrok URL for API key %s: %s", api_key, ngrok_url)

                    # Correctly update the request scope with the ngrok URL
                    if ngrok_url and ngrok_url.startswith("https://"):
                        # Ensure correct host format
                        ngrok_host = ngrok_url.replace(
                            "https://", "").split("/")[0]
                        self.logger.info(
                            "Updating request scope for server: %s", ngrok_host)
                        request.scope["server"] = (ngrok_host, 443)
                        return await call_next(request)
                    else:
                        self.logger.error(
                            "Invalid ngrok URL detected: %s", ngrok_url)
                        return JSONResponse(status_code=500, content={"detail": "Invalid ngrok URL"})
                except HTTPException as e:
                    return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
                except Exception as e:
                    self.logger.error(f"Error updating ngrok URL: {str(e)}")
                    return JSONResponse(status_code=500, content={"detail": "Error updating ngrok URL"})

            except Exception as e:
                self.logger.error(f"Error in middleware: {str(e)}")
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})

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
            print(
                f"DEBUG: Making request to {ngrok_url}/files/structure with API key: {api_key}")

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
            try:
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

                # Return the response from S3Manager
                return update_response
            except Exception as e:
                self.logger.error(f"Error updating ngrok URL: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update ngrok URL: {str(e)}"
                ) from e

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

        @self.app.post("/api-keys/generate")
        async def generate_api_key(request: Request):
            """Generate a new API key for a user."""
            try:
                # Parse request body for optional settings
                data = await request.json() if request.headers.get("content-type") == "application/json" else {}

                # Get settings with defaults
                expiration_days = data.get(
                    "expiration_days", 30)  # Default 30 days
                requests_per_minute = data.get(
                    "requests_per_minute", 60)  # Default 60 rpm

                # Generate a secure random key
                random_bytes = secrets.token_bytes(32)
                new_api_key = base64.b64encode(random_bytes).decode('utf-8')

                # Calculate expiration date
                created_at = datetime.datetime.utcnow()
                expires_at = (created_at + datetime.timedelta(days=expiration_days)
                              ).isoformat() if expiration_days else None

                # Load existing API keys
                api_keys = self.s3_manager.load_encrypted_api_keys() or {}

                # Add the new key with settings
                api_keys[new_api_key] = {
                    "created_at": created_at.isoformat(),
                    "last_used": None,
                    "expires_at": expires_at,
                    "rate_limit": {
                        "requests_per_minute": requests_per_minute,
                        "current_minute": None,
                        "minute_requests": 0
                    },
                    "total_requests": 0
                }

                # Store updated keys
                try:
                    self.s3_manager.store_encrypted_api_keys(api_keys)
                except Exception as e:
                    self.logger.error(f"Error storing API key: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to store API key. Please try again later."
                    )

                # Initialize an empty entry in ngrok_urls.json for this API key
                self.s3_manager.update_ngrok_url(new_api_key, None)

                # Update the in-memory cache
                self.api_keys[new_api_key] = f"User{len(self.api_keys) + 1}"

                return {
                    "api_key": new_api_key,
                    "expires_at": expires_at,
                    "rate_limit": requests_per_minute,
                    "message": "API key generated successfully. Keep this key secure!"
                }
            except Exception as e:
                self.logger.error(f"Error generating API key: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to generate API key. Please try again later."
                )


# Create an instance of the GatewayAPI class
gateway_instance = GatewayAPI()

# Set the FastAPI app to use the class-based instance
app = gateway_instance.app
