# CodeQuery API

![CodeQueryGPT cover artwork](./assets/social_CodeQueryAPI.png)

**CodeQuery™ API** is a lightweight and efficient Python/Flask tool designed to enable AI assistants—such as custom GPTs—to navigate and interact with local code. With this API, LLM agents\* can effortlessly query project structures and retrieve up-to-date file contents, helping developers efficiently explore and manage large codebases. By adhering to customizable ignore patterns, the API ensures that only relevant files are probed, making it an invaluable tool for AI-driven code analysis and development.

\* An LLM agent is the decision-making component of an AI assistant. Read more about agents [in this article](https://python.langchain.com/v0.1/docs/modules/agents/).

🤖 **Curious Fact**: During its development, the **CodeQuery API** was an integral part of its own creation process, being used to analyze, write, and debug its own files while the project evolved. This unique feedback loop made it a participant in its own development stages! For more details on how the CodeQuery API has been applied, see the [Cases](#cases) section.

## Features

- **Designed for AI Assistants**: This API was specifically designed to integrate with AI assistants such as custom GPTs, providing them with efficient access to project file structures and contents.
- **Retrieve Project Structure**: Get a detailed view of the project’s directories and files.
- **Retrieve File Contents**: Access the contents of specific files in the project, with error handling for non-existent paths.
- **Custom Ignore Patterns**: Utilize `.agentignore` and/or `.gitignore` for specifying which files or directories to exclude from the structure retrieval.

## API Endpoints

### 1. **Retrieve Project Structure**

- **Endpoint**: `/files/structure`
- **Method**: `GET`
- **Description**: Retrieves the directory structure of the project, respecting the ignore patterns in `.agentignore`. This is useful for tools that need to understand the file organization, such as code editors or static analysis tools.

- **Response Example**:

  ```json
  {
    ".": {
      "directories": ["backend", "frontend", "config"],
      "files": [".env", "README.md"]
    },
    "backend": {
      "directories": ["controllers", "models", "services"],
      "files": ["app.py", "database.py"]
    },
    "frontend": {
      "directories": ["components", "pages"],
      "files": ["index.html", "app.js"]
    },
    "config": {
      "directories": [],
      "files": ["settings.yaml", "logging.conf"]
    }
  }
  ```

- **Error Scenarios**:

  - **500 Internal Server Error**: If there’s a failure in reading the directory structure, such as permission issues or corrupted files, an internal error response will be returned.

  **Example Error Response**:

  ```json
  {
    "error": "Failed to retrieve directory structure: [Detailed error message]"
  }
  ```

### 2. **Retrieve File Contents**

- **Endpoint**: `/files/content`
- **Method**: `POST`
- **Description**: Retrieves the content of specified files. Useful for directly accessing specific source files or configuration files.

- **Request Body**:

  ```json
  {
    "file_paths": ["backend/app.py", "frontend/app.js"]
  }
  ```

- **Response Example**:

  ```json
  {
    "backend/app.py": {
      "content": "# Main application file\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef index():\n    return 'Hello, World!'"
    },
    "frontend/app.js": {
      "content": "// Frontend application logic\nimport React from 'react';\nfunction App() {\n    return (<div>Hello, World!</div>);\n}"
    }
  }
  ```

- **Error Scenarios**:

  - **400 Bad Request**: If no file paths are provided in the request body.

  **Example Error Response**:

  ```json
  {
    "error": "No file paths provided in the request."
  }
  ```

  - **404 Not Found**: If all the requested file paths do not exist or are missing.

  **Example Error Response**:

  ```json
  {
    "error": "All requested files are missing"
  }
  ```

  - **422 Unprocessable Entity**: If a directory is specified instead of a file.

  **Example Error Response**:

  ```json
  {
    "frontend/components": {
      "error": "Cannot read directory: frontend/components"
    }
  }
  ```

  - **500 Internal Server Error**: If there’s a failure in reading a file due to permissions, encoding issues, or other OS-level errors.

  **Example Error Response**:

  ```json
  {
    "backend/app.py": {
      "error": "Error reading file: [Detailed error message]"
    }
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

The **CodeQuery API** can be configured using the following environment variables defined in the `.env` file located in the root directory. Customizing these variables allows you to specify which project and files the API will interact with, providing flexibility for different use cases.

```plaintext
PROJECT_PATH="../my-project"             # Set this to the root path of your project
AGENTIGNORE_FILES=".agentignore,.gitignore"  # Specify custom ignore patterns for file structure queries
LOCAL_PORT=5001                          # Port number for running the Core component locally
API_KEY="<Your API Key>"                 # Set your API key for authentication (if used)
GATEWAY_BASE_URL="<Your Gateway URL>"    # Public URL for the Gateway component (if used)

NGROK_API_URL="http://localhost:4040/api/tunnels"  # Ngrok API URL for querying tunnel status
TIMEOUT=10                               # Request timeout in seconds
```

### Key Variables to Customize

1. **`PROJECT_PATH`**: Set this variable to the root path of the project you want the CodeQuery API to work with. This path should point to the directory where your project is located (e.g., `../my-project/`). By default, it is set to `"./"`, which points to the current folder, usually the CodeQuery project itself.
2. **`AGENTIGNORE_FILES`**: Use this variable to customize which files and directories should be ignored when querying the project structure. You can specify multiple ignore files separated by commas (e.g., `.agentignore,.gitignore,.dockerignore`).

3. **`LOCAL_PORT`**: The port on which the Core component will run locally (default: `5001`).

4. **`API_KEY` (if using Gateway)**: Set your personal API key to authenticate requests to the Core and Gateway components.

5. **`GATEWAY_BASE_URL` (if using Gateway)**: Set this to the public URL of your Gateway component if using Gateway for secure access. This variable can also be left empty if not applicable.

After defining the environment variables, ensure they are loaded:

```bash
source .env
```

## Installation and Exposure

### Prerequisites

- Python 3.8+ (3.12 recommended)
- Flask

### Installation Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/danfmaia/CodeQuery-API.git
   cd CodeQuery-API
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Activate local environment:

   ```bash
   conda activate venv/
   ```

4. Choose one of the following exposure options to make the Core component accessible:

### Exposure Options

#### 1. **Using the Gateway Component**

- **Description**: This is the recommended option if you need secure access management and dynamic URL synchronization. The Gateway component acts as an intermediary, handling API key validation, ngrok URL synchronization, and request forwarding to the Core component.
- **Command**:
  ```bash
  python run.py
  ```
- **Use Case**: Ideal for secure, managed access and when operating in environments where dynamic URL management is needed.

#### 2. **Using a Paid ngrok URL**

- **Description**: With a paid ngrok plan, you can set up a permanent public URL, simplifying external access without the Gateway component. This approach only requires running the Core locally and using the ngrok URL for remote access.
- **Command**:
  ```bash
  python run_local.py
  ```
- **Use Case**: Suitable for users who prefer a straightforward setup using ngrok but need a permanent URL for consistent access.

#### 3. **Setting Up a Self-Hosted Server**

- **Description**: For users with a static IP address or a home server, you can host the Core directly using your ISP’s services. This setup avoids the need for ngrok or the Gateway but may require configuring your router and securing the connection with SSL/TLS certificates.
- **Command**:
  ```bash
  python run_local.py
  ```
- **Steps**:
  1. **Check Static IP Availability**: Verify if your ISP offers a static IP address.
  2. **Port Forwarding**: Configure your router to forward traffic on a specific port (e.g., `5001`) to the local machine running CodeQuery Core.
  3. **Domain Setup**: Consider using a custom domain to access your server.
  4. **SSL/TLS Configuration**: Use services like Let’s Encrypt to secure your server.

## Testing the CodeQuery API

This section outlines the environment variable setup and key testing commands for the Core component, including running unit tests and troubleshooting integration issues.

### Environment Variable Setup for Testing

Before running any tests, make sure to configure the necessary environment variables in the `.env` file. Here’s the complete `.env` file template:

```plaintext
PROJECT_PATH="./"
AGENTIGNORE_FILES=".agentignore,.gitignore"
LOCAL_PORT=<YOUR_LOCAL_PORT>          # Set to your preferred port, e.g., 5001
API_KEY="<YOUR_API_KEY>"              # Replace with your personal API key for testing
GATEWAY_BASE_URL="<YOUR_GATEWAY_URL>" # Set to your Gateway's public URL if applicable

NGROK_API_URL="http://localhost:4040/api/tunnels"
TIMEOUT=10
```

**Key Variables for Testing**:

1. **`API_KEY`**: The API key to authenticate requests. Set this to your personal API key.
2. **`LOCAL_PORT`**: The port on which the Core component will run locally (default: `5001`).
3. **`GATEWAY_BASE_URL`**: The base URL for the Gateway component if testing with the Gateway (e.g., `https://codequery.dev` or your custom Gateway URL).

After setting these variables, run:

```bash
source .env
```

### 1. Testing the Core Component Locally

If you’re running the Core component locally (e.g., using `run_local.py`), follow these steps:

#### Health Check (Localhost)

```bash
curl -X GET http://127.0.0.1:$LOCAL_PORT/
```

#### Retrieve Project Structure (Localhost)

```bash
curl -H "X-API-KEY: $API_KEY" http://127.0.0.1:$LOCAL_PORT/files/structure
```

#### Retrieve File Contents (Localhost)

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
  "file_paths": [
    "src/app.py",
    "src/ngrok_manager.py"
  ]
}' http://127.0.0.1:$LOCAL_PORT/files/content
```

### 2. Running Integration Tests

To verify the integration between the Core and Gateway components, use the `tests/integration_test.py` file. This test ensures that the Gateway can correctly interact with the Core API, handling ngrok URL synchronization and request forwarding.

1. **Run the Integration Test**:

   ```bash
   pytest tests/integration_test.py
   ```

   This will execute the integration test and provide a summary of the results, validating the communication between the Gateway and Core components.

### 3. Troubleshooting Common Issues

- **Ngrok URL Mismatch**: If you encounter issues with ngrok URL synchronization between the Core and Gateway, ensure that:

  - The `GATEWAY_UPLOAD_URL` is correctly set in your `.env` file.
  - The Gateway component is reachable and the API key is valid.

- **Missing Environment Variables**: Ensure all necessary environment variables (`PROJECT_PATH`, `API_KEY`, etc.) are defined in your `.env` file.

For more detailed troubleshooting steps, refer to `gateway/README.md` if you're encountering Gateway-specific issues.

## CodeQueryGPT – Creating your own custom GPT for using this API

This API was designed to be used by custom AI assistants. If you are a ChatGPT Premium user, you can create a custom GPT using the **ChatGPT Builder**.

### Steps:

1. Go to the [GPT Builder](https://chatgpt.com/gpts/editor/g-vKMjAxftT) in your ChatGPT Premium account.
2. Access the **Create** tab.
3. Send the following prompt to the GPT Builder to create your custom GPT:

```

Name: CodeQueryGPT

Description: Helps developers analyze code, debug issues, and develop features, by leveraging an API to retrieve project structure and files.

Instructions: You are CodeQueryGPT, an AI specialized in actively assisting with software development tasks by querying project files, analyzing code structure, answering questions, and providing direct coding support. You use an external API to fetch the latest file structures and retrieve file contents as needed. Your primary goal is to engage in code analysis, feature development, debugging, and understanding code dependencies, while actively contributing to the coding process. Whether through refactoring, writing new code, or suggesting improvements, you play an active role in the developer's workflow. Your core functionality includes querying the structure of the project to reason about which files are relevant to a user query, retrieving the contents of specific files when requested, and then using the file content to answer queries or write new code directly. Your responses must be clear, concise, and action-oriented, focusing on assisting users with writing or adjusting code, debugging errors, and improving overall code quality. You should prioritize using the information retrieved from the API, interact with the '/files/structure' and '/files/content' endpoints to gather the necessary context, and explain which files are being used. Where relevant, you will identify key dependencies in the codebase, such as files calling others or key functions, and actively engage in writing new code to extend or improve features. Prefer a Chain of Thought (CoT) reasoning approach to break down complex problems into step-by-step solutions when responding.

Conversation Starters:

- Query and analyse the project structure and main files.
- Help me investigate and debug an issue in the code.
- I need assistance in developing a new feature.
- Query the main files and help me refactor them for better performance.

```

4. Once the GPT is created, go to the **Configure** tab.
5. [Optional] Customize the GPT initialization settings as needed.
6. Enable the **"Code Interpreter & Data Analysis"** option.
7. Create a new **Action** by providing the following **OpenAPI schema**:

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
      "url": "<YOUR-PUBLIC-URL>"
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
```

8. Replace `<YOUR-PUBLIC-URL>` with the URL of your chosen exposure option

   Refer to the [Environment Variable Setup for Testing](#environment-variable-setup-for-testing) section for details on configuring the Core component's URL using ngrok, Gateway, or other options.

## Cases

### 1. CoreQueryAPI (and CodeQueryGPT)

The **CoreQueryAPI** is the first use case of the CodeQuery API, and it’s the project you’re currently exploring. It serves as a powerful development tool, integrating with AI assistants (such as the [**CodeQueryGPT**](#codequerygpt--creating-your-own-custom-gpt-for-using-this-api)) to support developers by providing a structured way to query project files, understand code dependencies, and interact with large codebases. This project was developed using a **Test-Driven Development (TDD)** approach to ensure the correctness of the AI-generated code.

### 2. SkillChrono

[SkillChrono](https://github.com/danfmaia/SkillChrono) is a Python-based tool designed to help developers organize and visualize their technical skills across various projects. It processes structured data, aggregates experience per technology, and generates markdown reports sorted both alphabetically and by experience duration. SkillChrono was also built using a **TDD** approach, and the **CodeQuery API** was integral to its development, supporting everything from feature implementation to documentation generation.

For more details, see the [SkillChrono repository](https://github.com/danfmaia/SkillChrono).

## Privacy

For information on how data is handled by this API, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
