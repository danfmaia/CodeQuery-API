# Commands

<!-- TODO: Rewrite history to purge sensitive data in this file. -->

lsof -i :5001 && ps aux | grep ngrok

## Testing

### Pytest

clear && pytest tests/ | tee tests/results.txt

### Endpoints

source .env

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

curl -X GET "https://codequery.dev/ngrok-urls/other-valid-key" \
 -H "x-api-key: $API_KEY"

#### POST /ngrok-urls/

curl -X POST "https://codequery.dev/ngrok-urls/" \
 -H "Content-Type: application/json" \
 -H "x-api-key: $API_KEY" \
 -d '{"api_key": "test-key", "ngrok_url": "https://new-ngrok-url.ngrok.io"}'
