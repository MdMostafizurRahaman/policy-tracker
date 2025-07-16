"""
Services initialization file.
"""
from .auth_service_dynamodb import auth_service
from .email_service import email_service  
# Remove broken MongoDB service import
# from .policy_service import policy_service

__all__ = [
    "auth_service",
    "email_service"
]
