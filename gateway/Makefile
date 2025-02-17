# Colors for better visibility
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
NC := \033[0m # No Color

.PHONY: help test-coverage

help: ## Show this help message
	@echo "CodeQuery Gateway - Available Commands"
	@echo ""
	@echo "Usage:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  make %-20s%s\n", $$1, $$2}' $(MAKEFILE_LIST)

test-coverage: ## Run tests with coverage report
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	python -m pytest tests/ --cov=src --cov=. -v
	@echo "$(GREEN)Coverage report generated.$(NC)" 