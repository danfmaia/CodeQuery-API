import os
import sys
import logging
import threading
import traceback
from dotenv import load_dotenv
from src.app import CodeQueryAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


def main():
    """Main entry point for the application."""
    try:
        logger.info("Initializing CodeQueryAPI...")
        api = CodeQueryAPI()

        # Start ngrok in a separate thread to avoid blocking Flask startup
        def setup_ngrok():
            try:
                api.ensure_ngrok_tunnel()
            except Exception as e:
                logger.error(f"Error setting up ngrok: {str(e)}")
                logger.warning("Continuing without Gateway registration...")

        ngrok_thread = threading.Thread(target=setup_ngrok)
        ngrok_thread.daemon = True
        ngrok_thread.start()

        # Start the Flask application
        logger.info("Starting Flask application...")
        try:
            api.run()  # Start the Flask application
            return 0
        except Exception as e:
            logger.error(f"Failed to start Flask application: {str(e)}")
            traceback.print_exc()
            return 1

    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
