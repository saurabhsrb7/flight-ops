#!/usr/bin/env python3
"""
Database initialization script for payment-service
"""
import os
from database import engine, Base
from models import Payment

def init_database():
    """Create all tables in the database"""
    print("Creating payment database tables...")
    Base.metadata.create_all(bind=engine)
    print("Payment database tables created successfully!")

if __name__ == "__main__":
    init_database() 