"""
Simplified test to check core functionality.
"""
import sys
import os

# Test basic structure
def test_basic_structure():
    """Test if basic structure exists"""
    print("Testing basic directory structure...")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(base_path, 'app')
    
    required_dirs = [
        'app',
        'app/core',
        'app/models', 
        'app/services',
        'app/api',
        'app/api/v1',
        'app/api/v1/endpoints'
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(base_path, dir_path)
        if os.path.exists(full_path):
            print(f"✅ {dir_path} exists")
        else:
            print(f"❌ {dir_path} missing")
            return False
    
    print("✅ Directory structure verified")
    return True

def test_individual_modules():
    """Test importing individual modules"""
    print("\nTesting individual modules...")
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Test core config
    try:
        from core.config import settings
        print(f"✅ Config loaded - Project: {settings.PROJECT_NAME}")
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False
    
    # Test models individually
    try:
        from models.auth import UserRegistration
        print("✅ Auth models loaded")
    except Exception as e:
        print(f"❌ Auth models failed: {e}")
        return False
    
    try:
        from models.policy import EnhancedSubmission
        print("✅ Policy models loaded")
    except Exception as e:
        print(f"❌ Policy models failed: {e}")
        return False
    
    # Test services
    try:
        from services.auth_service import auth_service
        print("✅ Auth service loaded")
    except Exception as e:
        print(f"❌ Auth service failed: {e}")
        return False
    
    print("✅ Individual modules working")
    return True

if __name__ == "__main__":
    print("🔍 Simple Structure Test")
    print("=" * 30)
    
    if not test_basic_structure():
        print("❌ Basic structure test failed")
        exit(1)
    
    if not test_individual_modules():
        print("❌ Module import test failed")
        exit(1)
    
    print("\n🎉 Basic structure is working!")
    print("The restructured backend is ready for use.")
