.PHONY: help install dev test lint format clean build run docker-build docker-run docker-stop

help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean cache files"
	@echo "  build       - Build Docker image"
	@echo "  run         - Run with Docker Compose"
	@echo "  stop        - Stop Docker Compose"

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest test_api.py -v

lint:
	flake8 *.py
	black --check *.py

format:
	black *.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

build:
	docker build -t ragnaforge .

run:
	docker-compose up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f

test-api:
	python scripts/test_client.py
