#!/bin/bash
#
# Rebuild Backend Script
# Run this on your VPS to pull latest code and rebuild the backend
#

set -e  # Exit on error

echo "========================================="
echo "  Rebuilding Backend on VPS"
echo "========================================="
echo ""

# Step 1: Pull latest code
echo "1️⃣  Pulling latest code from Git..."
git pull origin main
echo "✅ Code updated"
echo ""

# Step 2: Stop all services
echo "2️⃣  Stopping all services..."
docker-compose down
echo "✅ Services stopped"
echo ""

# Step 3: Remove backend image to force rebuild
echo "3️⃣  Removing old backend image..."
docker rmi internaldevelopersplatform-backend:latest 2>/dev/null || echo "No old image found"
echo "✅ Old image removed"
echo ""

# Step 4: Rebuild backend with no cache
echo "4️⃣  Rebuilding backend (this may take a minute)..."
docker-compose build --no-cache backend
echo "✅ Backend rebuilt"
echo ""

# Step 5: Start all services
echo "5️⃣  Starting all services..."
docker-compose up -d
echo "✅ Services started"
echo ""

# Step 6: Wait for services to start
echo "⏳ Waiting 10 seconds for services to initialize..."
sleep 10
echo ""

# Step 7: Check container status
echo "📊 Container Status:"
docker-compose ps
echo ""

# Step 8: Test backend health
echo "🧪 Testing backend health..."
sleep 3  # Give backend a bit more time

if curl -f -s http://localhost:8100/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    curl -s http://localhost:8100/api/v1/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8100/api/v1/health
else
    echo "❌ Backend health check failed. Checking logs..."
    echo ""
    echo "Last 30 lines of backend logs:"
    docker-compose logs --tail=30 backend
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "Services:"
echo "  • Backend:  http://localhost:8100"
echo "  • Frontend: http://localhost:3200"
echo "  • DynamoDB: http://localhost:8001"
echo ""
echo "Quick checks:"
echo "  docker-compose ps                  # Check status"
echo "  docker-compose logs -f backend     # Follow backend logs"
echo "  curl http://localhost:8100/api/v1/health  # Test backend"
echo ""
