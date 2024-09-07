from flask import Flask, request, jsonify
import os

PROJECT_PATH = "../portfolio/src"

app = Flask(__name__)


@app.route('/filestructure', methods=['GET'])
def get_file_structure():
    """
    Endpoint to retrieve the file structure of the project directory.

    This endpoint returns a nested dictionary representing the folder structure
    and file paths of the current project directory. This can be used by the agent
    to reason about which files to access based on the user's query.

    Returns:
        dict: A JSON object representing the project file structure.
    """
    def get_directory_structure(root_dir):
        """
        Recursively builds the directory structure.
        """
        dir_structure = {}
        for dirpath, dirnames, filenames in os.walk(root_dir):
            folder = os.path.relpath(dirpath, root_dir)
            dir_structure[folder] = {
                "files": filenames, "directories": dirnames}
        return dir_structure

    file_structure = get_directory_structure(PROJECT_PATH)
    return jsonify(file_structure)


@app.route('/retrievefiles', methods=['POST'])
def retrieve_files():
    """
    Endpoint to retrieve file content based on the selected file paths.

    This endpoint accepts a list of file paths and returns their content. It is 
    designed to allow the agent to gather the content of selected files based on 
    the reasoning of the file structure and prompt the agent with the right context.

    Returns:
        dict: A JSON object containing the file names and their corresponding content.
    """
    data = request.json
    file_paths = data.get('file_paths', [])

    if not file_paths:
        return jsonify({"error": "No file paths provided"}), 400

    file_contents = {}
    all_missing = True

    for file_path in file_paths:
        full_path = os.path.join(PROJECT_PATH, file_path)
        try:
            with open(full_path, 'r') as file:
                file_contents[file_path] = file.read()
                all_missing = False  # At least one file exists
        except Exception as e:
            file_contents[file_path] = f"Error reading file: {str(e)}"

    if all_missing:
        return jsonify({"error": "All requested files are missing"}), 404

    return jsonify(file_contents)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
