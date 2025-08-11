"""
Comprehensive OpenAI API and Chatbot Debug Script
Tests API keys, database connections, and chatbot responses
"""
import os
import asyncio
import httpx
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

async def test_openai_api():
    """Test OpenAI API directly"""
    print("=" * 50)
    print("TESTING OPENAI API")
    print("=" * 50)
    
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ No OpenAI API key found in environment!")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    print(f"Key length: {len(api_key)}")
    print(f"Starts with 'sk-': {'✅' if api_key.startswith('sk-') else '❌'}")
    
    # Test API call
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "What is Bangladesh's education policy? Keep it brief."}
        ],
        "max_tokens": 150,
        "temperature": 0.7
    }
    
    try:
        print("\n🔄 Making API call...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions", 
                headers=headers, 
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ OpenAI API Working!")
                print("Response:")
                print("-" * 30)
                print(data['choices'][0]['message']['content'])
                print("-" * 30)
                return True
            elif response.status_code == 401:
                print("❌ Invalid API Key - Check your OpenAI key")
                print(f"Response: {response.text}")
                return False
            elif response.status_code == 403:
                print("❌ Access Denied - Check billing/model access")
                print(f"Response: {response.text}")
                return False
            elif response.status_code == 429:
                print("❌ Rate Limited - Too many requests")
                print(f"Response: {response.text}")
                return False
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception during API call: {e}")
        return False

async def test_database_connection():
    """Test database connection"""
    print("\n" + "=" * 50)
    print("TESTING DATABASE CONNECTION")
    print("=" * 50)
    
    try:
        # Add current directory to path to import modules
        sys.path.append(os.path.dirname(__file__))
        
        from config.dynamodb import get_dynamodb
        
        db = await get_dynamodb()
        print("✅ Database connection successful")
        
        # Test if we can access policies
        try:
            policies_table = db.Table('policies')
            response = await policies_table.scan(Limit=1)
            print(f"✅ Policies table accessible, sample data: {len(response.get('Items', []))} items")
        except Exception as e:
            print(f"⚠️ Could not access policies table: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_chatbot_service():
    """Test the chatbot service"""
    print("\n" + "=" * 50)
    print("TESTING CHATBOT SERVICE")
    print("=" * 50)
    
    try:
        # Import chatbot service
        sys.path.append(os.path.dirname(__file__))
        
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        from models.chat import ChatRequest
        
        print("✅ Chatbot service imported successfully")
        
        # Test cache update
        print("🔄 Updating cache...")
        await enhanced_chatbot_service._update_cache()
        
        print(f"Policy cache: {len(enhanced_chatbot_service.policy_cache) if enhanced_chatbot_service.policy_cache else 0} policies")
        print(f"Countries: {len(enhanced_chatbot_service.countries_cache) if enhanced_chatbot_service.countries_cache else 0}")
        print(f"Areas: {len(enhanced_chatbot_service.areas_cache) if enhanced_chatbot_service.areas_cache else 0}")
        
        # Test different types of queries
        test_queries = [
            "Hello",
            "What is Bangladesh's education policy?",
            "Compare AI policies between USA and Bangladesh",
            "What's the weather today?"  # Should redirect
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}: '{query}' ---")
            try:
                test_request = ChatRequest(
                    message=query,
                    conversation_id=None,
                    user_id="test_user"
                )
                
                response = await enhanced_chatbot_service.chat(test_request)
                print(f"✅ Response: {response.response[:200]}...")
                
            except Exception as e:
                print(f"❌ Error with query '{query}': {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Chatbot service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_backend_server():
    """Test if backend server is running"""
    print("\n" + "=" * 50)
    print("TESTING BACKEND SERVER")
    print("=" * 50)
    
    backend_urls = [
        "http://localhost:8000",
        "http://localhost:5000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5000"
    ]
    
    for url in backend_urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    print(f"✅ Backend server running at {url}")
                    return url
        except:
            continue
    
    print("❌ Backend server not found on common ports")
    print("Try starting it with: python main.py")
    return None

async def main():
    """Run all tests"""
    print("🚀 POLICYTRACKER CHATBOT DEBUG SCRIPT")
    print("=" * 60)
    
    results = {}
    
    # Test OpenAI API
    results['openai'] = await test_openai_api()
    
    # Test Database
    results['database'] = await test_database_connection()
    
    # Test Chatbot Service
    results['chatbot'] = await test_chatbot_service()
    
    # Test Backend Server
    results['server'] = await test_backend_server()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test.upper()}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! Your chatbot should be working.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        
        if not results.get('openai'):
            print("\n🔧 OPENAI FIX:")
            print("1. Check your API key in .env file")
            print("2. Verify billing is set up at https://platform.openai.com/account/billing")
            print("3. Try using gpt-3.5-turbo instead of gpt-4")
        
        if not results.get('database'):
            print("\n🔧 DATABASE FIX:")
            print("1. Make sure AWS credentials are configured")
            print("2. Check DynamoDB table exists")
            print("3. Verify AWS region settings")
        
        if not results.get('chatbot'):
            print("\n🔧 CHATBOT FIX:")
            print("1. Check imports in chatbot_service_enhanced.py")
            print("2. Ensure all methods are implemented")
            print("3. Check for syntax errors")

if __name__ == "__main__":
    asyncio.run(main())
