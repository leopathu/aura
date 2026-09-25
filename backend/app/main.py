import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_v1_router
from app.seed import seed_initial_demo_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage directory exists
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    # Auto-create tables and seed initial demo data
    try:
        await seed_initial_demo_data()
    except Exception as e:
        print(f"Startup seeding warning: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Open Source Agentic Data & Knowledge Platform with Secure Tool Gateway, RBAC, and Policy Engine",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Aura Control Plane",
        "environment": settings.ENVIRONMENT
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "docs": "/docs",
        "api": f"{settings.API_V1_STR}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
