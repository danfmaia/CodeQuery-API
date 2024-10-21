import os
from dotenv import load_dotenv
from src.app import CodeQueryAPI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'))


if __name__ == "__main__":
    api = CodeQueryAPI()
    api.ensure_ngrok_tunnel()
    api.run()
