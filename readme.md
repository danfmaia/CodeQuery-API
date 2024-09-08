# AutocoderGPT API

**AutocoderGPT API** is a Flask-based API specifically designed to serve the [AutocoderGPT agent](https://chatgpt.com/g/g-p6iZtgfWt-autocodergpt), a custom agent available in the GPT Store. This API allows this or similar agents to query a project's file structure and retrieve file contents programmatically. It is built to help developers explore and interact with a project's directory structure efficiently, while adhering to ignore patterns specified in `.agentignore`.

🤖 **Curious Fact**: During its development, the **AutocoderGPT API** was an integral part of its own creation process, being used to query and analyze its own files while the project evolved. This unique feedback loop made it a participant in its own development stages!

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
    "file_paths": ["app.py", "tests/test_app.py"]
  }
  ```
- **Response Example**:

  ```json
  {
    "app.py": {
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
assets/

# Ignore files
.env
.gitignore
pytest.ini
requirements.txt
github.webp

# Ignore specific files or directories in the source and tests
src/__pycache__/
tests/__pycache__/
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
   python app.py
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

## Privacy

For information on how data is handled by **AutocoderGPT**, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
