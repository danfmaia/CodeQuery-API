# Colors for better visibility
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

# Include environment variables from .env
include .env
export

.PHONY: help init build run stop logs test integration-test

help: ## Show this help message
	@echo "CodeQuery Core - Quick Start Guide"
	@echo "Usage:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-10s %s\n", $$1, $$2}'

init: ## Setup environment (copy template.env to .env)
	@if [ ! -f .env ]; then \
		cp template.env .env; \
		echo "$(GREEN)Created .env file. Please edit it with your settings.$(NC)"; \
	else \
		echo "$(GREEN).env file already exists.$(NC)"; \
	fi

build: ## Build the Docker image
	@echo "Building Docker image..."
	@if [ -z "$(NGROK_AUTHTOKEN)" ]; then \
		echo "$(RED)Error: NGROK_AUTHTOKEN is not set in .env file$(NC)"; \
		exit 1; \
	fi
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
	docker run --rm -p 5001:5001 -p 4040:4040 --env-file .env codequery_core python core/tests/integration_test.py
