.PHONY: help dev prod logs clean build

help:
	@echo "DC Projects - Docker Commands"
	@echo "=============================="
	@echo "make dev          - Start development environment"
	@echo "make prod         - Start production environment"
	@echo "make logs-dev     - View development logs"
	@echo "make logs-prod    - View production logs"
	@echo "make build-dev    - Build development image"
	@echo "make build-prod   - Build production image"
	@echo "make stop-dev     - Stop development"
	@echo "make stop-prod    - Stop production"
	@echo "make clean        - Remove all containers and volumes"
	@echo "make shell-dev    - Open shell in dev container"
	@echo "make shell-prod   - Open shell in prod container"

# Development commands
dev:
	@echo "Starting DC Projects in DEVELOPMENT mode..."
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✓ Development started on http://localhost:5000"
	@echo "✓ Default credentials: admin/admin"

build-dev:
	docker-compose -f docker-compose.dev.yml build --no-cache

logs-dev:
	docker-compose -f docker-compose.dev.yml logs -f

stop-dev:
	docker-compose -f docker-compose.dev.yml down

shell-dev:
	docker exec -it dc-projects-dev /bin/bash

# Production commands
prod:
	@echo "Starting DC Projects in PRODUCTION mode..."
	@echo "⚠️  Make sure to set DC_SECRET_KEY in .env.prod"
	docker-compose -f docker-compose.prod.yml up -d
	@echo "✓ Production started on http://localhost:80"
	@echo "✓ Behind Nginx reverse proxy"

build-prod:
	docker-compose -f docker-compose.prod.yml build --no-cache

logs-prod:
	docker-compose -f docker-compose.prod.yml logs -f

stop-prod:
	docker-compose -f docker-compose.prod.yml down

shell-prod:
	docker exec -it dc-projects-prod /bin/bash

# Utility commands
clean:
	@echo "Cleaning up all containers and volumes..."
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.prod.yml down -v
	@echo "✓ Cleanup complete"

restart-dev:
	make stop-dev
	make dev

restart-prod:
	make stop-prod
	make prod
