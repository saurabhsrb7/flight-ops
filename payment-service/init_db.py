#!/usr/bin/env python3
"""
Database initialization script for flight-service
"""
import os
from database import engine, Base
from models import Payment

def init_database():
    """Create all tables in the database"""
    print("Creating flight database tables...")
    Base.metadata.create_all(bind=engine)
    print("Flight database tables created successfully!")

if __name__ == "__main__":
    init_database() 