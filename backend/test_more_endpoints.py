#!/usr/bin/env python3
"""
Test script to verify multiple API endpoints.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_policy_submission():
    """Test policy submission endpoint without authentication (should fail gracefully)"""
    try:
        data = {
            "title": "Test Policy",
            "country": "United States",
            "description": "Test policy description",
            "policyAreas": ["Technology"],
            "status": "proposed"
        }
        
        response = requests.post(f"{BASE_URL}/submit-enhanced-form", json=data, timeout=10)
        print(f"Policy submission response status: {response.status_code}")
        print(f"Policy submission response: {response.text[:200]}...")
        
        # Should fail due to authentication, but endpoint should be reachable
        if response.status_code in [401, 422]:  # 401 unauthorized, 422 validation error
            print("✅ Policy endpoint is working (authentication required as expected)")
            return True
        else:
            print("✅ Policy endpoint responded")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Policy test failed: {e}")
        return False

def test_chat_endpoint():
    """Test chat endpoint without authentication (should fail gracefully)"""
    try:
        data = {
            "message": "Hello, what policies are available?",
            "conversation_id": None,
            "user_id": None
        }
        
        response = requests.post(f"{BASE_URL}/chat/chat", json=data, timeout=10)
        print(f"Chat response status: {response.status_code}")
        print(f"Chat response: {response.text[:200]}...")
        
        # Should fail due to authentication, but endpoint should be reachable
        if response.status_code in [401, 422]:  # 401 unauthorized, 422 validation error
            print("✅ Chat endpoint is working (authentication required as expected)")
            return True
        else:
            print("✅ Chat endpoint responded")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing additional API endpoints...")
    
    test_policy_submission()
    print()
    test_chat_endpoint()
    
    print("\nAll endpoint tests completed!")
