#!/bin/bash

echo "🔍 Checking backend container issue..."
echo ""

# Check if backend container exists
if docker ps -a | grep -q "internaldevelopersplatform-backend"; then
    echo "📋 Backend container found. Checking logs..."
    echo ""
    docker logs internaldevelopersplatform-backend-1 --tail 50
    echo ""
else
    echo "⚠️  Backend container not found!"
    echo ""
fi

echo "🔧 Fixing backend container..."
echo ""

# Stop all services
echo "1️⃣ Stopping all services..."
docker-compose down

# Remove backend container if it exists
echo "2️⃣ Removing old backend container..."
docker rm -f internaldevelopersplatform-backend-1 2>/dev/null || true

# Remove backend image
echo "3️⃣ Removing backend image..."
docker rmi internaldevelopersplatform-backend 2>/dev/null || true

# Rebuild backend only
echo "4️⃣ Rebuilding backend image..."
docker-compose build --no-cache backend

# Start all services
echo "5️⃣ Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🧪 Testing backend..."
if curl -s http://localhost:8100/api/v1/health | grep -q "healthy"; then
    echo "✅ Backend is healthy!"
else
    echo "❌ Backend health check failed. Checking logs..."
    echo ""
    docker logs internaldevelopersplatform-backend-1 --tail 30
fi

echo ""
echo "Done! Check the status above."
