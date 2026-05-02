#!/usr/bin/env python3
"""
data_server/scripts/test_auth_api.py — Test authentication endpoints
Usage: python scripts/test_auth_api.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from app import create_app, db
from models import User
from utils import generate_uuid, hash_password

BASE_URL = "http://localhost:5001"


def setup_test_user():
    """Create a test user in the database"""
    app = create_app("development")
    with app.app_context():
        # Clear existing test user
        User.query.filter_by(username="testuser").delete()
        db.session.commit()
        
        # Create new test user
        user = User(
            id=generate_uuid(),
            username="testuser",
            password_hash=hash_password("testpass123"),
            email="test@example.com",
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"✓ Test user created: testuser/testpass123")


def test_login():
    """Test login endpoint"""
    print("\n--- Testing POST /api/auth/login ---")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if response.status_code == 200:
        return data.get("token")
    return None


def test_validate(token):
    """Test validate endpoint"""
    print("\n--- Testing POST /api/auth/validate ---")
    response = requests.post(
        f"{BASE_URL}/api/auth/validate",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_logout(token):
    """Test logout endpoint"""
    print("\n--- Testing POST /api/auth/logout ---")
    response = requests.post(
        f"{BASE_URL}/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_health():
    """Test health endpoint"""
    print("\n--- Testing GET /health ---")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def main():
    print("Starting data_server API tests...")
    print(f"Base URL: {BASE_URL}")
    
    try:
        # Setup
        setup_test_user()
        
        # Health check
        test_health()
        
        # Auth flow
        token = test_login()
        if token:
            test_validate(token)
            test_logout(token)
        else:
            print("✗ Login failed, skipping subsequent tests")
    
    except requests.ConnectionError:
        print(f"✗ Cannot connect to {BASE_URL}")
        print("  Make sure data_server is running: python app.py")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
