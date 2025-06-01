import motor.motor_asyncio
from config import MONGODB_URL

client = None
db = None

async def connect_to_mongo():
    global client, db
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
    db = client.ai_policy_database
    return db

async def get_db():
    if db is None:
        await connect_to_mongo()
    return db

async def close_mongo_connection():
    if client:
        client.close()