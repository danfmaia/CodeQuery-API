## Testing the CodeQuery API

This section outlines the environment variable setup and key testing commands for the Core component, including running unit tests and troubleshooting integration issues.

### Environment Variable Setup

Before running any tests, make sure to configure the necessary environment variables in the `.env` file. Here’s the complete `.env` file template:

```plaintext
# Project

PROJECT_PATH="./project-path" # Set this to the root path of your project
AGENTIGNORE_FILES=".agentignore,.gitignore" # Specify file patterns to ignore

# API and Gateway

LOCAL_PORT=5001 # Set your local port for the Core component
API_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" # Your personal API key
GATEWAY_BASE_URL="https://your-gateway-url.com" # Set to your Gateway's public URL

# Other

NGROK_API_URL="http://localhost:4040/api/tunnels" # Ngrok API URL for querying tunnel status
TIMEOUT=10 # Request timeout in seconds
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
   python tests/integration_test.py
   ```

   This will execute the integration test and provide a summary of the results, validating the communication between the Gateway and Core components.

### 3. Troubleshooting Common Issues

- **Ngrok URL Mismatch**: If you encounter issues with ngrok URL synchronization between the Core and Gateway, ensure that:

  - The `GATEWAY_UPLOAD_URL` is correctly set in your `.env` file.
  - The Gateway component is reachable and the API key is valid.

- **Missing Environment Variables**: Ensure all necessary environment variables (`PROJECT_PATH`, `API_KEY`, etc.) are defined in your `.env` file.

For more detailed troubleshooting steps, refer to `gateway/README.md` if you're encountering Gateway-specific issues.
