import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth import models
from src.auth.routes import router, get_db
import os
from dotenv import load_dotenv

# Load environment variables from a .env.test file or similar
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
assert DATABASE_URL is not None, "DATABASE_URL environment variable must be set for tests"

# Create SQLAlchemy engine and session for the test database
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test DB session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def test_app():
    # Create all tables before tests
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = override_get_db

    yield app

    # Drop tables after tests complete
    models.Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(test_app):
    return TestClient(test_app)

def test_register_user(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json()["msg"] == "User registered successfully"

def test_register_existing_user(client):
    # Register the user once
    client.post("/auth/register", json={
        "email": "test2@example.com",
        "password": "password123"
    })
    # Try to register again with same email
    response = client.post("/auth/register", json={
        "email": "test2@example.com",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "mypassword"
    })
    response = client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_fail(client):
    response = client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
