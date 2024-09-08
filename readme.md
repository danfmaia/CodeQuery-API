# AutocoderGPT API

**AutocoderGPT API** is a Flask-based API specifically designed to serve the **AutocoderGPT** agent, a custom agent available in the GPT Store. This API allows AI agents, like **AutocoderGPT**, to query a project's file structure and retrieve file contents programmatically. It is built to help developers explore and interact with a project's directory structure efficiently, while adhering to ignore patterns specified in `.agentignore`.

**Curious Fact**: During its development, the **AutocoderGPT API** was an integral part of its own creation process, being used to query and analyze its own files while the project evolved. This unique feedback loop made it a participant in its own development stages!

---

## Features

- **Specifically Designed for AutocoderGPT**: This API was developed with the **AutocoderGPT** agent in mind, ensuring seamless integration and performance for file-based interactions.
- **Retrieve Project File Structure**: Get a detailed view of the project’s directories and files, excluding those specified in the `.agentignore` file.
- **Retrieve File Contents**: Access the contents of specific files in the project, with error handling for non-existent or ignored files.
- **Custom Ignore Patterns**: Utilize `.agentignore` for specifying which files or directories to exclude from the structure or content retrieval.

---

## API Endpoints

### 1. **Retrieve Project Structure**

- **Endpoint**: `/files/structure`
- **Method**: `GET`
- **Description**: Retrieves the project directory structure, respecting the ignore patterns in `.agentignore`.
- **Response Example**:
  ```json
  {
    ".": {
      "directories": ["src", "tests"],
      "files": [".agentignore", "openapi.json"]
    },
    "src": {
      "directories": [],
      "files": ["app.py"]
    },
    "tests": {
      "directories": [],
      "files": ["test_app.py"]
    }
  }
  ```

### 2. **Retrieve File Contents**

- **Endpoint**: `/files/content`
- **Method**: `POST`
- **Description**: Retrieves the content of specified files.
- **Request Body**:
  ```json
  {
    "file_paths": ["src/app.py", "tests/test_app.py"]
  }
  ```
- **Response Example**:

  ```json
  {
    "src/app.py": {
      "content": "# Content of app.py file..."
    },
    "tests/test_app.py": {
      "content": "# Content of test_app.py file..."
    }
  }
  ```

- **Error Example (File Not Found)**:
  ```json
  {
    "error": "All requested files are missing"
  }
  ```

---

## .agentignore File

The `.agentignore` file works similarly to `.gitignore`, allowing you to specify files and directories that should be excluded from file structure and content queries.

**Example**:

```plaintext
# Ignore Python cache and virtual environment directories
__pycache__/
venv/

# Ignore directories
.benchmarks/
.pytest_cache/
.git/

# Ignore files
.env
.gitignore
pytest.ini
requirements.txt
```

---

## Installation

### Prerequisites

- Python 3.8+
- Flask

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/autocoder-gpt-api.git
   cd autocoder-gpt-api
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the Flask application:

   ```bash
   python src/app.py
   ```

4. The API will be available at `http://localhost:5001`.

---

## Running Tests

Unit tests are provided for key API functionality using `pytest`. To run the tests, use the following command:

```bash
pytest tests/test_app.py
```

The tests cover:

- Loading the `.agentignore` file
- Retrieving the file structure
- Retrieving the contents of specific files
- Handling non-existent or ignored files

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
