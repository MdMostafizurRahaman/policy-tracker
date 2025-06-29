"""
API v1 router that combines all endpoint routers.
"""
from fastapi import APIRouter
from .endpoints import auth, policies, chat, admin

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(policies.router, prefix="", tags=["policies"])  # No prefix for backward compatibility
router.include_router(chat.router, prefix="/chat", tags=["chat"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "4.0.0"}
