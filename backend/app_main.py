"""
Main FastAPI application factory.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import connect_to_mongo, close_mongo_connection, get_collections
from core.security import hash_password
from api import router as api_router
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        """Initialize application on startup"""
        logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
        
        try:
            # Connect to database
            await connect_to_mongo()
            
            # Initialize super admin
            await initialize_super_admin()
            
            # Initialize chatbot
            await initialize_chatbot()
            
            logger.info("Application startup completed successfully")
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            raise
    
    # Add shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown"""
        logger.info("Shutting down application...")
        await close_mongo_connection()
        logger.info("Application shutdown completed")
    
    return app

async def initialize_super_admin():
    """Initialize super admin with enhanced error handling"""
    try:
        collections = get_collections()
        existing_admin = await collections["users"].find_one({"email": settings.SUPER_ADMIN_EMAIL})
        
        if not existing_admin:
            admin_doc = {
                "firstName": "Super",
                "lastName": "Admin",
                "email": settings.SUPER_ADMIN_EMAIL,
                "password": hash_password(settings.SUPER_ADMIN_PASSWORD),
                "country": "Global",
                "is_admin": True,
                "is_super_admin": True,
                "is_verified": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await collections["users"].insert_one(admin_doc)
            logger.info("Super admin created successfully")
        else:
            # Update password if needed
            from core.security import verify_password
            if not verify_password(settings.SUPER_ADMIN_PASSWORD, existing_admin["password"]):
                await collections["users"].update_one(
                    {"email": settings.SUPER_ADMIN_EMAIL},
                    {"$set": {
                        "password": hash_password(settings.SUPER_ADMIN_PASSWORD),
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info("Super admin password updated")
            logger.info("Super admin already exists")
    except Exception as e:
        logger.error(f"Error initializing super admin: {e}")

async def initialize_chatbot():
    """Initialize the chatbot"""
    try:
        from chatbot import init_chatbot
        from core.database import get_database_client
        
        client = get_database_client()
        init_chatbot(client)
        logger.info("Database-only chatbot initialized")
    except Exception as e:
        logger.error(f"Error initializing chatbot: {e}")

# Create the app
app = create_application()
