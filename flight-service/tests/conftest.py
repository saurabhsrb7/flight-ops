import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Clean up the test.db file before the test session starts
@pytest.fixture(scope="session", autouse=True)
def clean_test_db():
    db_path = "./test.db"
    if os.path.exists(db_path):
        os.remove(db_path)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db, set_engine_and_session
# Import models to ensure they're registered with Base
from models import Flight

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    set_engine_and_session(engine, TestingSessionLocal)
    # Create tables before each test
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after each test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    from app import create_app
    app = create_app(engine=engine, sessionmaker=TestingSessionLocal)
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c 