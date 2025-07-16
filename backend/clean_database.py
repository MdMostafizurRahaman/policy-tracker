"""
Clean Database Script
Removes all data from DynamoDB tables and creates a fresh admin user
"""
import asyncio
import logging
from config.dynamodb import get_dynamodb
from models.user_dynamodb import User
from services.auth_service_dynamodb import AuthService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clean_all_tables():
    """Clean all data from DynamoDB tables"""
    try:
        dynamodb = await get_dynamodb()
        
        # List of table keys to clean  
        table_keys = [
            'users',
            'policies', 
            'chat_messages',
            'chat_sessions',
            'admin_data',
            'file_metadata'
        ]
        
        for table_key in table_keys:
            try:
                # Get all items from table
                items = await dynamodb.scan_items(table_key)
                
                # Delete each item
                for item in items:
                    # Get the primary key for each table
                    if table_key == 'users':
                        await dynamodb.delete_item(table_key, {'user_id': item['user_id']})
                    elif table_key == 'policies':
                        await dynamodb.delete_item(table_key, {'policy_id': item['policy_id']})
                    elif table_key == 'chat_messages':
                        await dynamodb.delete_item(table_key, {'message_id': item['message_id']})
                    elif table_key == 'chat_sessions':
                        await dynamodb.delete_item(table_key, {'session_id': item['session_id']})
                    elif table_key == 'admin_data':
                        await dynamodb.delete_item(table_key, {'admin_id': item['admin_id']})
                    elif table_key == 'file_metadata':
                        await dynamodb.delete_item(table_key, {'file_id': item['file_id']})
                
                logger.info(f"Cleaned {len(items)} items from {table_key}")
                
            except Exception as e:
                logger.warning(f"Could not clean table {table_key}: {str(e)}")
        
        logger.info("All tables cleaned successfully")
        
    except Exception as e:
        logger.error(f"Error cleaning tables: {str(e)}")

async def create_admin_user():
    """Create the initial admin user"""
    try:
        # Check if admin already exists
        admin_user = await User.find_by_email("admin@gmail.com")
        
        if admin_user:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user = await User.create_user(
            email="admin@gmail.com",
            password="admin123",
            name="Super Administrator",
            firstName="Super",
            lastName="Administrator", 
            country="United States",
            role="super_admin"
        )
        
        if admin_user:
            # Set email as verified for admin
            await admin_user.update({
                'is_email_verified': True
            })
            logger.info("Admin user created successfully")
        else:
            logger.error("Failed to create admin user")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")

async def main():
    """Main function to clean database and create admin"""
    logger.info("Starting database cleanup...")
    
    # Clean all tables
    await clean_all_tables()
    
    # Create fresh admin user
    await create_admin_user()
    
    logger.info("Database cleanup completed!")

if __name__ == "__main__":
    asyncio.run(main())
