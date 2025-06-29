"""
Database connection and initialization.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    
database = Database()

async def get_database() -> AsyncIOMotorClient:
    return database.client

async def connect_to_mongo():
    """Create database connection"""
    logger.info("Connecting to MongoDB...")
    try:
        database.client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Test connection
        await database.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    logger.info("Closing MongoDB connection...")
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed")

def get_database_client():
    """Get the database client"""
    return database.client

def get_collections():
    """Get all database collections"""
    if not database.client:
        raise Exception("Database not connected")
    
    db = database.client[settings.DATABASE_NAME]
    return {
        "users": db.users,
        "temp_submissions": db.temp_submissions,
        "master_policies": db.master_policies,
        "admin_actions": db.admin_actions,
        "files": db.files,
        "otp_codes": db.otp_codes,
        "conversations": db.conversations
    }
