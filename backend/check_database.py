"""
Direct database check to see stored policies
"""
import asyncio
import logging
from config.dynamodb import get_dynamodb

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_content():
    """Check what's actually stored in the database"""
    try:
        logger.info("🗄️ Checking database content directly...")
        
        # Get DynamoDB connection
        db = await get_dynamodb()
        
        # Check policies table
        logger.info("📋 Checking policies table...")
        policies = await db.scan_table('policies')
        logger.info(f"Found {len(policies)} policies in database")
        
        if policies:
            logger.info("📄 Sample policy structure:")
            sample_policy = policies[0]
            for key, value in sample_policy.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}: dict with {len(value)} keys")
                elif isinstance(value, list):
                    logger.info(f"  {key}: list with {len(value)} items")
                else:
                    logger.info(f"  {key}: {type(value).__name__} = {str(value)[:50]}")
        else:
            logger.info("❌ No policies found in database")
        
        # Check file_metadata table
        logger.info("📁 Checking file_metadata table...")
        files = await db.scan_table('file_metadata')
        logger.info(f"Found {len(files)} files in database")
        
        if files:
            for file_meta in files:
                logger.info(f"  File: {file_meta.get('filename')} - {file_meta.get('upload_status')}")
        
        # Check users table
        logger.info("👥 Checking users table...")
        users = await db.scan_table('users')
        logger.info(f"Found {len(users)} users in database")
        
        if users:
            for user in users:
                logger.info(f"  User: {user.get('email')} - {user.get('role', 'user')}")
        
        logger.info("✅ Database check completed!")
        
    except Exception as e:
        logger.error(f"❌ Database check failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_database_content())
