#!/bin/bash

# Aura MVP - Verification Script
# This script checks if all required files and dependencies are present

echo "🔍 Verifying Aura MVP Setup..."
echo ""

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
    else
        echo "✗ $1 - MISSING"
        ((ERRORS++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
    else
        echo "✗ $1/ - MISSING"
        ((ERRORS++))
    fi
}

echo "📁 Checking Project Structure..."
check_dir "backend"
check_dir "backend/app"
check_dir "backend/app/api"
check_dir "backend/app/core"
check_dir "backend/app/db"
check_dir "backend/app/schemas"
check_dir "backend/app/services"
check_dir "frontend"
check_dir "frontend/app"
check_dir "frontend/lib"
check_dir "database"

echo ""
echo "📄 Checking Backend Files..."
check_file "backend/requirements.txt"
check_file "backend/Dockerfile"
check_file "backend/.env.example"
check_file "backend/app/main.py"
check_file "backend/app/core/config.py"
check_file "backend/app/core/security.py"
check_file "backend/app/core/encryption.py"
check_file "backend/app/db/base.py"
check_file "backend/app/db/session.py"
check_file "backend/app/db/models/user.py"
check_file "backend/app/db/models/organization.py"
check_file "backend/app/db/models/credential.py"
check_file "backend/app/db/models/agent.py"

echo ""
echo "📄 Checking Frontend Files..."
check_file "frontend/package.json"
check_file "frontend/tsconfig.json"
check_file "frontend/Dockerfile"
check_file "frontend/.env.example"
check_file "frontend/app/layout.tsx"
check_file "frontend/app/page.tsx"
check_file "frontend/app/globals.css"
check_file "frontend/lib/api.ts"
check_file "frontend/lib/store.ts"

echo ""
echo "📄 Checking Configuration Files..."
check_file "docker-compose.yml"
check_file "database/init.sql"
check_file "README.md"
check_file "SETUP.md"
check_file "setup.sh"

echo ""
echo "🔧 Checking Dependencies..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python: $PYTHON_VERSION"
else
    echo "⚠ Python 3 not found"
    ((WARNINGS++))
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js: $NODE_VERSION"
else
    echo "⚠ Node.js not found"
    ((WARNINGS++))
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    echo "✓ PostgreSQL: $PSQL_VERSION"
else
    echo "⚠ PostgreSQL not found"
    ((WARNINGS++))
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✓ Docker: $DOCKER_VERSION"
else
    echo "⚠ Docker not found (optional)"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✓ Docker Compose: $COMPOSE_VERSION"
else
    echo "⚠ Docker Compose not found (optional)"
fi

echo ""
echo "📊 Verification Summary"
echo "======================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Your Aura MVP is ready."
    echo ""
    echo "Next steps:"
    echo "1. Run './setup.sh' for automated setup"
    echo "2. Or run 'docker-compose up -d' if using Docker"
    echo "3. Or follow manual setup in SETUP.md"
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Setup is complete but some optional dependencies are missing."
    echo "   Warnings: $WARNINGS"
    echo ""
    echo "You can still run the application, but some features may be limited."
else
    echo "❌ Setup is incomplete!"
    echo "   Errors: $ERRORS"
    echo "   Warnings: $WARNINGS"
    echo ""
    echo "Please ensure all required files are present."
    exit 1
fi

# Check if .env files exist
echo ""
echo "🔐 Environment Configuration"
echo "==========================="

if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found"
    echo "   Run: cp backend/.env.example backend/.env"
    echo "   Then edit with your configuration"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "⚠️  frontend/.env.local not found"
    echo "   Run: cp frontend/.env.example frontend/.env.local"
    echo "   Then edit with your configuration"
fi

echo ""
echo "📚 Documentation Files"
echo "====================="
echo "✓ README.md - Project overview"
echo "✓ SETUP.md - Setup instructions"
echo "✓ MVP_SUMMARY.md - Feature documentation"
echo "✓ QUICK_REFERENCE.md - Quick commands"
echo "✓ COMPLETE.md - Complete guide"

echo ""
echo "🎉 Verification complete!"
