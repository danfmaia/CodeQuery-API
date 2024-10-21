# CodeQuery Core

## Overview

The **CodeQuery Core** component is the main API service designed to provide AI assistants, like **CodeQueryGPT**, with programmatic access to project structure and file contents. It’s built with Flask and offers endpoints that facilitate efficient code navigation, analysis, and content retrieval.

## API Endpoints

### 1. Retrieve Project Structure

- **Endpoint**: `/files/structure`
- **Method**: `GET`
- **Description**: Returns the directory structure of the project, following the ignore patterns specified in `.agentignore`.

  **Response Example**:

  ```json
  {
    ".": {
      "directories": ["src", "tests"],
      "files": ["README.md", "requirements.txt"]
    }
  }
  ```

### 2. Retrieve File Contents

- **Endpoint**: `/files/content`
- **Method**: `POST`
- **Description**: Returns the content of specified files.

  **Request Example**:

  ```json
  {
    "file_paths": ["src/app.py", "src/ngrok_manager.py"]
  }
  ```

  **Response Example**:

  ```json
  {
    "src/app.py": {
      "content": "# Main application file for CodeQuery Core."
    }
  }
  ```

## .agentignore File

Specify files and directories to exclude from the structure retrieval using `.agentignore`. It functions similarly to `.gitignore`.

## Environment Variables

Configure the **CodeQuery Core** component using environment variables defined in the `.env` file:

```plaintext
PROJECT_PATH="../my-project"        # Path to the target project
AGENTIGNORE_FILES=".agentignore"   # Files to ignore
LOCAL_PORT=5001                    # Local port for the Core component
```

Load the environment variables:

```bash
source .env
```

## Testing the Core Component

### 1. Local Testing

Run the Core API locally:

```bash
python run_local.py
```

#### Health Check

```bash
curl -X GET http://127.0.0.1:5001/
```

## Exposure Options

The Core component can be exposed using various methods:

1. **Direct Localhost Access**
2. **Via Paid ngrok URL**
3. **Through Gateway**

For more details on each option, refer to the main **README**.

## License

This project is licensed under the Apache License, Version 2.0.  
You may obtain a copy of the License at:

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
