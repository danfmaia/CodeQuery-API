# Commands

<!-- TODO: Rewrite history to purge sensitive data in this file. -->

lsof -i :5001 && ps aux | grep ngrok

## Testing

### Pytest

clear && pytest tests/ | tee tests/results.txt

### Curl

source .env

curl -H "X-API-KEY: $API_KEY" https://codequery.dev/files/structure

curl -H "X-API-KEY: $API_KEY" http://$EC2_HOST:8080/files/structure

curl -X POST "https://codequery.dev/ngrok-urls/" \
 -H "Content-Type: application/json" \
 -H "x-api-key: $API_KEY" \
 -d '{"api_key": "test-key", "ngrok_url": "https://new-ngrok-url.ngrok.io"}'

curl -X GET "https://codequery.dev/ngrok-urls/$API_KEY" \
 -H "x-api-key: $API_KEY"
