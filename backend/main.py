from fastapi import FastAPI
from dotenv import load_dotenv
import os
from auth import router as auth_router

load_dotenv()

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Aura FastAPI backend!"}
