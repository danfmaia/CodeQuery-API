import os
from fastapi import FastAPI, Request, HTTPException
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

NGROK_URL = os.getenv("NGROK_URL")
print(f"NGROK_URL: {NGROK_URL}")  # Add this for debugging
TIMEOUT = 10

# Load API keys from environment variables (comma-separated keys)
API_KEYS = {
    key: f"User{index + 1}" for index, key in enumerate(os.getenv("API_KEYS").split(","))
}


@app.middleware("http")
async def api_key_validator(request: Request, call_next):
    """
    Middleware to validate API Key.
    """
    api_key = request.headers.get("x-api-key")
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    response = await call_next(request)
    return response


@app.get("/")
def read_root():
    """
    Server health check.
    """
    return {"message": "FastAPI is running"}


@app.get("/files/structure")
async def get_file_structure():
    """
    Retrieve the file structure from the Codebase Query API via the ngrok URL.

    Returns:
        dict: The directory and file structure of the project.
    """
    try:
        response = requests.get(
            f"{NGROK_URL}/files/structure", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Explicitly re-raising the HTTPException with the original exception
        raise HTTPException(
            status_code=500, detail=f"Error retrieving file structure: {str(e)}") from e


@app.post("/files/content")
async def get_file_content(request_data: dict):
    """
    Retrieve the content of specified files from the Codebase Query API.

    Args:
        request_data (dict): A dictionary containing the file paths to retrieve.

    Returns:
        dict: The content of the requested files.
    """
    try:
        response = requests.post(
            f"{NGROK_URL}/files/content", json=request_data, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Explicitly re-raising the HTTPException with the original exception
        raise HTTPException(
            status_code=500, detail=f"Error retrieving file content: {str(e)}") from e
