run:
	# Kill any process occupying port 5001
	@if lsof -i :5001; then \
		kill -9 $$(lsof -t -i :5001); \
		echo "Released port 5001"; \
	fi
	# Run the container
	docker run --rm -it -p 5001:5001 -p 4040:4040 --name codequery_core -v "$(shell pwd):/app" --env-file .env codequery_core

logs:
	docker logs -f codequery_core

build:
	docker build -t codequery_core --build-arg NGROK_AUTHTOKEN=$(NGROK_AUTHTOKEN) .
