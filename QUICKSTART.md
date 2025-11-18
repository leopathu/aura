# Quick Start Guide - Aura RAG System

Get up and running in 5 minutes! 🚀

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

## Steps

### 1. Setup Environment

```bash
# Navigate to project directory
cd /home/leopathu/Public/aura

# Copy environment files
cp backend/.env.example backend/.env
```

### 2. Configure API Keys

Edit `backend/.env` and add:

```env
OPENAI_API_KEY=your-openai-key-here
SECRET_KEY=your-secret-key-here  # Generate: openssl rand -hex 32
```

### 3. Start Services

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

Or manually:

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head
```

### 4. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## First Use

1. **Register**: Create an account at http://localhost:3000
   - First user becomes org admin
   
2. **Create Brain**: Dashboard → Brains → Create Brain

3. **Upload Docs**: Select brain → Upload Documents

4. **Chat**: Go to Chat → Select brain → Ask questions!

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart a service
docker-compose restart backend

# View service status
docker-compose ps

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U postgres -d aura_db
```

## File Structure

```
aura/
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   ├── alembic/     # Database migrations
│   └── .env         # Configuration (create this)
├── frontend/         # Next.js frontend
│   ├── app/         # Pages
│   ├── components/  # React components
│   └── lib/         # Utilities
├── docker-compose.yml
└── README.md
```

## Troubleshooting

**Backend won't start?**
```bash
# Check logs
docker-compose logs backend

# Ensure .env has OPENAI_API_KEY
cat backend/.env | grep OPENAI
```

**Frontend errors?**
```bash
# Reinstall dependencies
docker-compose exec frontend npm install
docker-compose restart frontend
```

**Database issues?**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## What's Included

✅ **Organization Management** - Multi-tenant setup  
✅ **User Management** - Roles, departments, teams  
✅ **Brain System** - Multiple knowledge bases  
✅ **Document Upload** - PDF, DOCX, TXT, Images  
✅ **AI Chat** - RAG-powered conversations  
✅ **Search** - Semantic document search  
✅ **Access Control** - Fine-grained permissions  

## Next Steps

📖 Read the full [README.md](README.md)  
📋 Check [INSTALLATION.md](INSTALLATION.md) for detailed setup  
🔧 Explore [API Documentation](http://localhost:8000/docs)  

## Support

Having issues? 
- Check the logs: `docker-compose logs -f`
- Review [INSTALLATION.md](INSTALLATION.md)
- Open an issue on GitHub

---

Happy coding! 🎉
