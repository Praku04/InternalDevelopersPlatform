#!/bin/bash
#
# Quick Deploy on VPS - One Command Deployment
# Usage: ./QUICK_DEPLOY_VPS.sh
#

set -e  # Exit on error

echo ""
echo "🚀 Quick Deploy - Internal Developers Platform"
echo "================================================"
echo ""

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main
echo ""

# Restart backend only (fastest deployment)
echo "🔄 Restarting backend..."
docker-compose restart backend
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 10
echo ""

# Test health endpoint
echo "🧪 Testing health endpoint..."
echo ""

if curl -f -s http://localhost:8100/api/v1/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
    echo ""
    curl -s http://localhost:8100/api/v1/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8100/api/v1/health
    echo ""
else
    echo "⚠️  Health check failed, trying /healthz..."
    if curl -f -s http://localhost:8100/healthz > /dev/null 2>&1; then
        echo "✅ Backend is responding at /healthz"
        curl -s http://localhost:8100/healthz
        echo ""
    else
        echo "❌ Backend not responding. Checking logs..."
        echo ""
        docker-compose logs --tail=30 backend
        exit 1
    fi
fi

echo ""
echo "📊 Container Status:"
docker-compose ps
echo ""

echo "================================================"
echo "✅ Deployment Complete!"
echo "================================================"
echo ""
echo "Access your platform:"
echo "  • Frontend: http://localhost:3200"
echo "  • Backend:  http://localhost:8100"
echo "  • API Docs: http://localhost:8100/docs"
echo "  • Health:   http://localhost:8100/api/v1/health"
echo ""
