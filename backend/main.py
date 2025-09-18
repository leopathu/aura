from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth import models 
from src.auth.routes import get_db, router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

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
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)