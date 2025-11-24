# Indicator Computation Service Makefile

.PHONY: help install test run-rest run-grpc run-all docker-build docker-run docker-dev clean generate-grpc demo lint format

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

generate-grpc: ## Generate gRPC Python files
	python generate_grpc.py

test: ## Run all tests
	pytest -v

test-unit: ## Run unit tests only
	pytest test_indicators.py test_service.py -v

test-integration: ## Run integration tests only
	pytest test_integration.py -v

test-coverage: ## Run tests with coverage
	pytest --cov=indicators --cov=service --cov-report=html --cov-report=term

run-rest: ## Run REST API server
	python main.py

run-grpc: ## Run gRPC server
	python grpc_server.py

run-all: ## Run both REST and gRPC servers
	python main.py & python grpc_server.py

docker-build: ## Build Docker image
	docker build -t indicator-service .

docker-run: ## Run with Docker Compose
	docker-compose up --build

docker-dev: ## Run development version with Docker Compose
	docker-compose --profile dev up

docker-stop: ## Stop Docker containers
	docker-compose down

demo: ## Run demo script
	python demo.py

lint: ## Run linting
	flake8 indicators/ main.py grpc_server.py service.py test*.py demo.py
	mypy indicators/ main.py grpc_server.py service.py

format: ## Format code
	black indicators/ main.py grpc_server.py service.py test*.py demo.py
	isort indicators/ main.py grpc_server.py service.py test*.py demo.py

clean: ## Clean up generated files
	rm -rf indicators_pb2.py indicators_pb2_grpc.py
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

dev-setup: install generate-grpc ## Set up development environment
	echo "Development environment ready!"
	echo "Run 'make run-all' to start both servers"
	echo "Run 'make demo' to test the service"

check: lint test-coverage ## Run all checks (lint + test with coverage)
	echo "All checks completed!"