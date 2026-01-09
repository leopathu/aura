#!/bin/bash

# Aura MVP - Quick Setup Script

echo "🌟 Setting up Aura AI Agent Platform..."

# Check if Docker is installed
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
    
    # Ask user if they want to use Docker
    read -p "Do you want to use Docker for setup? (y/n): " use_docker
    
    if [ "$use_docker" = "y" ]; then
        echo "🐳 Starting services with Docker..."
        docker-compose up -d
        
        echo ""
        echo "✅ Aura is running!"
        echo "📱 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/api/docs"
        echo ""
        echo "To view logs: docker-compose logs -f"
        echo "To stop: docker-compose down"
        exit 0
    fi
fi

# Manual setup
echo "📦 Setting up manually..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is required but not installed"
    exit 1
fi

echo "✓ All prerequisites found"

# Setup backend
echo ""
echo "🔧 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    
    # Generate encryption key
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env file
    sed -i "s/your-encryption-key-must-be-32-bytes-long/$ENCRYPTION_KEY/" .env
    sed -i "s/your-secret-key-change-in-production-min-32-chars/$SECRET_KEY/" .env
    
    echo "⚠️  Please update the database URL and other settings in backend/.env"
fi

# Setup database
echo ""
echo "🗄️  Setting up database..."
read -p "Database name (default: aura): " DB_NAME
DB_NAME=${DB_NAME:-aura}

read -p "Do you want to create the database? (y/n): " create_db
if [ "$create_db" = "y" ]; then
    createdb $DB_NAME 2>/dev/null || echo "Database might already exist"
    psql $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"
    psql $DB_NAME -f ../database/init.sql
    echo "✓ Database initialized"
fi

# Setup frontend
echo ""
echo "🎨 Setting up frontend..."
cd ../frontend

npm install

if [ ! -f ".env.local" ]; then
    echo "Creating .env.local file..."
    cp .env.example .env.local
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "2. Frontend: cd frontend && npm run dev"
echo ""
echo "📱 Frontend will be at: http://localhost:3000"
echo "🔧 Backend API will be at: http://localhost:8000"
echo "📚 API Docs will be at: http://localhost:8000/api/docs"
