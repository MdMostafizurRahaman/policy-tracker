"""
Main Routes Configuration
Registers all API routes with the FastAPI application
"""
from fastapi import APIRouter
from controllers.auth_controller import router as auth_router
from controllers.admin_controller import router as admin_router
from controllers.public_controller_clean import router as public_router, api_router as public_api_router
from controllers.chat_controller import router as chat_router
from controllers.policy_controller_dynamodb import policy_router
from controllers.ai_analysis_controller_dynamodb import ai_analysis_router
from controllers.system_controller import system_router
from controllers.visit_controller import visit_router
from controllers.rag_chat_controller import create_rag_router
from config.data_constants import POLICY_AREAS

def setup_routes(app):
    """Setup all application routes"""
    
    # Include all DynamoDB-compatible controllers (prefixes already defined in controllers)
    app.include_router(auth_router, tags=["Authentication"])
    app.include_router(admin_router, tags=["Admin"]) 
    app.include_router(public_router, tags=["Public"])
    app.include_router(public_api_router, tags=["Public API"])  # Add the direct API router
    app.include_router(chat_router, tags=["Chat"])
    app.include_router(policy_router, prefix="/api/policy", tags=["Policy"])  # This one needs prefix
    app.include_router(ai_analysis_router, prefix="/api/ai-analysis", tags=["AI Analysis"])  # This one needs prefix
    app.include_router(system_router, tags=["System"])  # Debug and health endpoints
    app.include_router(visit_router, tags=["Visits"])  # Visit tracking endpoints
    app.include_router(policy_router, prefix="/api/policy", tags=["Policy"])
    
    # RAG (Retrieval-Augmented Generation) routes
    rag_router = create_rag_router()
    app.include_router(rag_router, tags=["RAG Chat"])

    @app.get("/api/policy-areas")
    async def get_policy_areas():
        return {"success": True, "policy_areas": POLICY_AREAS, "count": len(POLICY_AREAS)}
