.PHONY: up down build logs test clean

# Start the entire full-stack application via Docker Compose
up:
	docker compose up -d --build

# Stop and remove containers and networks
down:
	docker compose down

# Rebuild containers
build:
	docker compose build

# Follow logs from all containers
logs:
	docker compose logs -f

# Run backend test suite locally
test:
	python -m pytest backend/tests -v

# Clean up temporary test files, caches and build artifacts
clean:
	rm -rf backend/.pytest_cache frontend/dist backend/__pycache__ backend/app/__pycache__ backend/tests/__pycache__
