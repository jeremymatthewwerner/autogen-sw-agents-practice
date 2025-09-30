.PHONY: help test test-unit test-integration test-e2e coverage clean install run deploy

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-e2e         - Run end-to-end tests"
	@echo "  make coverage         - Run tests with coverage report"
	@echo "  make clean            - Clean up cache and temporary files"
	@echo "  make run              - Run the application locally"
	@echo "  make deploy           - Deploy to AWS"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio pytest-mock httpx playwright
	playwright install chromium

test: test-unit test-integration

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v --tb=short

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v --tb=short -m integration

test-e2e:
	@echo "Starting application for E2E tests..."
	python app.py &
	@echo "Waiting for app to start..."
	sleep 5
	@echo "Running E2E tests..."
	pytest tests/e2e/ -v --tb=short -m e2e || (pkill -f "python app.py"; exit 1)
	@echo "Stopping application..."
	pkill -f "python app.py"

coverage:
	@echo "Running tests with coverage..."
	pytest tests/unit/ tests/integration/ \
		--cov=agents \
		--cov=utils \
		--cov=multi_agent_system \
		--cov-report=html:htmlcov \
		--cov-report=term \
		--cov-report=xml

clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".coverage" -delete

run:
	@echo "Starting application..."
	python app.py

deploy:
	@echo "Deploying to AWS..."
	./deploy_automated.sh

# Development helpers
lint:
	@echo "Running linters..."
	black .
	isort .
	flake8 . --max-line-length=88 --extend-ignore=E203,W503

format:
	@echo "Formatting code..."
	black .
	isort .

check:
	@echo "Running pre-commit checks..."
	pre-commit run --all-files

watch-tests:
	@echo "Watching for file changes and running tests..."
	while true; do \
		inotifywait -r -e modify,create,delete --exclude '\.git|__pycache__|\.pytest_cache' .; \
		clear; \
		make test-unit; \
	done