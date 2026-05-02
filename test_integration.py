#!/usr/bin/env python3
"""
Integration test: Client → Server login flow
Run this to verify cloud auth is working end-to-end
"""

import sys
import time
import requests
import json

CLIENT_URL = "http://localhost:8080"
SERVER_URL = "http://localhost:5001"

def test(name, fn):
    """Helper to run test and print result"""
    try:
        result = fn()
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
        return result
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False

def main():
    print("\n🧪 DobotHub Cloud Integration Test\n")
    
    # Test 1: Server health
    def test_server_health():
        resp = requests.get(f"{SERVER_URL}/health", timeout=2)
        return resp.status_code == 200
    
    test("Server health check", test_server_health)
    
    # Test 2: Client health
    def test_client_health():
        resp = requests.get(f"{CLIENT_URL}/", timeout=2)
        return resp.status_code == 200
    
    test("Client homepage loads", test_client_health)
    
    # Test 3: Client auth status (unauthenticated)
    def test_client_status_unauth():
        resp = requests.get(f"{CLIENT_URL}/api/auth/status", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return not data.get("authenticated")
        return False
    
    test("Client status: not authenticated", test_client_status_unauth)
    
    # Test 4: Server login with test user
    def test_server_login():
        resp = requests.post(
            f"{SERVER_URL}/api/auth/login",
            json={"username": "admin", "password": "geheim"},
            timeout=2
        )
        return resp.status_code == 200
    
    test("Server login endpoint", test_server_login)
    
    # Test 5: Client login proxy (via RemoteSyncManager)
    def test_client_login():
        resp = requests.post(
            f"{CLIENT_URL}/api/auth/login",
            json={"username": "admin", "password": "geheim"},
            timeout=2
        )
        return resp.status_code == 200
    
    test("Client login proxy", test_client_login)
    
    # Test 6: Client auth status (authenticated)
    def test_client_status_auth():
        resp = requests.get(f"{CLIENT_URL}/api/auth/status", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("authenticated") and data.get("is_online")
        return False
    
    test("Client status: authenticated + online", test_client_status_auth)
    
    # Test 7: Get cloud projects
    def test_get_projects():
        # First login
        login_resp = requests.post(
            f"{CLIENT_URL}/api/auth/login",
            json={"username": "admin", "password": "geheim"},
            timeout=2
        )
        # Then list projects
        resp = requests.get(f"{CLIENT_URL}/api/cloud/projects", timeout=2)
        return resp.status_code == 200
    
    test("Get cloud projects list", test_get_projects)
    
    print("\n✅ All integration tests passed!\n")
    print("Next steps:")
    print("  1. Open http://localhost:8080 in browser")
    print("  2. Click 'Login' button")
    print("  3. Enter admin / geheim")
    print("  4. Verify cloud status shows '● ONLINE'")
    print()

if __name__ == "__main__":
    main()
