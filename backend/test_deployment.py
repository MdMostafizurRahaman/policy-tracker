#!/usr/bin/env python3
"""
Test script to verify httpx import and enhanced chatbot functionality
"""
import sys
import os

def test_imports():
    """Test that all required imports work"""
    try:
        print("Testing imports...")
        
        # Test httpx import
        import httpx
        print("✅ httpx imported successfully")
        
        # Test enhanced chatbot service import
        sys.path.append('.')
        from services.chatbot_service_enhanced import enhanced_chatbot_service
        print("✅ Enhanced chatbot service imported successfully")
        
        # Test OpenAI API key configuration
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.startswith('sk-'):
            print("✅ OpenAI API key configured")
        else:
            print("❌ OpenAI API key not configured properly")
        
        print("\n🎉 All imports successful! Ready for deployment.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
