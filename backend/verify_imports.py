#!/usr/bin/env python3
"""
Comprehensive import verification script for the restructured backend.
"""
import sys
import importlib
import traceback

def test_import(module_name, description):
    """Test importing a specific module"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        print(f"❌ {description}: {module_name} - {str(e)}")
        return False

def main():
    """Run all import tests"""
    print("Testing all module imports in the restructured backend...\n")
    
    success_count = 0
    total_count = 0
    
    # Test core modules
    print("=== Core Modules ===")
    modules_to_test = [
        ("core.config", "Configuration"),
        ("core.database", "Database connection"),
        ("core.security", "Security utilities"),
        ("core.constants", "Constants"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print("\n=== Model Modules ===")
    modules_to_test = [
        ("models.auth", "Authentication models"),
        ("models.policy", "Policy models"),
        ("models.chat", "Chat models"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print("\n=== Service Modules ===")
    modules_to_test = [
        ("services.auth_service", "Authentication service"),
        ("services.email_service", "Email service"),
        ("services.policy_service", "Policy service"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print("\n=== API Modules ===")
    modules_to_test = [
        ("api.v1.endpoints.auth", "Auth endpoints"),
        ("api.v1.endpoints.policies", "Policy endpoints"),
        ("api.v1.endpoints.chat", "Chat endpoints"),
        ("api.v1.endpoints.admin", "Admin endpoints"),
        ("api.v1.api", "API router"),
        ("api", "Main API package"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print("\n=== Utilities ===")
    modules_to_test = [
        ("utils.helpers", "Helper utilities"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print("\n=== Main Application ===")
    modules_to_test = [
        ("app_main", "Main FastAPI application"),
    ]
    
    for module, desc in modules_to_test:
        total_count += 1
        if test_import(module, desc):
            success_count += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Successfully imported: {success_count}/{total_count} modules")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 All imports working perfectly!")
        return True
    else:
        print("⚠️  Some imports failed - check the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
