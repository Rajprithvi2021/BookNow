#!/bin/bash
# Docker initialization script for BookNow

set -e

echo "🚀 BookNow Docker Setup"
echo "======================="
echo ""

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker is installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DB_USER=booknow
DB_PASSWORD=booknow_secure_pass_123
DB_NAME=booknow

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Environment
NODE_ENV=development
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

echo ""
echo "✅ BookNow is running!"
echo ""
echo "📍 Access points:"
echo "   - Frontend:  http://localhost:3000"
echo "   - Backend:   http://localhost:8000"
echo "   - API Docs:  http://localhost:8000/docs"
echo "   - Adminer:   http://localhost:8081"
echo ""
echo "📊 Database credentials:"
echo "   - Server:   localhost:5432"
echo "   - User:     booknow"
echo "   - Database: booknow"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
