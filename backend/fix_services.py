#!/usr/bin/env python3
"""
Quick fix script to replace service imports with lazy getters
"""
import re
import os

def fix_service_imports():
    # Files to fix
    files_to_fix = [
        "controllers/policy_controller.py",
        "controllers/admin_controller.py", 
        "controllers/chat_controller.py"
    ]
    
    backend_dir = "d:/Policy_Tracker/PolicyTracker/backend"
    
    # Service replacements
    replacements = {
        "policy_service": "get_policy_service()",
        "admin_service": "get_admin_service()",
        "chat_service": "get_chat_service()"
    }
    
    for file_path in files_to_fix:
        full_path = os.path.join(backend_dir, file_path)
        if os.path.exists(full_path):
            print(f"Fixing {file_path}...")
            
            with open(full_path, 'r') as f:
                content = f.read()
            
            # Replace service instances with getter calls
            for service, getter in replacements.items():
                # Replace import
                content = re.sub(
                    rf"from services\..*_service import {service}",
                    f"from services.{service.replace('_service', '_service')} import {getter.replace('()', '')}",
                    content
                )
                
                # Replace usage
                content = re.sub(
                    rf"\b{service}\.",
                    f"{getter}.",
                    content
                )
            
            with open(full_path, 'w') as f:
                f.write(content)
            
            print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_service_imports()
