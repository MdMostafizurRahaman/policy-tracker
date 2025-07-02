"""
AI Policy Tracker - Enhanced Main Application
Refactored FastAPI application following layered architecture pattern
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import uvicorn

# Import configuration and setup
from config.settings import settings
from config.database import database
from middleware.cors import add_cors_middleware
from routes.main import setup_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION
    )
    
    # Add CORS middleware
    add_cors_middleware(app)
    
    # Setup routes
    setup_routes(app)
    
    return app

# Create the app instance
app = create_app()

async def initialize_super_admin():
    """Initialize super admin with enhanced error handling"""
    try:
        from services.admin_service import admin_service
        await admin_service.initialize_super_admin(
            settings.SUPER_ADMIN_EMAIL,
            settings.SUPER_ADMIN_PASSWORD
        )
    except Exception as e:
        logger.error(f"Error initializing super admin: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Connect to database
    if await database.connect():
        await initialize_super_admin()
        
        # Initialize fast cache
        try:
            from cache_manager import init_cache
            await init_cache()
            logger.info("Fast cache initialized")
        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
        
        # Initialize the database-only chatbot
        try:
            from services.chatbot_service import init_chatbot
            init_chatbot(database.client)
            logger.info("Database-only chatbot initialized")
        except ImportError:
            logger.info("Chatbot module not found, skipping chatbot initialization")
        
        logger.info("Application startup completed successfully")
    else:
        logger.error("Application startup failed - database connection issue")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application")
    await database.disconnect()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        await database.db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
