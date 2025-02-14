# CodeQuery API

> Note: For the gateway component of this project, [check this directory](https://github.com/danfmaia/CodeQuery-API/tree/main/gateway).

![CodeQueryGPT cover artwork](./assets/social/social_CodeQueryAPI.png)

**Usage demo 1:**

<p>
  <img src="./assets/demo/GPT_usage_1.gif" alt="CodeQueryGPT usage GIF 1"/>
</p>

**Usage demo 2:**

<p>
  <img src="./assets/demo/GPT_usage_2.gif" alt="CodeQueryGPT usage GIF 2"/>
</p>

## Introduction

**CodeQuery™ API** is a lightweight Python/Flask tool designed to enable AI assistants—such as custom GPTs—to navigate and interact with local code effectively. With this API, [LLM agents](https://python.langchain.com/v0.1/docs/modules/agents/) can query project structures and retrieve file contents, helping developers explore and manage large codebases. By adhering to customizable ignore patterns, the API ensures that only relevant files are accessed, making it an invaluable tool for AI-driven code analysis and development.

🤖 **Curious Fact**: During its development, the **CodeQuery API** was an integral part of its own creation process, being used to analyze, write, and debug its own files while the project evolved. This unique feedback loop made it a participant in its own development stages! For more details on how the CodeQuery API has been applied, see the [Cases](#cases) section.

## Features

- **Designed for AI Assistants**: This API was specifically designed to integrate with AI assistants such as custom GPTs, providing them with efficient access to project file structures and contents.
- **Retrieve Project Structure**: Get a detailed view of the project's directories and files.
- **Retrieve File Contents**: Access the contents of specific files in the project, with error handling for non-existent paths.
- **Custom Ignore Patterns**: Utilize `.agentignore` and/or `.gitignore` for specifying which files or directories to exclude from the structure retrieval.

## Installation and Usage

The CodeQuery API consists of two components:

- A **Core** component that runs locally and accesses your files
- A **Gateway** service that manages authentication and routes requests

### Prerequisites

- **Docker**: Required for running the Core component in a container
- **Make**: Used for simplified command execution
- **curl**: Needed for API key generation and testing
- **ngrok account**: Required for secure tunneling (free tier is sufficient)
  - Sign up at https://dashboard.ngrok.com/signup
  - Get your authtoken at https://dashboard.ngrok.com/get-started/your-authtoken

### Quick Start

1. **Get Required Credentials**:

   ```bash
   # Generate a new API key from the Gateway service
   curl -X POST https://codequery.dev/api-keys/generate

   # Get your ngrok authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
   # You'll need this in step 2c
   ```

2. **Set Up the Core Component**:

   a. Clone the repository:

   ```bash
   git clone https://github.com/danfmaia/CodeQuery-API.git
   cd CodeQuery-API
   ```

   b. Initialize the environment:

   ```bash
   make init  # Creates a fresh .env file from template
   # Use 'make clean' if you need to start fresh later
   ```

   c. Configure your `.env` file:

   - Set your project path
   - Add your API key from step 1
   - Add your ngrok authtoken from step 1

3. **Start the Core**:

   ```bash
   make build  # Build the Docker image
   make run    # Run the Core container
   ```

   The Core will automatically:

   - Start a secure ngrok tunnel
   - Register its URL with the Gateway
   - Begin accepting requests through the Gateway

4. **Use the API**:

   ```bash
   # Get the project structure
   curl -H "X-API-KEY: API_KEY" https://codequery.dev/files/structure

   # Get specific file contents
   curl -X POST \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: API_KEY" \
     -d '{"file_paths": ["README.md"]}' \
     https://codequery.dev/files/content
   ```

5. **Other Useful Commands**:
   ```bash
   make help   # Show all available commands
   make stop   # Stop the container
   make test   # Run tests
   make logs   # View container logs
   ```

### Environment Variables

The `.env` file created by `make init` contains all necessary configuration. The main variables you'll need to set are:

```plaintext
# Required settings
PROJECT_PATH=      # Path to the project you want to analyze
API_KEY=          # Your API key from step 1
NGROK_AUTHTOKEN=  # Your ngrok authtoken
```

Other settings like ports and timeouts have sensible defaults and usually don't need modification.

For more detailed information about the API endpoints and advanced usage, see the [Documentation](docs/README.md).

### Other Exposure Options

#### 1. **Using a Paid Ngrok URL**

- **Description**: If you have a paid ngrok plan, set up a permanent public URL by running the Core component locally and using the ngrok URL for external access.

- **Command**:

  ```bash
  python run_local.py
  ```

- **Use Case**: Suitable for users who require a consistent external URL and prefer a simple setup.

#### 2. **Setting Up a Self-Hosted Server**

- **Description**: For users with a static IP or home server, you can host the Core directly using your ISP's services, avoiding ngrok or Gateway usage.

- **Command**:

  ```bash
  python run_local.py
  ```

- **Steps**:

  1. **Check Static IP Availability**: Ensure your ISP offers a static IP.
  2. **Port Forwarding**: Configure your router to forward traffic on port 5001 to the local machine.
  3. **Domain Setup**: Consider using a custom domain for access.
  4. **SSL/TLS Configuration**: Use services like Let's Encrypt to secure the server.

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

  - **500 Internal Server Error**: If there's a failure in reading the directory structure, such as permission issues or corrupted files, an internal error response will be returned.

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

  - **500 Internal Server Error**: If there's a failure in reading a file due to permissions, encoding issues, or other OS-level errors.

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

## CodeQueryGPT – Creating your own custom GPT for using this API

This API was designed to be used by custom AI assistants. If you are a ChatGPT Premium user, you can create a custom GPT using the **ChatGPT Builder**.

### Steps:

1. Go to the [GPT Builder](https://chatgpt.com/gpts/editor/g-vKMjAxftT) in your ChatGPT Premium account.
2. Access the **Create** tab.
3. Send the following prompt to the GPT Builder to create your custom GPT:

```

Name: CodeQueryGPT

Description: Helps developers analyze code, debug issues, and develop features, by leveraging an API to retrieve project structure and files.

Instructions:
"""
You are CodeQueryGPT, an AI specialized in assisting with software development tasks by actively querying project files, analyzing code structure, and providing coding support. You use an external API to fetch file structures and retrieve file contents as needed.

Your goal is to assist with code analysis, feature development, debugging, and understanding code dependencies, contributing directly to the development process. You should determine when to query the project structure or relevant files, integrating this step into your workflow naturally.

Use a Chain of Thought (CoT) approach to break down complex tasks into clear steps. When debugging or implementing features, proactively query test results, logs, and relevant files to understand the problem or requirements. Focus on suggesting clear, actionable code changes or improvements while ensuring that you have all the necessary context to perform the task effectively.
"""

Conversation Starters:

- Analyse the code following a thorough CoT process. Use both endpoints.
- Help me investigate and debug an issue in the code.
- I need assistance in developing a new feature.
- Query the main files. Then pick some method(s) refactor them for better performance.

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
    "description": "A Flask API to retrieve the file structure and contents of a project directory.",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://codequery.dev"
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

### Screenshots

#### "Configure" screen

<p>
  <img width=600 src="https://drive.google.com/uc?export=view&id=13qcof-EX1bFbjvklaNXyRimUJwTz98hU" alt="CodeQueryGPT Configure 1"/>
</p>
<p>
  <img width=600 src="https://drive.google.com/uc?export=view&id=1ZsdCZbGpPThQ4sRTMFJlKAgxz12zXme4" alt="CodeQueryGPT Configure 2"/>
</p>
<p>
  <img width=600 src="https://drive.google.com/uc?export=view&id=1v_1JnFscTwOYD7ZKJPnpfOXq3blONlCr" alt="CodeQueryGPT Configure 3"/>
</p>

#### "Edit actions" screen

<p>
  <img width=600 src="https://drive.google.com/uc?export=view&id=1ues8rh0GXGS78pQevACNKMNaTro6EVnT" alt="CodeQueryGPT Edit actions 1"/>
</p>
<p>
  <img width=600 src="https://drive.google.com/uc?export=view&id=1sKmo0_GkNq4e8ITvNcgQtTs3gsHPqE-n" alt="CodeQueryGPT Edit actions 2"/>
</p>

## Cases

### 1. CoreQuery API (and CodeQueryGPT)

The **CoreQuery API** itself is the first use case of the CodeQuery API, and it's the project you're currently exploring. It serves as a powerful development tool, integrating with AI assistants (such as the [**CodeQueryGPT**](#codequerygpt--creating-your-own-custom-gpt-for-using-this-api)) to support developers by providing a structured way to query project files, understand code dependencies, and interact with large codebases. This project was developed using a **Test-Driven Development (TDD)** approach to ensure the correctness of the AI-generated code.

### 2. SkillChrono

[SkillChrono](https://github.com/danfmaia/SkillChrono) is a Python-based tool designed to help developers organize and visualize their technical skills across various projects. It processes structured data, aggregates experience per technology, and generates markdown reports sorted both alphabetically and by experience duration. SkillChrono was also built using a **TDD** approach, and the **CodeQuery API** was integral to its development, supporting everything from feature implementation to documentation generation.

For more details, see the [SkillChrono repository](https://github.com/danfmaia/SkillChrono).

## Privacy

For information on how data is handled by this API, please refer to the [Privacy Policy](privacy.md). The policy explains what data is processed, how it's used, and the lack of data retention within the API.

## License

This project is licensed under the Apache License, Version 2.0.  
You may obtain a copy of the License at:

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)
