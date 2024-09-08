# Codebase Query API

**Codebase Query API** is a Flask-based API specifically designed to serve custom AI agents. This API allows AI agents to query a project's file structure and retrieve file contents programmatically. It is built to help developers explore and interact with a project's directory structure efficiently, while adhering to ignore patterns specified in `.agentignore`.

🤖 **Curious Fact**: During its development, the **Codebase Query API** was an integral part of its own creation process, being used to query and analyze its own files while the project evolved. This unique feedback loop made it a participant in its own development stages!

## Features

- **Designed for Custom AI Agents**: This API was specifically designed to integrate with custom GPT agents or other AI agents, providing them with efficient access to project file structures and contents.
- **Retrieve Project File Structure**: Get a detailed view of the project’s directories and files, excluding those specified in the `.agentignore` file.
- **Retrieve File Contents**: Access the contents of specific files in the project, with error handling for non-existent or ignored files.
- **Custom Ignore Patterns**: Utilize `.agentignore` for specifying which files or directories to exclude from the structure or content retrieval.

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

## Environment Variables

You can and should customize the **Codebase Query API** using environment variables defined in a `.env` file.

- **`PROJECT_PATH`**: Set this variable to the relative path of the project you are working on.
- **`AGENTIGNORE_FILE`**: Change this if you want another file to determine which files are to be ignored by the agent (for the `/files/structure` endpoint), such as `.gitignore`. Note that those files can still be accessed by the `/files/content/` endpoint.

Example `.env` file:

```
PROJECT_PATH=../your-project/
AGENTIGNORE_FILE=.agentignore
```

## Installation

### Prerequisites

- Python 3.8+
- Flask

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/codebase-query-api.git
   cd codebase-query-api
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

## Creating your own custom GPT for using this API

This API was designed to be used by custom AI agents. If you are a ChatGPT Premium user, you can create a custom GPT using the **ChatGPT Builder**.

### Steps:

1. Go to the [GPT Builder](https://chatgpt.com/gpts/editor/g-vKMjAxftT) in your ChatGPT Premium account.
2. Access the **Create** tab.
3. Send the following prompt to the GPT Builder to create your custom GPT:

   ```
   Name: CodebaseGPT

   Description: Helps developers analyze code, debug issues, and develop features, by leveraging an API to retrieve project files.

   Instructions: You are 'CodebaseGPT,' an AI specialized in actively assisting with software development tasks by retrieving relevant project files, answering questions, generating insights, and providing direct coding support based on the provided codebase. You use an external API to fetch the latest file structures and retrieve file contents as needed. Your primary goal is to engage in code analysis, feature development, debugging, and understanding code dependencies, while actively contributing to the coding process. Whether through refactoring, writing new code, or suggesting improvements, you play an active role in the developer's workflow. Your core functionality includes retrieving the structure of the codebase to reason about which files are relevant to a user query, retrieving the contents of specific files when requested, and then using the file content to answer queries or write new code directly. Your responses must be clear, concise, and action-oriented, focusing on assisting users with writing or adjusting code, debugging errors, and improving overall code quality. You should prioritize using the information retrieved from the API, interact with the '/files/structure' and '/files/content' endpoints to gather the necessary context, and explain which files are being used. Where relevant, you will identify key dependencies in the codebase, such as files calling others or key functions, and actively engage in writing new code to extend or improve features.

   Conversation Starters:
   - Analyze the current codebase in a general way.
   - Help me investigate and debug an issue in the code.
   - I need assistance in developing a new feature.
   - Analyze the main files and help me refactor them for better performance.
   ```

   You can of course tweak some of the settings above.

4. Once the GPT is created, go to the **Configure** tab.
5. Enable the **"Code Interpreter & Data Analysis"** option.
6. Create a new **Action** by providing the following **OpenAPI schema**:

   ```json
   {
     "openapi": "3.1.0",
     "info": {
       "title": "Codebase Query API",
       "description": "A Flask API to retrieve the file structure and contents of a project directory",
       "version": "1.0.0"
     },
     "servers": [
       {
         "url": "<YOUR-GENERATED-NGROK-URL>"
       }
     ],
     "paths": {
       "/filestructure": {
         "get": {
           "summary": "Retrieve the file structure",
           "description": "Returns the file structure of the project directory in a nested format, showing directories and files.",
           "operationId": "getFileStructure",
           "responses": {
             "200": {
               "description": "Successful response with the file structure",
               "content": {
                 "application/json": {
                   "schema": {
                     "type": "object",
                     "properties": {
                       "directories": {
                         "type": "array",
                         "items": {
                           "type": "string"
                         },
                         "description": "List of directory names"
                       },
                       "files": {
                         "type": "array",
                         "items": {
                           "type": "string"
                         },
                         "description": "List of file names"
                       }
                     }
                   }
                 }
               }
             }
           }
         }
       },
       "/retrievefiles": {
         "post": {
           "summary": "Retrieve file contents",
           "description": "Accepts a list of file paths and returns their contents or an error message if the file does not exist.",
           "operationId": "retrieveFiles",
           "requestBody": {
             "content": {
               "application/json": {
                 "schema": {
                   "type": "object",
                   "properties": {
                     "file_paths": {
                       "type": "array",
                       "items": {
                         "type": "string"
                       },
                       "description": "A list of file paths to retrieve"
                     }
                   },
                   "required": ["file_paths"]
                 }
               }
             }
           },
           "responses": {
             "200": {
               "description": "Successful response with file contents",
               "content": {
                 "application/json": {
                   "schema": {
                     "type": "object",
                     "properties": {
                       "file_path": {
                         "type": "object",
                         "additionalProperties": {
                           "type": "object",
                           "properties": {
                             "content": {
                               "type": "string",
                               "description": "The content of the file"
                             },
                             "error": {
                               "type": "string",
                               "description": "Error message in case of failure"
                             }
                           }
                         }
                       }
                     }
                   }
                 }
               }
             },
             "400": {
               "description": "Error when no file paths are provided",
               "content": {
                 "application/json": {
                   "schema": {
                     "type": "object",
                     "properties": {
                       "error": {
                         "type": "string",
                         "description": "Error message"
                       }
                     }
                   }
                 }
               }
             },
             "404": {
               "description": "Error when all requested files are missing",
               "content": {
                 "application/json": {
                   "schema": {
                     "type": "object",
                     "properties": {
                       "error": {
                         "type": "string",
                         "description": "Error message"
                       }
                     }
                   }
                 }
               }
             }
           }
         }
       }
     }
   }
   ```

7. Make sure to update the `"servers.url"` field with your **ngrok** HTTPS URL, which you generate by running `ngrok http 5001` while the API is running locally.

## Privacy

For information on how data is handled by this API, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
