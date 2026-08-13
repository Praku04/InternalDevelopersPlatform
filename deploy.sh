#!/bin/bash

# Deployment script for Infrastructure Self-Service Platform
# Usage: ./deploy.sh

set -e

echo "🚀 Deploying Infrastructure Self-Service Platform..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please review and update if needed.${NC}"
fi

# Stop existing containers
echo -e "${BLUE}📦 Stopping existing containers...${NC}"
docker-compose down

# Remove old containers if they exist
echo -e "${BLUE}🗑️  Removing old containers...${NC}"
docker rm -f internaldevelopersplatform-frontend-1 internaldevelopersplatform-backend-1 2>/dev/null || true

# Build images
echo -e "${BLUE}🔨 Building Docker images (this may take a few minutes)...${NC}"
docker-compose build --no-cache

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker-compose up -d

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check container status
echo ""
echo -e "${BLUE}📊 Container Status:${NC}"
docker-compose ps

# Test backend
echo ""
echo -e "${BLUE}🧪 Testing backend health...${NC}"
if curl -s http://localhost:8100/api/v1/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose logs backend${NC}"
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  📊 Frontend (UI):      ${GREEN}http://${SERVER_IP}:3200${NC}"
echo -e "  🔌 Backend API:        ${GREEN}http://${SERVER_IP}:8100${NC}"
echo -e "  📖 API Documentation:  ${GREEN}http://${SERVER_IP}:8100/docs${NC}"
echo -e "  ❤️  Health Check:       ${GREEN}http://${SERVER_IP}:8100/api/v1/health${NC}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  View logs:       ${BLUE}docker-compose logs -f${NC}"
echo -e "  Restart:         ${BLUE}docker-compose restart${NC}"
echo -e "  Stop:            ${BLUE}docker-compose down${NC}"
echo -e "  Check status:    ${BLUE}docker-compose ps${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
