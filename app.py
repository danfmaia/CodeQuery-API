import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src.app_config import AppConfig


# Load environment variables from .env file
load_dotenv()

# Get project configuration from environment variables
PROJECT_PATH = os.getenv('PROJECT_PATH', './')
print(f"PROJECT_PATH: {PROJECT_PATH}")
AGENTIGNORE_FILE = os.getenv('AGENTIGNORE_FILE', '.agentignore')

app = Flask(__name__)

# Custom logger setup
logger = logging.getLogger('flask_app')
logger.setLevel(logging.INFO)

# Create a handler to log to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a logging format
formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)


def filter_access_logs(record):
    """Suppress logs that contain GET or POST requests."""
    return not ("GET /" in record.getMessage() or "POST /" in record.getMessage())


# Apply the filter to Werkzeug's access logger
access_logger = logging.getLogger('werkzeug')
access_logger.setLevel(logging.INFO)

# Get the Werkzeug access log handler and apply the filter
access_handler = logging.StreamHandler()
access_handler.addFilter(filter_access_logs)
access_logger.addHandler(access_handler)

ignored_patterns = []


app_config = AppConfig()


@app.before_request
def log_request_info():
    """Log request details before handling."""
    if request.method == 'POST':
        logger.info("Request Data: %s", request.get_json())


@app.after_request
def log_response_info(response):
    """Log response details."""
    logger.info('%s - - [%s %s] %s', request.remote_addr,
                request.method, request.path, response.status_code)
    return response


def load_agentignore():
    """Loads the .agentignore file and stores the ignored patterns."""
    ignore_path = AGENTIGNORE_FILE
    if os.path.exists(ignore_path):
        with open(ignore_path, 'r', encoding='utf-8') as f:
            app_config.ignored_patterns = [
                line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')
            ]
    else:
        app_config.ignored_patterns = []


def is_ignored(path):
    """Checks if a file or directory should be ignored based on the .agentignore patterns."""
    for pattern in app_config.ignored_patterns:
        # Normalize both the pattern and the path
        normalized_pattern = os.path.normpath(pattern).lstrip(os.sep)
        normalized_path = os.path.normpath(path).lstrip(os.sep)

        # Print statements for debugging
        # print(f"Checking path: {normalized_path}\
        #   against pattern: {normalized_pattern}")

        # Check if the path is ignored (matches the pattern exactly or starts with the pattern)
        if normalized_path == normalized_pattern or normalized_path.startswith(normalized_pattern):
            # print(f"Ignoring path: {normalized_path}")
            return True

    return False


@app.route('/files/structure', methods=['GET'])
def get_file_structure():
    """
    Retrieves the project directory structure for AI-based file navigation.

    Returns:
        dict: JSON object representing the project’s files and directories.
    """
    def get_directory_structure(root_dir):
        """Recursively builds the directory structure, ignoring files in .agentignore."""
        dir_structure = {}
        for dirpath, dirnames, filenames in os.walk(root_dir):
            folder = os.path.relpath(dirpath, root_dir)

            # Normalize the folder path and check if it's ignored
            if is_ignored(folder):
                continue

            # Filter out ignored directories and files
            dirnames[:] = [d for d in dirnames if not is_ignored(
                os.path.join(folder, d))]
            filenames = [f for f in filenames if not is_ignored(
                os.path.join(folder, f))]

            dir_structure[folder] = {
                "files": filenames,
                "directories": dirnames
            }
        return dir_structure

    file_structure = get_directory_structure(PROJECT_PATH)
    return jsonify(file_structure)


@app.route('/files/content', methods=['POST'])
def get_file_content():
    """
    Retrieves content of specified files for AI processing. 

    Parameters:
        list(string):
            file_paths: A list of file paths to retrieve. Each path should be a string.

    Returns:
        dict: JSON object with file content or error messages if files can't be accessed.
    """
    data = request.json
    file_paths = data.get('file_paths', [])

    if not file_paths:
        return jsonify({"error": "No file paths provided"}), 400

    file_contents = {}
    all_missing = True

    for file_path in file_paths:
        full_path = os.path.join(PROJECT_PATH, file_path)

        # Check if the path is a directory
        if os.path.isdir(full_path):
            file_contents[file_path] = {
                "error": "Cannot read directory: " + file_path}
            continue

        # Try to read the file
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                file_contents[file_path] = {"content": file.read()}
                all_missing = False  # At least one file exists
        except OSError as e:  # Catch specific file-related exceptions
            file_contents[file_path] = {
                "error": f"Error reading file: {str(e)}"}

    if all_missing:
        return jsonify({"error": "All requested files are missing"}), 404

    return jsonify(file_contents)


if __name__ == '__main__':
    load_agentignore()
    app.run(host='0.0.0.0', port=5001)
