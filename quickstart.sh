#!/bin/bash

# Quick start script for BookNow system

echo "🚀 Starting BookNow appointment system..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Start services
echo "📦 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Seed database
echo "🌱 Seeding database with availability slots..."
docker-compose exec backend python -m scripts.seed_db

echo ""
echo "✅ BookNow is running!"
echo ""
echo "📖 Access the application:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000/api"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "  - Assignment Brief: ASSIGNMENT_BRIEF.md"
echo "  - Architecture: ARCHITECTURE.md"
echo "  - README: README.md"
echo ""
echo "To stop: docker-compose down"
