# src/services/file_service.py

import logging
import os
import pathspec


class FileService:
    """
    A service class responsible for handling file structure and content retrieval.
    """

    def __init__(self, project_path, agentignore_files):
        self.project_path = project_path
        self.agentignore_files = agentignore_files
        self.logger = logging.getLogger("FileService")

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
        self.logger.debug(f"Loaded ignore spec: {combined_spec}")
        return combined_spec

    def is_ignored(self, path, ignore_spec):
        """Check if a path should be ignored based on the loaded patterns."""
        normalized_path = os.path.normpath(path)
        return ignore_spec.match_file(normalized_path) if ignore_spec else False

    def get_directory_structure(self):
        """Returns the project directory structure as a dictionary."""
        ignore_spec = self.load_ignore_spec()

        def traverse_directory(root_dir):
            dir_structure = {}
            for dirpath, dirnames, filenames in os.walk(root_dir):
                folder = os.path.relpath(dirpath, root_dir)
                normalized_folder = os.path.normpath(folder)

                # Skip ignored directories
                if self.is_ignored(normalized_folder, ignore_spec):
                    self.logger.debug(f"Ignored folder: {normalized_folder}")
                    continue

                dirnames[:] = [d for d in dirnames if not self.is_ignored(
                    os.path.normpath(os.path.join(folder, d)), ignore_spec)]
                filenames = [f for f in filenames if not self.is_ignored(
                    os.path.normpath(os.path.join(folder, f)), ignore_spec)]

                dir_structure[folder] = {
                    "files": filenames,
                    "directories": dirnames
                }
            return dir_structure

        try:
            structure = traverse_directory(self.project_path)
            self.logger.info(f"Retrieved directory structure: {structure}")
            return structure
        except Exception as e:
            self.logger.error(f"Failed to retrieve directory structure: {e}")
            raise

    def get_file_content(self, file_paths):
        """Retrieve the content of specified files."""
        file_contents = {}
        all_missing = True

        for file_path in file_paths:
            full_path = os.path.join(self.project_path, file_path)
            if os.path.isdir(full_path):
                file_contents[file_path] = {
                    "error": f"Cannot read directory: {file_path}"}
                continue

            try:
                with open(full_path, 'r', encoding='utf-8') as file:
                    file_contents[file_path] = {"content": file.read()}
                    all_missing = False
            except OSError as e:
                file_contents[file_path] = {
                    "error": f"Error reading file: {str(e)}"}

        if all_missing:
            return {"error": "All requested files are missing"}, 404

        return file_contents, 200
