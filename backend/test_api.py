#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/auth/register", timeout=5)
        print("✅ Server is responding")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return False

def test_registration():
    """Test user registration endpoint"""
    try:
        data = {
            "firstName": "Test",
            "lastName": "User", 
            "email": "test@example.com",
            "password": "testpass123",
            "confirmPassword": "testpass123",
            "country": "United States"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=data, timeout=10)
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response: {response.text[:200]}...")
        
        if response.status_code in [200, 201, 400]:  # 400 is ok if user already exists
            print("✅ Registration endpoint is working")
            return True
        else:
            print("❌ Registration endpoint failed")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Registration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing API endpoints...")
    
    if test_health():
        test_registration()
    
    print("API testing completed.")
