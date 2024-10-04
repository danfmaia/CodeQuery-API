# src/app.py

import os
import logging
import pathspec
from flask import Flask, request, jsonify
from dotenv import load_dotenv


from src.ngrok_manager import NgrokManager
from src.services.file_service import FileService


class CodeQueryAPI:
    """CodeQueryAPI is a Flask-based application managing ngrok tunnels and exposing API endpoints."""

    def __init__(self):
        # Initialize environment variables and configurations
        load_dotenv()
        self.project_path = os.getenv('PROJECT_PATH', './')
        self.agentignore_files = os.getenv('AGENTIGNORE_FILES', '[]')
        self.ngrok_manager = NgrokManager()
        self.file_service = FileService(
            self.project_path, self.agentignore_files)  # Initialize FileService

        # Initialize Flask app and logging
        self.app = Flask(__name__)
        self.logger = logging.getLogger('flask_app')
        self.configure_logging()
        self.setup_routes()
        self.setup_log_filters()

    def configure_logging(self):
        """Configure logging for the application."""
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def ensure_ngrok_tunnel(self):
        """Ensure the ngrok tunnel is correctly set up and synchronized."""
        print("Ensuring ngrok tunnel is set up...")
        if not self.ngrok_manager.check_ngrok_status():
            print("ngrok tunnel not running or not synchronized. Setting up...")
            self.ngrok_manager.setup_ngrok()
        else:
            print("ngrok tunnel is already running and synchronized with the gateway.")

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
        @self.app.route('/files/structure', methods=['GET'])
        def get_file_structure():
            """Retrieves the project directory structure for AI analysis."""
            structure = self.file_service.get_directory_structure()
            return jsonify(structure)

        @self.app.route('/files/content', methods=['POST'])
        def get_file_content():
            """Retrieves content of specified files for AI processing."""
            data = request.json
            file_paths = data.get('file_paths', [])
            if not file_paths:
                return jsonify({"error": "No file paths provided"}), 400

            content, status = self.file_service.get_file_content(file_paths)
            return jsonify(content), status

    def run(self):
        """Run the Flask application."""
        self.app.run(host='0.0.0.0', port=5001)


# Entry point for running the application
if __name__ == '__main__':
    api = CodeQueryAPI()
    api.ensure_ngrok_tunnel()
    api.run()
