import os
from dotenv import load_dotenv
from src.app import CodeQueryAPI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

if __name__ == "__main__":
    # Initialize the local-only version of the Core API without ngrok setup
    api = CodeQueryAPI.init_local_service()
    api.run()
