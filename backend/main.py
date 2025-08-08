"""
AI Policy Tracker - Enhanced Main Application
Refactored FastAPI application using AWS DynamoDB for better AWS integration
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import uvicorn
from contextlib import asynccontextmanager

# Import configuration and setup
from config.settings import settings
from config.dynamodb import get_dynamodb, init_dynamodb
from middleware.cors import add_cors_middleware
from routes.main import setup_routes

# Import AWS service for initialization
from services.aws_service import aws_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(exist_ok=True)

async def initialize_super_admin():
    """Initialize super admin with enhanced error handling"""
    try:
        from services.admin_service_dynamodb import admin_service
        result = await admin_service.initialize_super_admin(
            settings.SUPER_ADMIN_EMAIL,
            settings.SUPER_ADMIN_PASSWORD
        )
        logger.info(f"Super admin initialization: {result.get('message', 'Unknown status')}")
    except Exception as e:
        logger.error(f"Error initializing super admin: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - replaces deprecated on_event"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        # Initialize DynamoDB connection
        dynamodb_connected = await init_dynamodb()
        if dynamodb_connected:
            logger.info("DynamoDB connection established successfully")
            
            # Initialize AWS S3 service
            await aws_service.initialize()
            
            # Initialize super admin
            await initialize_super_admin()
            
            # Chatbot service is initialized automatically when imported by controllers
            logger.info("Chatbot service available via controllers")
            
            logger.info("Application startup completed successfully")
        else:
            logger.warning("DynamoDB not available - running with limited functionality")
            
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        # Don't raise - let the app continue for development
    
    yield
    
    # Shutdown
    try:
        # Close AWS service connections
        await aws_service.close()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize FastAPI app with lifespan
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        lifespan=lifespan
    )
    
    # Add CORS middleware
    add_cors_middleware(app)
    
    # Setup routes
    setup_routes(app)
    return app

# Create the app instance
app = create_app()

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
        # Check DynamoDB connection
        dynamodb_client = await get_dynamodb()
        if dynamodb_client and dynamodb_client.tables['users']:
            return {
                "status": "healthy",
                "database": "DynamoDB connected",
                "version": settings.APP_VERSION
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "database": "DynamoDB disconnected",
                    "version": settings.APP_VERSION
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "DynamoDB error",
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
