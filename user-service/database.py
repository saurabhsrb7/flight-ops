from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/user_service"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Allow tests to override engine and session
_def_engine = engine
_def_session = SessionLocal

def set_engine_and_session(new_engine, new_session):
    global engine, SessionLocal
    engine = new_engine
    SessionLocal = new_session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 