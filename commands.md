# Commands

<!-- TODO: Rewrite history to purge sensitive data in this file. -->

lsof -i :5001 && ps aux | grep ngrok

curl --silent http://127.0.0.1:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9-]+\.ngrok-free\.app'

## Testing

### Pytest

clear && pytest tests/ | tee tests/results.txt

### Core-side Endpoints

source .env

#### Health check

export NGROK_TEST_URL=$(curl --silent http://127.0.0.1:4040/api/tunnels | grep -Eo 'https://[a-zA-Z0-9-]+\.ngrok-free\.app')

curl -X GET $NGROK_TEST_URL/health

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

#### GET /ngrok-urls/$API_KEY

curl -X GET "https://codequery.dev/ngrok-urls/$API_KEY" \
 -H "x-api-key: $API_KEY"

curl -X GET "https://codequery.dev/ngrok-urls/test-key" \
 -H "x-api-key: $API_KEY"

#### POST /ngrok-urls/

curl -X POST "https://codequery.dev/ngrok-urls/" \
 -H "Content-Type: application/json" \
 -H "x-api-key: $API_KEY" \
 -d '{"api_key": $API_KEY, "ngrok_url": "https://6e95-2804-1b3-7000-829a-c598-42f-2d99-3b97.ngrok-free.app"}'

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
