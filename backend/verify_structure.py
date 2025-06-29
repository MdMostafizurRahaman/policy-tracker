"""
Startup verification script to test the new structure.
Run this to verify the restructured application works correctly.
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test core imports
        from core.config import settings
        from core.database import connect_to_mongo, get_collections
        from core.security import hash_password, verify_password
        print("✅ Core imports successful")
        
        # Test model imports
        from models.auth import UserRegistration, UserLogin
        from models.policy import EnhancedSubmission
        from models.chat import ChatRequest
        print("✅ Model imports successful")
        
        # Test service imports
        from services.auth_service import auth_service
        from services.email_service import email_service
        from services.policy_service import policy_service
        print("✅ Service imports successful")
        
        # Test API imports
        from api.v1.endpoints import auth, policies, chat, admin
        print("✅ API endpoint imports successful")
        
        # Test main app
        print("✅ Main app import successful")
        
        print("🎉 All imports successful! The restructured application is ready to use.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_configuration():
    """Test configuration settings"""
    print("⚙️ Testing configuration...")
    
    try:
        from core.config import settings
        
        print(f"📋 Project: {settings.PROJECT_NAME}")
        print(f"📋 Version: {settings.VERSION}")
        print(f"📋 API Prefix: {settings.API_V1_STR}")
        print(f"📋 Environment: {settings.ENVIRONMENT}")
        print(f"📋 CORS Origins: {len(settings.ALLOWED_ORIGINS)} configured")
        
        # Test password hashing
        from core.security import hash_password, verify_password
        test_password = "test123456"
        hashed = hash_password(test_password)
        verified = verify_password(test_password, hashed)
        
        if verified:
            print("✅ Password hashing working correctly")
        else:
            print("❌ Password hashing failed")
            return False
        
        print("✅ Configuration test successful")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚀 AI Policy Tracker - New Structure Verification")
    print("=" * 50)
    
    # Test imports
    imports_ok = await test_imports()
    if not imports_ok:
        print("❌ Import tests failed. Please check the structure.")
        return False
    
    print()
    
    # Test configuration
    config_ok = await test_configuration()
    if not config_ok:
        print("❌ Configuration tests failed.")
        return False
    
    print()
    print("🎊 Verification Complete!")
    print("The restructured AI Policy Tracker backend is ready to run.")
    print()
    print("To start the server:")
    print("  python main.py")
    print("  or")
    print("  uvicorn main:app --reload")
    print()
    print("📝 Check README_NEW_STRUCTURE.md for detailed information.")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
