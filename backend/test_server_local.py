"""
Simple test to check if the server is working locally
"""

import requests
import json

def test_local_server():
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Local PolicyTracker Server")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server not running! Start with: python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: API Documentation
    print("\n2. Testing API docs...")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API documentation available at http://127.0.0.1:8000/docs")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test chatbot endpoint
    print("\n3. Testing basic chat endpoint...")
    try:
        chat_data = {
            "message": "Hello, test message",
            "conversation_id": "test_123"
        }
        response = requests.post(f"{base_url}/api/v1/chat", json=chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Chat endpoint working")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Test RAG endpoint (if available)
    print("\n4. Testing RAG chat endpoint...")
    try:
        rag_data = {
            "message": "What are education policies?",
            "conversation_id": "rag_test_123"
        }
        response = requests.post(f"{base_url}/api/v1/rag/chat", json=rag_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ RAG chat endpoint working")
            result = response.json()
            print(f"   Response preview: {result.get('response', '')[:100]}...")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎉 Server Testing Complete!")
    print("\nTo access your application:")
    print("• API Documentation: http://127.0.0.1:8000/docs")
    print("• Health Check: http://127.0.0.1:8000/health")
    print("• Chat API: http://127.0.0.1:8000/api/v1/chat")
    print("• RAG Chat API: http://127.0.0.1:8000/api/v1/rag/chat")
    
    return True

if __name__ == "__main__":
    test_local_server()
