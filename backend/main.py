from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth import models 
from src.auth.routes import get_db, router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import psycopg2
from pgvector.psycopg2 import register_vector

# Load environment variables
load_dotenv()

from src.auth import models
from src.auth.database import engine  # PostgreSQL engine

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Aura API",
    description="Augmented Understanding & Retrieval Assistant API",
    version="1.0.0"
)

app.include_router(router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://frontend:3000",
        os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Aura API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "aura-backend"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working correctly", "data": "test_data"}

@app.get("/api/db-status")
async def database_status():
    """Check database connection and PgVector extension availability"""
    try:
        # Connect to database
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        register_vector(conn)
        
        with conn.cursor() as cur:
            # Check if pgvector extension is available
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
            vector_extension = cur.fetchone()
            
            # Get database version
            cur.execute("SELECT version();")
            db_version = cur.fetchone()[0]
            
        conn.close()
        
        return {
            "database": "connected",
            "version": db_version,
            "pgvector": "available" if vector_extension else "not_available",
            "message": "Database and vector extension are ready"
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e),
            "message": "Failed to connect to database"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)