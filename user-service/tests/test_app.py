import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json

def test_register_user_success(client):
    """Test successful user registration"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] == True
    assert "id" in data
    assert "created_at" in data
    # Password should not be returned
    assert "password" not in data
    assert "hashed_password" not in data

def test_register_user_duplicate_email(client):
    """Test registration with duplicate email"""
    user_data = {
        "email": "duplicate@example.com",
        "username": "user1",
        "full_name": "User One",
        "password": "password123"
    }
    
    # Register first user
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    
    # Try to register second user with same email
    user_data2 = {
        "email": "duplicate@example.com",
        "username": "user2",
        "full_name": "User Two",
        "password": "password456"
    }
    response = client.post("/register", json=user_data2)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_register_user_duplicate_username(client):
    """Test registration with duplicate username"""
    user_data = {
        "email": "user1@example.com",
        "username": "duplicateuser",
        "full_name": "User One",
        "password": "password123"
    }
    
    # Register first user
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    
    # Try to register second user with same username
    user_data2 = {
        "email": "user2@example.com",
        "username": "duplicateuser",
        "full_name": "User Two",
        "password": "password456"
    }
    response = client.post("/register", json=user_data2)
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]

def test_register_user_invalid_email(client):
    """Test registration with invalid email format"""
    user_data = {
        "email": "invalid-email",
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422  # Validation error

def test_register_user_missing_fields(client):
    """Test registration with missing required fields"""
    # Missing email
    user_data = {
        "username": "testuser",
        "full_name": "Test User",
        "password": "testpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422
    
    # Missing username
    user_data = {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422
    
    # Missing password
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 422

def test_login_success(client):
    """Test successful login"""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "full_name": "Login User",
        "password": "loginpass123"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    
    # Then login
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 0

def test_login_invalid_username(client):
    """Test login with non-existent username"""
    login_data = {
        "username": "nonexistentuser",
        "password": "password123"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_invalid_password(client):
    """Test login with incorrect password"""
    # First register a user
    user_data = {
        "email": "wrongpass@example.com",
        "username": "wrongpassuser",
        "full_name": "Wrong Pass User",
        "password": "correctpass123"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    
    # Then login with wrong password
    login_data = {
        "username": user_data["username"],
        "password": "wrongpassword"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user_success(client):
    """Test getting current user with valid token"""
    # First register and login to get token
    user_data = {
        "email": "current@example.com",
        "username": "currentuser",
        "full_name": "Current User",
        "password": "currentpass123"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = client.post("/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Get current user with token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]
    assert data["is_active"] == True

def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_get_current_user_no_token(client):
    """Test getting current user without token"""
    response = client.get("/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_get_user_by_id_success(client):
    """Test getting user by ID"""
    # First register a user
    user_data = {
        "email": "getbyid@example.com",
        "username": "getbyiduser",
        "full_name": "Get By ID User",
        "password": "getbyidpass123"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    user_id = register_response.json()["id"]
    
    # Get user by ID
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["full_name"] == user_data["full_name"]

def test_get_user_by_id_not_found(client):
    """Test getting non-existent user by ID"""
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_get_user_by_id_invalid_id(client):
    """Test getting user with invalid ID format"""
    response = client.get("/users/invalid")
    assert response.status_code == 422  # Validation error for non-integer ID

def test_password_hashing(client):
    """Test that passwords are properly hashed"""
    user_data = {
        "email": "hash@example.com",
        "username": "hashuser",
        "full_name": "Hash User",
        "password": "hashpass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    
    # Verify password is not returned in response
    assert "password" not in data
    assert "hashed_password" not in data
    
    # Verify we can still login with the original password
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = client.post("/token", data=login_data)
    assert login_response.status_code == 200

def test_user_active_status(client):
    """Test that newly registered users are active by default"""
    user_data = {
        "email": "active@example.com",
        "username": "activeuser",
        "full_name": "Active User",
        "password": "activepass123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] == True

def test_register_and_login_complete_flow(client):
    """Test complete user registration and login flow"""
    # Step 1: Register user
    user_data = {
        "email": "flow@example.com",
        "username": "flowuser",
        "full_name": "Flow User",
        "password": "flowpass123"
    }
    register_response = client.post("/register", json=user_data)
    assert register_response.status_code == 200
    user_info = register_response.json()
    
    # Step 2: Login to get token
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = client.post("/token", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Step 3: Get current user with token
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/users/me", headers=headers)
    assert me_response.status_code == 200
    me_data = me_response.json()
    
    # Step 4: Get user by ID
    get_user_response = client.get(f"/users/{user_info['id']}")
    assert get_user_response.status_code == 200
    get_user_data = get_user_response.json()
    
    # Verify all responses are consistent
    assert me_data["id"] == user_info["id"]
    assert me_data["id"] == get_user_data["id"]
    assert me_data["email"] == user_data["email"]
    assert get_user_data["email"] == user_data["email"] 