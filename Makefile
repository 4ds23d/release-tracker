.PHONY: test test-unit test-integration test-coverage install install-dev clean lint format help

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up generated files"

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e .

# Testing targets
test:
	pytest

test-unit:
	pytest tests/ -m "not integration and not slow"

test-integration:
	pytest tests/ -m integration

test-slow:
	pytest tests/ -m slow

test-coverage:
	pytest --cov=git_release_notifier --cov-report=html --cov-report=term-missing

# Code quality targets
lint:
	@echo "Linting with flake8..."
	@which flake8 > /dev/null || (echo "flake8 not installed. Install with: pip install flake8" && exit 1)
	flake8 git_release_notifier/ tests/ --max-line-length=100 --ignore=E501,W503

format:
	@echo "Formatting with black..."
	@which black > /dev/null || (echo "black not installed. Install with: pip install black" && exit 1)
	black git_release_notifier/ tests/ --line-length=100

# Cleanup targets
clean:
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf repos/
	rm -rf *.html
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development targets
run-example:
	python main.py --config config.yaml --output example_report.html --verbose

run-report:
	python examples/generate_demo_report.py 

setup-dev: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything works."