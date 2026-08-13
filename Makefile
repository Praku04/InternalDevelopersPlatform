.PHONY: help install test lint format security clean \
        backend-install backend-test backend-run backend-lint backend-format \
        frontend-install frontend-dev frontend-build frontend-test \
        terraform-fmt terraform-validate \
        docker-up docker-down docker-logs \
        azure-devops-validate

help:
	@echo "AI Cloud Self-Service Platform - Makefile Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install              - Install all dependencies"
	@echo "  make backend-install      - Install backend dependencies"
	@echo "  make frontend-install     - Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make backend-run          - Run backend dev server"
	@echo "  make frontend-dev         - Run frontend dev server"
	@echo "  make docker-up            - Start all services with Docker Compose"
	@echo "  make docker-down          - Stop all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test                 - Run all tests"
	@echo "  make backend-test         - Run backend tests"
	@echo "  make frontend-test        - Run frontend tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                 - Run all linters"
	@echo "  make format               - Format all code"
	@echo "  make security             - Run security scans"
	@echo ""
	@echo "Terraform:"
	@echo "  make terraform-fmt        - Format Terraform code"
	@echo "  make terraform-validate   - Validate Terraform modules"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                - Clean build artifacts"
	@echo "  make docker-logs          - View Docker logs"

# Installation
install: backend-install frontend-install

backend-install:
	cd backend && pip install -r requirements.txt --break-system-packages

frontend-install:
	cd frontend && npm install

# Development
backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && npm run dev

# Testing
test: backend-test

backend-test:
	cd backend && pytest -v

frontend-test:
	cd frontend && npm run test

# Code Quality
lint: backend-lint

backend-lint:
	@echo "Running backend linters..."
	cd backend && python -m ruff check app/
	cd backend && python -m mypy app/ --ignore-missing-imports

format: backend-format terraform-fmt

backend-format:
	@echo "Formatting backend code..."
	cd backend && python -m ruff format app/
	cd backend && python -m black app/

# Security
security: security-checkov security-trivy

security-checkov:
	@echo "Running Checkov security scan..."
	checkov --directory terraform/modules \
		--config-file security/checkov/config.yaml \
		--compact

security-trivy:
	@echo "Running Trivy security scan..."
	trivy config terraform/modules \
		--config security/trivy/trivy.yaml

# Terraform
terraform-fmt:
	@echo "Formatting Terraform code..."
	terraform fmt -recursive terraform/

terraform-validate:
	@echo "Validating Terraform modules..."
	@for dir in terraform/modules/*/; do \
		echo "Validating $$dir"; \
		cd $$dir && terraform init -backend=false && terraform validate; \
		cd ../..; \
	done

# Azure DevOps
azure-devops-validate:
	@echo "Validating Azure DevOps pipelines..."
	@echo "Note: This requires Azure CLI with DevOps extension"
	az pipelines build validate --yaml-path azure-devops/pipelines/deployment.yml

# Docker
docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Utilities
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf terraform/generated/* 2>/dev/null || true
	@echo "Clean complete"

# Quick start for development
dev:
	@echo "Starting development environment..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@make -j2 backend-run frontend-dev
