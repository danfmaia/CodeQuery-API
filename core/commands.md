# Commands

## Quick Start

```bash
# Initialize environment
make init

# Build and run
make build
make run

# View logs
make logs

# Stop the container
make stop

# Run tests
make test

# Show all available commands
make help
```

## Manual Commands (Alternative)

### Running Manually

```bash
# Build the image
docker build -t codequery_core --build-arg NGROK_AUTHTOKEN=$NGROK_AUTHTOKEN .

# Run the container
docker run --rm -d -p 5001:5001 -p 4040:4040 --name codequery_core -v "$(pwd):/app" --env-file .env codequery_core

# View logs
docker logs -f codequery_core

# Stop the container
docker stop codequery_core
```

### Testing

```bash
# Run tests
docker run --rm codequery_core pytest core/tests
```

### API Testing

#### Health check (Localhost)

```bash
curl -X GET http://127.0.0.1:$LOCAL_PORT/
```

#### GET /files/structure (Localhost)

```bash
curl -H "X-API-KEY: $API_KEY" http://127.0.0.1:$LOCAL_PORT/files/structure
```

#### POST /files/content (Localhost)

```bash
curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
  "file_paths": [
    "core/src/app.py",
    "core/src/ngrok_manager.py"
  ]
}' http://127.0.0.1:$LOCAL_PORT/files/content
```

### Ngrok URLs

```bash
# Get current ngrok URL
curl --silent http://127.0.0.1:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9-]+\.ngrok-free\.app'
```

## Testing

clear && docker run --rm codequery_core COMMAND

### Unit testing with Pytest

clear && docker run --rm codequery_core pytest core/tests

### Integration testing

clear && docker run --rm codequery_core python core/tests/integration_test.py

### Core-side Endpoints (Localhost)

> Simpler approach, no ngrok or gateway dependency.

#### Health check (Localhost)

curl -X GET http://127.0.0.1:$LOCAL_PORT/

#### GET /files/structure (Localhost)

curl -H "X-API-KEY: $API_KEY" http://127.0.0.1:$LOCAL_PORT/files/structure

#### POST /files/content (Localhost)

curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
"file_paths": [
"core/src/app.py",
"core/src/ngrok_manager.py"
]
}' http://127.0.0.1:$LOCAL_PORT/files/content

### Core-side Endpoints (via nGrok)

export NGROK_TEST_URL=$(curl --silent http://127.0.0.1:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9-]+\.ngrok-free\.app')

#### Health check

curl -X GET $NGROK_TEST_URL/

#### GET /files/structure

curl -H "X-API-KEY: $API_KEY" $NGROK_TEST_URL/files/structure

#### POST /files/content

curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
"file_paths": [
"gateway/gateway.py",
"gateway/src/s3_manager.py"
]
}' $NGROK_TEST_URL/files/content

### Gateway-side Endpoints

#### GET /files/structure

curl -H "X-API-KEY: $API_KEY" https://codequery.dev/files/structure

curl -H "X-API-KEY: $API_KEY" http://$EC2_HOST:8080/files/structure

#### POST /files/content

curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
"file_paths": [
"gateway/gateway.py",
"gateway/src/s3_manager.py"
]
}' https://codequery.dev/files/content

curl -X POST -H "Content-Type: application/json" -H "X-API-KEY: $API_KEY" -d '{
"file_paths": [
".env"
]
}' https://codequery.dev/files/content

NGROK_TEST_URL/files/content

#### GET /ngrok-urls/$API_KEY

curl -X GET "https://codequery.dev/ngrok-urls/$API_KEY" \
 -H "x-api-key: $API_KEY"

curl -X GET "https://codequery.dev/ngrok-urls/test-key" \
 -H "x-api-key: $API_KEY"

#### POST /ngrok-urls/

curl -X POST "https://codequery.dev/ngrok-urls/" \
 -H "Content-Type: application/json" \
 -H "x-api-key: $API_KEY" \
 -d '{"api_key": $API_KEY, "ngrok_url": "https://XXXX.ngrok-free.app"}'

curl -X POST "https://codequery.dev/ngrok-urls/" \
 -H "Content-Type: application/json" \
 -H "x-api-key: $API_KEY" \
 -d '{"api_key": "test-key", "ngrok_url": "https://new-ngrok-url.ngrok.io"}'

## Service Management

**Restart service:**

sudo systemctl daemon-reload && sudo systemctl restart codequery_core && sudo systemctl status codequery_core

**Clear journalctl logs && Restart service:**

sudo journalctl --rotate && sudo journalctl --vacuum-time=1s && clear && \
sudo systemctl daemon-reload && sudo systemctl restart codequery_core && sudo systemctl status codequery_core

**Check service status:**

sudo systemctl status codequery_core

sudo journalctl -u codequery_core -n 50

**Clear journalctl logs**

sudo journalctl --rotate && sudo journalctl --vacuum-time=1s && clear
