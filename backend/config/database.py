"""
Database Configuration and Connection Management
Handles MongoDB connection and database operations
"""
import motor.motor_asyncio
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            # Use MONGO_URI from environment variables
            mongo_uri = settings.MONGODB_URL
            self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
            self.db = self.client[settings.DATABASE_NAME]
            
            # Test connection
            await self.db.command("ping")
            logger.info(f"Database connection successful to: {settings.DATABASE_NAME}")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    def get_collection(self, collection_name: str):
        """Get a collection from the database"""
        if self.db is None:
            raise RuntimeError("Database not connected")
        return self.db[collection_name]

# Global database instance
database = Database()

# Collection shortcuts
def get_users_collection():
    return database.get_collection("users")

def get_temp_submissions_collection():
    return database.get_collection("temp_submissions")

def get_master_policies_collection():
    return database.get_collection("master_policies")

def get_admin_actions_collection():
    return database.get_collection("admin_actions")

def get_files_collection():
    return database.get_collection("files")

def get_otp_collection():
    return database.get_collection("otp_codes")
