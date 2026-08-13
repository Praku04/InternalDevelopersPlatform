#!/bin/bash

echo "🔍 BACKEND DIAGNOSTIC TOOL"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "1️⃣ Checking all containers (including stopped)..."
echo "-----------------------------------------------------------"
docker-compose ps -a
echo ""

echo "2️⃣ Checking for any backend containers..."
echo "-----------------------------------------------------------"
docker ps -a | grep -i backend || echo "No backend containers found"
echo ""

echo "3️⃣ Checking backend service logs..."
echo "-----------------------------------------------------------"
docker-compose logs backend --tail 100 2>&1
echo ""

echo "4️⃣ Checking if backend image exists..."
echo "-----------------------------------------------------------"
docker images | grep internaldevelopersplatform-backend || echo "Backend image not found"
echo ""

echo "5️⃣ Checking port 8100 availability..."
echo "-----------------------------------------------------------"
if sudo lsof -i :8100 2>/dev/null; then
    echo "⚠️  Port 8100 is in use!"
else
    echo "✅ Port 8100 is available"
fi
echo ""

echo "6️⃣ Checking docker-compose configuration..."
echo "-----------------------------------------------------------"
docker-compose config | grep -A 20 "backend:" || echo "Backend service not in config"
echo ""

echo "7️⃣ Checking backend directory structure..."
echo "-----------------------------------------------------------"
ls -la backend/
echo ""
ls -la backend/app/ 2>/dev/null || echo "backend/app directory not found"
echo ""

echo "8️⃣ Checking backend Dockerfile..."
echo "-----------------------------------------------------------"
cat backend/Dockerfile
echo ""

echo "9️⃣ Checking Python requirements..."
echo "-----------------------------------------------------------"
cat backend/requirements.txt
echo ""

echo "🔟 Attempting to build backend manually..."
echo "-----------------------------------------------------------"
docker-compose build backend 2>&1 | tail -20
echo ""

echo "════════════════════════════════════════════════════════════"
echo "Diagnostic complete!"
echo ""
echo "Next steps:"
echo "1. If you see errors above, address them"
echo "2. If port 8100 is in use, kill that process"
echo "3. Try: docker-compose up backend"
echo "════════════════════════════════════════════════════════════"
