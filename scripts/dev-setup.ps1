# Development environment setup script for Windows PowerShell

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "RESTO360 Development Environment Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check for Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "ERROR: Docker is not installed." -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
}

# Check if .env exists, create from example if not
if (-not (Test-Path "apps/api/.env")) {
    Write-Host "Creating apps/api/.env from .env.example..."
    Copy-Item ".env.example" "apps/api/.env"
    Write-Host "IMPORTANT: Edit apps/api/.env with your local settings if needed." -ForegroundColor Yellow
    Write-Host ""
}

# Build and start containers
Write-Host "Building and starting Docker containers..." -ForegroundColor Yellow
Set-Location docker
docker-compose up -d --build

Write-Host ""
Write-Host "Waiting for database to be ready..."
Start-Sleep -Seconds 5

# Run migrations
Write-Host "Running database migrations..."
docker-compose exec api python manage.py migrate

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:"
Write-Host "  - API:      http://localhost:8000"
Write-Host "  - Database: localhost:5432 (resto360/resto360)"
Write-Host "  - Redis:    localhost:6379"
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  make dev-up      - Start all services"
Write-Host "  make dev-down    - Stop all services"
Write-Host "  make dev-logs    - View logs"
Write-Host "  make test        - Run tests"
Write-Host "  make lint        - Run linter"
Write-Host "  make shell       - Django shell"
Write-Host ""
Write-Host "To create a superuser:"
Write-Host "  docker-compose exec api python manage.py createsuperuser"
Write-Host ""

Set-Location ..
