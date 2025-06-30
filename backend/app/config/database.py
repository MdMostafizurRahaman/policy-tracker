"""
Database configuration and connection
"""
import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

def init_database():
    """Initialize and return MongoDB client"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    return client

def get_database():
    """Get database instance"""
    client = init_database()
    return client.ai_policy_database
