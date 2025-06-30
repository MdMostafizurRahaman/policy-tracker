"""
Main Routes Configuration
Registers all API routes with the FastAPI application
"""
from fastapi import APIRouter
from controllers.auth_controller import router as auth_router
from controllers.policy_controller import router as policy_router
from controllers.admin_controller import router as admin_router
from controllers.public_controller import router as public_router
from controllers.debug_controller import router as debug_router
from controllers.chat_controller import router as chat_router

def setup_routes(app):
    """Setup all application routes"""
    
    # Create main API router
    api_router = APIRouter()
    
    # Include all controller routers
    api_router.include_router(auth_router)
    api_router.include_router(policy_router)
    api_router.include_router(admin_router)
    api_router.include_router(public_router)
    api_router.include_router(debug_router)
    api_router.include_router(chat_router)
    
    # Include the main router in the app
    app.include_router(api_router)
    
    return app
