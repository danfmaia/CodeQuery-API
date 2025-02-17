# Colors for better visibility
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.PHONY: help init build run stop logs test integration-test clean integration-test-gateway test-coverage

help: ## Show this help message
	@echo "CodeQuery Core - Quick Start Guide"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Docker"
	@echo "  - Make"
	@echo "  - curl"
	@echo "  - ngrok account (free tier is sufficient)"
	@echo "    Get your authtoken at https://dashboard.ngrok.com/get-started/your-authtoken"
	@echo ""
	@echo "Usage:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  make %-20s%s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Setup environment and configure API key
	@if [ -f .env ]; then \
		echo "$(YELLOW)Warning: .env file already exists.$(NC)"; \
		read -p "Do you want to overwrite it? [y/N] " answer; \
		if [ "$$answer" != "y" ] && [ "$$answer" != "Y" ]; then \
			echo "Keeping existing .env file."; \
			exit 0; \
		fi; \
	fi; \
	cp template.env .env; \
	echo "$(GREEN)Created .env file from template.$(NC)"; \
	echo "$(GREEN)Next steps:$(NC)"; \
	echo "1. Get your API key by running:"; \
	echo "   curl -X POST https://codequery.dev/api-keys/generate"; \
	echo "2. Add your API key to .env as API_KEY=your_key"; \
	echo "3. Set PROJECT_PATH in .env to the root of the project you want CodeQuery to help you with"; \
	echo "   Example: PROJECT_PATH=/path/to/your/project"; \
	echo "4. Add your ngrok authtoken to .env as NGROK_AUTHTOKEN=your_token"; \
	echo "5. Run 'make build'"

clean: ## Remove .env file and start fresh
	@if [ -f .env ]; then \
		echo "$(YELLOW)Warning: This will remove your .env file.$(NC)"; \
		read -p "Are you sure? [y/N] " answer; \
		if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
			rm .env; \
			echo "$(GREEN).env file removed. Run 'make init' to start fresh.$(NC)"; \
		else \
			echo "Operation cancelled."; \
		fi; \
	else \
		echo "No .env file found."; \
	fi

# Load environment variables after init
ifneq ($(wildcard .env),)
    include .env
    export
endif

build: ## Build the Docker image
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found. Run 'make init' first.$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(NGROK_AUTHTOKEN)" ]; then \
		echo "$(RED)Error: NGROK_AUTHTOKEN is not set in .env file$(NC)"; \
		echo "Please edit .env and add your ngrok authtoken before building."; \
		exit 1; \
	fi
	@if [ -z "$(API_KEY)" ]; then \
		echo "$(RED)Error: API_KEY is not set in .env file$(NC)"; \
		echo "Please edit .env and add your API key before building."; \
		echo "You can generate one with: curl -X POST https://codequery.dev/api-keys/generate"; \
		exit 1; \
	fi
	@echo "Building Docker image..."
	docker build -t codequery_core --build-arg NGROK_AUTHTOKEN=$(NGROK_AUTHTOKEN) .
	@echo "$(GREEN)Build completed.$(NC)"

run: ## Run the Core container
	@echo "Starting Core container..."
	@if lsof -i :5001 >/dev/null 2>&1; then \
		kill -9 $$(lsof -t -i :5001); \
		echo "Released port 5001"; \
	fi
	docker run --rm -d -p 5001:5001 -p 4040:4040 --name codequery_core -v "$(shell pwd):/app" --env-file .env codequery_core
	@echo "$(GREEN)Container started. Use 'make logs' to view logs.$(NC)"

stop: ## Stop the Core container
	@echo "Stopping Core container..."
	@docker stop codequery_core 2>/dev/null || true
	@docker rm codequery_core 2>/dev/null || true
	@echo "$(GREEN)Container stopped and removed.$(NC)"

logs: ## View container logs
	docker logs -f codequery_core

test: ## Run tests (excluding integration)
	docker run --rm --env-file .env codequery_core pytest core/tests -k "not integration"

integration-test: ## Run integration tests
	@echo "Running integration tests..."
	@if lsof -i :5001 >/dev/null 2>&1; then \
		kill -9 $$(lsof -t -i :5001); \
		echo "Released port 5001"; \
	fi
	@if lsof -i :4040 >/dev/null 2>&1; then \
		kill -9 $$(lsof -t -i :4040); \
		echo "Released port 4040"; \
	fi
	@echo "Starting Core service..."
	docker run --rm -d -p 5001:5001 -p 4040:4040 --name codequery_core -v "$(shell pwd):/app" --env-file .env codequery_core
	@echo "Waiting for Core service to start..."
	@sleep 5
	@echo "Running integration test..."
	docker exec codequery_core python core/tests/integration_test.py
	@echo "Stopping Core service..."
	docker stop codequery_core

integration-test-gateway: ## Run integration tests including Gateway interaction
	@echo "Running Gateway integration tests..."
	@# Ensure cleanup of any existing containers
	@docker stop codequery_core 2>/dev/null || true
	@docker rm codequery_core 2>/dev/null || true
	@# Kill any processes using our ports
	@echo "Cleaning up ports..."
	@for port in 5001 4040; do \
		pid=$$(sudo ss -lptn "sport = :$$port" | grep LISTEN | sed -E 's/.*pid=([0-9]+).*/\1/'); \
		if [ ! -z "$$pid" ]; then \
			echo "Killing process $$pid using port $$port"; \
			sudo kill -9 $$pid 2>/dev/null || true; \
		fi \
	done
	@# Start Core service with proper error handling
	@echo "Starting Core service..."
	@docker run --rm -d -p 5001:5001 -p 4040:4040 --name codequery_core -v "$(shell pwd):/app" --env-file .env codequery_core || \
		(echo "Failed to start Core service" && exit 1)
	@echo "Waiting for Core service to start..."
	@sleep 5
	@echo "Running Gateway integration test..."
	@docker exec codequery_core python core/tests/integration_test_with_gateway.py || \
		(docker stop codequery_core && echo "Integration test failed" && exit 1)
	@echo "Stopping Core service..."
	@docker stop codequery_core || true

test-coverage: ## Run tests locally (outside Docker) with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	python -m pytest core/tests/ --cov=core/src --cov-report=term-missing:skip-covered -v
	@echo "$(GREEN)Coverage report generated. Only showing files with missing coverage.$(NC)"
