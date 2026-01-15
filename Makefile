.PHONY: help install test lint format typecheck clean docker-build docker-run docker-stop

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"
	@echo "  make typecheck    - Run type checker"
	@echo "  make clean        - Clean generated files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make dev          - Run development server"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/

typecheck:
	mypy app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name .coverage -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-build:
	docker build -t weather-api:latest .

docker-run:
	docker run -d --name weather-api -p 8000:8000 weather-api:latest
	@echo "Service running at http://localhost:8000"
	@echo "API docs at http://localhost:8000/docs"
	@echo "Web UI at http://localhost:8000/web/"

docker-stop:
	docker stop weather-api || true
	docker rm weather-api || true

docker-logs:
	docker logs -f weather-api

dev:
	python -m app.main

all: format lint typecheck test
