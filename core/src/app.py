import os
import logging
import pathspec
from flask import Flask, request, jsonify


from src.ngrok_manager import NgrokManager
from src.file_service import FileService


class CodeQueryAPI:
    """CodeQueryAPI is a Flask-based application managing ngrok tunnels and exposing API endpoints."""

    def __init__(self, use_ngrok=True):
        # Initialize environment variables and configurations
        self.project_path = os.getenv('PROJECT_PATH', './')
        self.agentignore_files = os.getenv('AGENTIGNORE_FILES', '[]')

        # Log project path and ignore files
        self.logger = logging.getLogger('flask_app')
        self.logger.info("Checking project path: %s", self.project_path)
        self.logger.info("Agent ignore files: %s", self.agentignore_files)

        # Initialize FileService with project configurations
        self.file_service = FileService(
            self.project_path, self.agentignore_files)

        # Initialize Flask app and logging
        self.app = Flask(__name__)
        self.configure_logging()
        self.setup_routes()
        self.setup_log_filters()

        if use_ngrok:
            # Initialize ngrok manager only if needed
            self.ngrok_manager = NgrokManager()

    @classmethod
    def init_local_service(cls):
        """Initialize the Core service without ngrok setup."""
        # Set up a simpler local version of the Core without Ngrok dependency
        instance = cls(use_ngrok=False)
        instance.logger.info(
            "Starting CodeQuery in local-only mode (no ngrok tunnel).")
        return instance

    def configure_logging(self):
        """Configure logging for the application."""
        self.logger.setLevel(logging.INFO)

        # Use StreamHandler for Docker environment
        formatter = logging.Formatter('%(asctime)s - %(message)s')

        # Console handler for container logs
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Optional: Additional handlers can be added here if needed

    def ensure_ngrok_tunnel(self):
        """Ensure the ngrok tunnel is correctly set up and synchronized."""
        self.logger.info("Ensuring ngrok tunnel is set up...")

        try:
            if not self.ngrok_manager.check_ngrok_status():
                self.logger.info(
                    "ngrok tunnel not running or not synchronized. Setting up...")
                try:
                    self.ngrok_manager.setup_ngrok()
                except Exception as e:
                    self.logger.error(f"Error setting up ngrok: {str(e)}")
                    self.logger.warning(
                        "Continuing without Gateway registration...")
                    return True

            # Verify ngrok health after setup
            if not self.ngrok_manager.check_ngrok_health():
                self.logger.error("ngrok health check failed after setup.")
                self.logger.warning(
                    "Continuing without Gateway registration...")
                return True

            self.logger.info("ngrok tunnel is running and synchronized.")
            return True
        except Exception as e:
            self.logger.error(f"Error ensuring ngrok tunnel: {str(e)}")
            self.logger.warning("Continuing without Gateway registration...")
            return True

    def setup_log_filters(self):
        """Apply filters to the access logs."""
        def filter_access_logs(record):
            return not ("GET /" in record.getMessage() or "POST /" in record.getMessage())

        access_logger = logging.getLogger('werkzeug')
        access_logger.setLevel(logging.INFO)

        access_handler = logging.StreamHandler()
        access_handler.addFilter(filter_access_logs)
        access_logger.addHandler(access_handler)

    def load_ignore_spec(self):
        """Load patterns from multiple ignore files using pathspec."""
        ignore_files = self.agentignore_files.split(',')
        combined_spec = None

        for ignore_file in ignore_files:
            if os.path.exists(ignore_file):
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    ignore_spec = pathspec.PathSpec.from_lines(
                        'gitwildmatch', f)
                    combined_spec = ignore_spec if combined_spec is None else combined_spec + ignore_spec
        return combined_spec

    def is_ignored(self, path, ignore_spec):
        """Check if a path should be ignored based on the loaded patterns."""
        normalized_path = os.path.normpath(path)
        return ignore_spec.match_file(normalized_path) if ignore_spec else False

    def setup_routes(self):
        """Define all the routes for the Flask app."""

        @self.app.route('/', methods=['GET'])
        def health_check():
            """Basic public health check to confirm server status."""
            return jsonify({"status": "Healthy", "message": "CodeQuery Core is running"}), 200

        @self.app.route('/files/structure', methods=['GET'])
        def get_file_structure():
            """Retrieves the project directory structure for AI analysis."""
            self.logger.info(
                "Incoming GET /files/structure request: %s", request.headers)
            try:
                self.logger.info(
                    "Calling FileService.get_directory_structure()...")
                structure = self.file_service.get_directory_structure()
                self.logger.info("File structure retrieved: %s", structure)
                return jsonify(structure)
            except (FileNotFoundError, IOError, ValueError, KeyError) as e:
                self.logger.error("File-related or expected error: %s", str(e))
                return jsonify({"error": "File-related or expected error", "details": str(e)}), 500
            except Exception as e:  # pylint: disable=W0718
                self.logger.error(
                    "Unexpected error retrieving file structure: %s", str(e))
                return jsonify({"error": "Unexpected error", "details": str(e)}), 500

        @self.app.route('/files/content', methods=['POST'])
        def get_file_content():
            """Retrieves content of specified files for AI processing."""
            data = request.json
            self.logger.info(
                "Incoming POST /files/content request: %s", request.headers)
            self.logger.info("Request data: %s", data)

            file_paths = data.get('file_paths', [])
            if not file_paths:
                self.logger.warning(
                    "No file paths provided in the request data.")
                return jsonify({"error": "No file paths provided"}), 400

            # Log FileService processing
            self.logger.info(
                "Calling FileService.get_file_content() for paths: %s", file_paths
            )
            content, status = self.file_service.get_file_content(file_paths)

            # Log each file's path and the number of characters in its content
            for file_path, file_data in content.items():
                file_content = file_data.get('content') if isinstance(
                    file_data, dict) else file_data
                if isinstance(file_content, str):
                    content_length = len(file_content)
                    self.logger.info(
                        "Retrieved file: %s with %d characters", file_path, content_length
                    )
                else:
                    self.logger.warning(
                        "Unexpected format for file content: %s", file_path
                    )

            return jsonify(content), status

    def run(self):
        """Run the Flask application."""
        try:
            local_port = int(os.getenv("LOCAL_PORT", "5001"))
            self.logger.info(
                f"Starting Flask application on port {local_port}...")
            self.app.run(host='0.0.0.0', port=local_port, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Failed to start Flask application: {str(e)}")
            raise
