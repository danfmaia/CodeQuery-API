# CodeQuery API

![CodeQueryGPT cover artwork](./assets/social_CodeQueryAPI.png)

**CodeQuery™ API** is a lightweight and efficient Python/Flask tool designed to enable AI assistants—such as custom GPTs—to navigate and interact with local code. With this API, LLM agents\* can effortlessly query project structures and retrieve up-to-date file contents, helping developers efficiently explore and manage large codebases. By adhering to customizable ignore patterns via `.agentignore`, the API ensures that only relevant files are probed, making it an invaluable tool for AI-driven code analysis and development.

\* An LLM agent is the decision-making component of an AI assistant. Read more about about agents [in this article](https://python.langchain.com/v0.1/docs/modules/agents/). (You don't necessarily need to know about them to use CodeQuery, but a bit of knowledge is beneficial.)

🤖 **Curious Fact**: During its development, the **CodeQuery API** was an integral part of its own creation process, being used to analyze, write, and debug its own files while the project evolved. This unique feedback loop made it a participant in its own development stages!

## Features

- **Designed for AI Assistants**: This API was specifically designed to integrate with AI assistants such as custom GPTs, providing them with efficient access to project file structures and contents.
- **Retrieve Project Structure**: Get a detailed view of the project’s directories and files, excluding those specified in the `.agentignore` file.
- **Retrieve File Contents**: Access the contents of specific files in the project, with error handling for non-existent paths.
- **Custom Ignore Patterns**: Utilize `.agentignore` for specifying which files or directories to exclude from the structure retrieval.

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

The `.agentignore` file works similarly to `.gitignore`, allowing you to specify files and directories that should be excluded from file structure queries (`/files/structure` endpoint).

**Example**:

```plaintext
# General
.git/
.gitignore
.vscode/
assets/
public/

# Python
src/__pycache__/
tests/__pycache__/
__pycache__/
venv/
.benchmarks/
.pytest_cache/
.env
requirements.txt

# JavaScript
node_modules/
package-lock.json
package.json
```

## Environment Variables

You can and should customize the **CodeQuery API** using environment variables defined in a `.env` file.

- **`PROJECT_PATH`**: Set this variable to the relative path of the project you are working on.
- **`AGENTIGNORE_FILE_1`**: Change this if you want another file (such as `.gitignore`) to determine which files are to be ignored for the `/files/structure` endpoint. Note that those files can still be accessed by the `/files/content/` endpoint.

Example `.env` file:

```
PROJECT_PATH=../your-project/
AGENTIGNORE_FILE_1=.agentignore
```

## Installation and Setup

### Prerequisites

- Python 3.8+ (3.12 recommended)
- Flask

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/CodeQuery-API.git
   cd CodeQuery-API
   ```

2. Install dependencies:

   ```bash
   sudo apt-get install jq
   pip install -r requirements.txt
   ```

3. Activate local environment && Run the Flask application:

   ```bash
   conda activate venv/ && python app.py
   ```

4. The API will be available at `http://localhost:5001`.

## Testing

Before testing the public endpoints, ensure that the core API tests located in the `tests/` directory are passing. Running these tests ensures the core functionality is working as expected.

### Running Core API Tests

1. Install `pytest` if you haven’t already:

   ```bash
   conda activate venv/ && pip install pytest
   ```

2. Run the tests:

   ```bash
   export PYTHONPATH="$PYTHONPATH:/home/danfmaia/_repos/CodeQuery/CodeQuery-API" && pytest tests/
   ```

   This will execute all tests in the `tests/` directory and ensure the core API is functioning correctly.

Once the core tests have passed, you can proceed to test the public endpoints.

### Testing the Public API (Gateway)

You can use **curl** commands or Postman to interact with the public API.

#### Testing the Project Structure Retrieval

```bash
curl -H "X-API-KEY: <your-api-key>" http://localhost:5001/files/structure
```

#### Testing File Content Retrieval

```bash
curl -X POST -H "X-API-KEY: <your-api-key>" -d '{"file_paths": ["app.py", "requirements.txt"]}' http://localhost:5001/files/content
```

You can modify the request body to include different file paths and test how the API handles file retrieval and error scenarios.

```

## Creating your own custom GPT for using this API

This API was designed to be used by custom AI assistants. If you are a ChatGPT Premium user, you can create a custom GPT using the **ChatGPT Builder**.

### Steps:

1. Go to the [GPT Builder](https://chatgpt.com/gpts/editor/g-vKMjAxftT) in your ChatGPT Premium account.
2. Access the **Create** tab.
3. Send the following prompt to the GPT Builder to create your custom GPT:

```

Name: CodeQueryGPT

Description: Helps developers analyze code, debug issues, and develop features, by leveraging an API to retrieve project structure and files.

Instructions: You are CodeQueryGPT, an AI specialized in actively assisting with software development tasks by querying project files, analyzing code structure, answering questions, and providing direct coding support. You use an external API to fetch the latest file structures and retrieve file contents as needed. Your primary goal is to engage in code analysis, feature development, debugging, and understanding code dependencies, while actively contributing to the coding process. Whether through refactoring, writing new code, or suggesting improvements, you play an active role in the developer's workflow. Your core functionality includes querying the structure of the project to reason about which files are relevant to a user query, retrieving the contents of specific files when requested, and then using the file content to answer queries or write new code directly. Your responses must be clear, concise, and action-oriented, focusing on assisting users with writing or adjusting code, debugging errors, and improving overall code quality. You should prioritize using the information retrieved from the API, interact with the '/files/structure' and '/files/content' endpoints to gather the necessary context, and explain which files are being used. Where relevant, you will identify key dependencies in the codebase, such as files calling others or key functions, and actively engage in writing new code to extend or improve features.

Conversation Starters:

- Analyse the current project structure and main files.
- Help me investigate and debug an issue in the code.
- I need assistance in developing a new feature.
- Analyze the main files and help me refactor them for better performance.

````

You can of course tweak some of the settings above.

4. Once the GPT is created, go to the **Configure** tab.
5. Enable the **"Code Interpreter & Data Analysis"** option.
6. Create a new **Action** by providing the following **OpenAPI schema**:

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "CodeQuery API",
    "description": "A Flask API to retrieve the file structure and contents of a project directory",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "<YOUR-GENERATED-NGROK-URL>"
    }
  ],
  "paths": {
    "/files/structure": {
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
    "/files/content": {
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
````

7. Make sure to update the `"servers.url"` field with your **ngrok** HTTPS URL, which you generate by running `ngrok http 5001` while the API is running locally.

## Privacy

For information on how data is handled by this API, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
