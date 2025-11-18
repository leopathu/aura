from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, users, brains, documents, chat

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}", tags=["users", "organization"])
app.include_router(brains.router, prefix=f"{settings.API_V1_STR}/brains", tags=["brains"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/brains", tags=["documents"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}", tags=["chat"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to Aura RAG System",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
