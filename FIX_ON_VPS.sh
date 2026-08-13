#!/bin/bash

# This script fixes the terraform_service.py directly on the VPS

echo "🔧 Fixing terraform_service.py directly on VPS..."

cd ~/InternalDevelopersPlatform/backend/app/services

# Backup the original
cp terraform_service.py terraform_service.py.backup

# Fix the import line
sed -i 's/from app.repositories.request_repository import RequestRepository/from app.repositories.request_repository import get_request_repository/g' terraform_service.py

# Fix the usage line
sed -i 's/repo = RequestRepository()/repo = get_request_repository()/g' terraform_service.py

echo "✅ Fixed terraform_service.py"
echo ""

# Show the changes
echo "Checking imports (line 15):"
head -20 terraform_service.py | tail -10

echo ""
echo "Now rebuilding backend..."

cd ~/InternalDevelopersPlatform
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d

sleep 15

echo ""
echo "=== Container Status ==="
docker-compose ps

echo ""
echo "=== Health Check ==="
curl http://localhost:8100/api/v1/health

echo ""
echo "Done!"
