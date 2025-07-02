#!/usr/bin/env python3
"""
Database initialization script for booking-service
"""
from database import engine, Base

def init_database():
    """Create all tables in the database"""
    print("Creating booking database tables...")
    Base.metadata.create_all(bind=engine)
    print("Booking database tables created successfully!")

if __name__ == "__main__":
    init_database()