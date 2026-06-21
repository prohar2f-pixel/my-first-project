import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("SEED_ADMIN", "false")

from main import app
from database import get_db
from models import Base, User, Generation
from auth import hash_password

TEST_DB_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=test_engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    db = TestingSession()
    db.add(User(username="admin", password_hash=hash_password("admin123"), is_admin=True, credits=0))
    db.add(User(username="client1", password_hash=hash_password("pass123"), is_admin=False, credits=10))
    db.commit()
    db.close()

    yield TestClient(app)

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
