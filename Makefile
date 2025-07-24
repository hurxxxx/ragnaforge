.PHONY: help install dev test lint format clean build run docker-build docker-run docker-stop

help:
	@echo "Available commands:"
	@echo "  install       - Install dependencies"
	@echo "  dev           - Run development server"
	@echo "  test          - Run comprehensive search tests"
	@echo "  test-pipeline - Run complete pipeline test"
	@echo "  lint          - Run linting"
	@echo "  format        - Format code"
	@echo "  clean         - Clean cache files"
	@echo "  build         - Build Docker image"
	@echo "  run           - Run with Docker Compose"
	@echo "  stop          - Stop Docker Compose"

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	./test_comprehensive_search_test.sh

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

test-pipeline:
	./test_complete_pipeline.sh
