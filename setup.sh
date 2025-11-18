#!/bin/bash

# Aura RAG System Setup Script

echo "🚀 Setting up Aura RAG System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create backend .env if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend .env file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your API keys (OPENAI_API_KEY, SECRET_KEY)"
fi

# Create frontend .env.local if it doesn't exist
if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend .env.local file..."
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > frontend/.env.local
fi

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if backend is ready
echo "🔍 Checking backend health..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    attempt=$((attempt+1))
    echo "Waiting for backend... ($attempt/$max_attempts)"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
    exit 1
fi

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec -T backend alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed!"
else
    echo "❌ Database migrations failed. Check logs with: docker-compose logs backend"
    exit 1
fi

echo "
✨ Setup complete! ✨

🌐 Frontend: http://localhost:3000
🔧 Backend API: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
🗄️  Qdrant: http://localhost:6333/dashboard

📝 Next steps:
1. Edit backend/.env and add your OPENAI_API_KEY
2. Restart backend: docker-compose restart backend
3. Visit http://localhost:3000 to get started!

🔍 View logs:
   docker-compose logs -f

🛑 Stop services:
   docker-compose down
"
