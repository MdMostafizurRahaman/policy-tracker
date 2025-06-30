"""
CORS Middleware Configuration
Handles Cross-Origin Resource Sharing settings
"""
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

def add_cors_middleware(app):
    """Add CORS middleware to FastAPI app"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
