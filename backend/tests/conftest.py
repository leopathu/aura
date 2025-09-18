from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.models import Base
from src.auth.database import get_db
from main import app
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

# Create tables before test session
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
