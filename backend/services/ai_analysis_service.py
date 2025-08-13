"""
Alias import for backward compatibility
"""
from .ai_analysis_service_dynamodb import ai_analysis_service

# Export the service so it can be imported as:
# from services.ai_analysis_service import ai_analysis_service
__all__ = ['ai_analysis_service']
