#!/usr/bin/env python3
"""
Database initialization script for notification-service
"""
from database import engine, Base
from models import Notification

def init_database():
    """Create all tables in the database"""
    print("Creating notification database tables...")
    Base.metadata.create_all(bind=engine)
    print("Notification database tables created successfully!")

if __name__ == "__main__":
    init_database()