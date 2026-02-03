#!/bin/bash
# Development environment setup script for Unix/macOS/Linux

set -e

echo "======================================"
echo "RESTO360 Development Environment Setup"
echo "======================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose is not installed."
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists, create from example if not
if [ ! -f "apps/api/.env" ]; then
    echo "Creating apps/api/.env from .env.example..."
    cp .env.example apps/api/.env
    echo "IMPORTANT: Edit apps/api/.env with your local settings if needed."
    echo ""
fi

# Build and start containers
echo "Building and starting Docker containers..."
cd docker
docker-compose up -d --build

echo ""
echo "Waiting for database to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker-compose exec api python manage.py migrate

# Create superuser prompt
echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Services running:"
echo "  - API:      http://localhost:8000"
echo "  - Database: localhost:5432 (resto360/resto360)"
echo "  - Redis:    localhost:6379"
echo ""
echo "Useful commands:"
echo "  make dev-up      - Start all services"
echo "  make dev-down    - Stop all services"
echo "  make dev-logs    - View logs"
echo "  make test        - Run tests"
echo "  make lint        - Run linter"
echo "  make shell       - Django shell"
echo ""
echo "To create a superuser:"
echo "  docker-compose exec api python manage.py createsuperuser"
echo ""
