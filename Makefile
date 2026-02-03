# RESTO360 Development Makefile
# Run 'make help' to see available commands

.PHONY: help dev-up dev-down dev-logs dev-restart test lint format shell migrate makemigrations createsuperuser clean

# Default target
help:
	@echo "RESTO360 Development Commands"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  make dev-up        Start all services (Docker Compose)"
	@echo "  make dev-down      Stop all services"
	@echo "  make dev-restart   Restart all services"
	@echo "  make dev-logs      View service logs (follow mode)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          Run all tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Format code with ruff"
	@echo ""
	@echo "Django:"
	@echo "  make shell         Open Django shell"
	@echo "  make migrate       Run database migrations"
	@echo "  make makemigrations  Create new migrations"
	@echo "  make createsuperuser  Create Django superuser"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove containers, volumes, and cache"
	@echo ""

# Development environment
dev-up:
	cd docker && docker-compose up -d --build
	@echo ""
	@echo "Services started:"
	@echo "  API:      http://localhost:8000"
	@echo "  Database: localhost:5432"
	@echo "  Redis:    localhost:6379"

dev-down:
	cd docker && docker-compose down

dev-restart:
	cd docker && docker-compose restart

dev-logs:
	cd docker && docker-compose logs -f

# Testing
test:
	cd docker && docker-compose exec api pytest -v

test-cov:
	cd docker && docker-compose exec api pytest --cov=apps --cov-report=html --cov-report=term-missing

test-local:
	cd apps/api && pytest -v

# Linting and formatting
lint:
	ruff check apps/api/

lint-docker:
	cd docker && docker-compose exec api ruff check .

format:
	ruff format apps/api/

format-check:
	ruff format --check apps/api/

# Django commands
shell:
	cd docker && docker-compose exec api python manage.py shell

migrate:
	cd docker && docker-compose exec api python manage.py migrate

makemigrations:
	cd docker && docker-compose exec api python manage.py makemigrations

createsuperuser:
	cd docker && docker-compose exec api python manage.py createsuperuser

# Cleanup
clean:
	cd docker && docker-compose down -v --remove-orphans
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
