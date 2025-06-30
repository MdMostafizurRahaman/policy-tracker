"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import init_database
from config.settings import settings
from routers import auth, policies, chat, admin, debug
from services.chatbot_service import init_chatbot
import uvicorn

def create_app():
    app = FastAPI(
        title="AI Policy Tracker API",
        description="Complete AI Policy Management System with Authentication, Submissions, and Admin Dashboard",
        version="4.1.0"
    )

    # Enhanced CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize database
    app.state.db = init_database()
    
    # Initialize chatbot
    init_chatbot(app.state.db)

    # Include routers
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
    app.include_router(policies.router, prefix="/api/policies", tags=["policies"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])

    @app.get("/")
    async def root():
        return {
            "message": "Enhanced AI Policy Database API with Database-Only Chatbot", 
            "version": "4.1.0",
            "status": "operational",
            "features": [
                "🔐 Complete Authentication System with Email Verification",
                "🤖 Database-Only AI Policy Chatbot",
                "🚀 Enhanced Google OAuth Integration", 
                "📝 Multi-Policy Area Submission System",
                "🗺️ Real-time Map Visualization",
                "👨‍💼 Advanced Admin Dashboard",
                "📊 Policy Scoring and Analytics",
                "📧 Improved Email System with Templates",
                "🔄 Automatic Policy-to-Master Migration",
                "🌍 Enhanced Country and Area Support",
                "⚡ Performance Optimizations",
                "🔍 Advanced Database Search and Filtering"
            ],
            "endpoints": {
                "authentication": "/api/auth/*",
                "submissions": "/api/policies/submit",
                "admin": "/api/admin/*",
                "policies": "/api/policies/public",
                "chatbot": "/api/chat",
                "health": "/health"
            }
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "database": "connected", "version": "4.1.0"}

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
