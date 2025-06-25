#!/usr/bin/env python3
"""
Database initialization script for user-service
"""
import os
from database import engine, Base
from models import User

def init_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database() 