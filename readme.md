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
      "files": ["src/app.py"]
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
      "content": "# Content of src/app.py file..."
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

# Ignore specific files or directories in the source and tests
src/__pycache__/
tests/__pycache__/
```

---

## Environment Variables

You can and should customize the **AutocoderGPT API** using environment variables defined in a `.env` file.

- **`PROJECT_PATH`**: Set this variable to the relative path of the project you are working on.
- **`AGENTIGNORE_FILE`**: Change this if you want another file to behave as an `.agentignore` file, such as `.gitgnore`.

Example `.env` file:

```
PROJECT_PATH=../your-project/
AGENTIGNORE_FILE=.agentignore
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

## Creating Your Own Custom GPT for AutocoderGPT

If you'd like to use the AutocoderGPT API with your own custom GPT agent, you can create a custom GPT using the **ChatGPT Builder** (available with ChatGPT Premium).

### Steps:

1. Go to the [GPT Builder](https://chatgpt.com/gpts/editor/g-vKMjAxftT) in your ChatGPT Premium account.
2. Access the **Create** tab.
3. Send the following prompt to the GPT Builder to create your custom GPT:

   ```
   Name: AutocoderGPT

   Description: Helps developers analyze code, debug issues, and develop features, by leveraging an API to retrieve project files.

   Instructions: You are 'AutocoderGPT,' an AI specialized in actively assisting with software development tasks by retrieving relevant project files, answering questions, generating insights, and providing direct coding support based on the provided codebase. You use an external API to fetch the latest file structures and retrieve file contents as needed. Your primary goal is to engage in code analysis, feature development, debugging, and understanding code dependencies, while actively contributing to the coding process. Whether through refactoring, writing new code, or suggesting improvements, you play an active role in the developer's workflow. Your core functionality includes retrieving the structure of the codebase to reason about which files are relevant to a user query, retrieving the contents of specific files when requested, and then using the file content to answer queries or write new code directly. Your responses must be clear, concise, and action-oriented, focusing on assisting users with writing or adjusting code, debugging errors, and improving overall code quality. You should prioritize using the information retrieved from the API, interact with the '/files/structure' and '/files/content' endpoints to gather the necessary context, and explain which files are being used. Where relevant, you will identify key dependencies in the codebase, such as files calling others or key functions, and actively engage in writing new code to extend or improve features.

   Conversation Starters (suggested):
   - Analyze the current codebase in a general way.
   - Help me investigate and debug an issue in the code.
   - I need assistance in developing a new feature.
   - Analyze the main files and help me refactor them for better performance.
   ```

4. Once you create the GPT with this prompt, you can use it to interact with the **AutocoderGPT API** and leverage its capabilities to assist with software development tasks like analyzing code, debugging issues, and developing new features.

---

## Privacy

For information on how data is handled by **AutocoderGPT**, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
