# Aura
**Augmented Understanding & Retrieval Assistant**

A modern full-stack application built with Next.js frontend and FastAPI backend.

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python 3.11
- **Database**: PostgreSQL 16
- **Containerization**: Docker & Docker Compose

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd aura
```

2. Start the services:
```bash
docker-compose up -d
```

3. Access the applications:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## 📁 Project Structure

```
aura/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application file
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Backend container
│   └── .env.example       # Environment variables template
├── frontend/               # Next.js frontend
│   ├── src/               # Source code
│   ├── package.json       # Node.js dependencies
│   ├── Dockerfile         # Frontend container
│   └── .env.example       # Environment variables template
├── docker-compose.yml     # Multi-service container setup
└── README.md             # This file
```

## 🔧 Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@db:5432/aura_db
API_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Aura
NEXT_PUBLIC_APP_DESCRIPTION=Augmented Understanding & Retrieval Assistant
```

## 🛠️ Development

### Adding Backend Dependencies
```bash
cd backend
pip install <package-name>
pip freeze > requirements.txt
```

### Adding Frontend Dependencies
```bash
cd frontend
npm install <package-name>
```

### Database Migrations
The PostgreSQL database is automatically created when you start the Docker services. For migrations and advanced database operations, SQLAlchemy and Alembic are included in the backend dependencies.

## 📚 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by FastAPI's automatic OpenAPI integration.

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚢 Deployment

The application is containerized and ready for deployment on any Docker-compatible platform. The docker-compose.yml file defines the complete infrastructure including the database.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
