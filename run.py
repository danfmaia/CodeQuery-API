from src.app import CodeQueryAPI

if __name__ == "__main__":
    api = CodeQueryAPI()
    api.ensure_ngrok_tunnel()
    api.run()
