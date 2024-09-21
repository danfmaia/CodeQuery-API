import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pathspec

from app_config import AppConfig

# Load environment variables from .env file
load_dotenv()

# Get project configuration from environment variables
PROJECT_PATH = os.getenv('PROJECT_PATH', './')
print(f"PROJECT_PATH: {PROJECT_PATH}")

# Load multiple ignore files
AGENTIGNORE_FILES = os.getenv('AGENTIGNORE_FILES', '[]')

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


def load_ignore_spec():
    """Load patterns from multiple ignore files using pathspec."""
    ignore_files = eval(AGENTIGNORE_FILES)  # Parse the string into a list
    combined_spec = None

    for ignore_file in ignore_files:
        if os.path.exists(ignore_file):
            with open(ignore_file, 'r', encoding='utf-8') as f:
                ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', f)
                # Combine patterns from all ignore files
                if combined_spec:
                    combined_spec += ignore_spec
                else:
                    combined_spec = ignore_spec
    return combined_spec


def is_ignored(path, ignore_spec):
    """Check if a path should be ignored based on the loaded patterns."""
    # Normalize path to ensure proper matching, especially for nested directories
    normalized_path = os.path.normpath(path)
    return ignore_spec.match_file(normalized_path) if ignore_spec else False


@app.route('/files/structure', methods=['GET'])
def get_file_structure():
    """
    Retrieves the project directory structure for AI analysis.

    Returns:
        dict: JSON object representing the project’s files and directories.
    """
    ignore_spec = load_ignore_spec()

    def get_directory_structure(root_dir):
        """Recursively builds the directory structure, ignoring files based on the ignore spec."""
        dir_structure = {}
        for dirpath, dirnames, filenames in os.walk(root_dir):
            folder = os.path.relpath(dirpath, root_dir)
            normalized_folder = os.path.normpath(folder)

            # Check if the folder or any files should be ignored
            if is_ignored(normalized_folder, ignore_spec):
                continue

            dirnames[:] = [d for d in dirnames if not is_ignored(
                os.path.normpath(os.path.join(folder, d)), ignore_spec)]
            filenames = [f for f in filenames if not is_ignored(
                os.path.normpath(os.path.join(folder, f)), ignore_spec)]

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
    load_ignore_spec()
    app.run(host='0.0.0.0', port=5001)
