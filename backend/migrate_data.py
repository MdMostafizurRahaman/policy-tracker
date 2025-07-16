"""
Data Migration Script: MongoDB to DynamoDB
Run this script when you have DynamoDB permissions to migrate existing data
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
import pymongo
import json

# MongoDB imports
from config.database import database
from config.settings import settings

# DynamoDB imports  
from config.dynamodb import get_dynamodb, init_dynamodb
from models.user_dynamodb import User
from models.policy_dynamodb import Policy
from models.chat_dynamodb import ChatMessage, ChatSession
from models.admin_dynamodb import AdminData
from models.file_metadata_dynamodb import FileMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMigrator:
    """Migrate data from MongoDB to DynamoDB"""
    
    def __init__(self):
        self.mongodb = None
        self.dynamodb = None
        self.migration_stats = {
            'users': {'attempted': 0, 'successful': 0, 'failed': 0},
            'policies': {'attempted': 0, 'successful': 0, 'failed': 0},
            'chat_messages': {'attempted': 0, 'successful': 0, 'failed': 0},
            'admin_data': {'attempted': 0, 'successful': 0, 'failed': 0},
            'file_metadata': {'attempted': 0, 'successful': 0, 'failed': 0}
        }
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            # Initialize MongoDB connection
            await database.connect()
            self.mongodb = database.db
            logger.info("MongoDB connection established")
            
            # Initialize DynamoDB connection
            dynamodb_connected = await init_dynamodb()
            if dynamodb_connected:
                self.dynamodb = await get_dynamodb()
                logger.info("DynamoDB connection established")
                return True
            else:
                logger.error("Failed to connect to DynamoDB - check permissions")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize connections: {str(e)}")
            return False
    
    def convert_objectid_to_string(self, data: Dict) -> Dict:
        """Convert MongoDB ObjectId to string"""
        if isinstance(data, dict):
            converted = {}
            for key, value in data.items():
                if isinstance(value, pymongo.collection.ObjectId):
                    converted[key] = str(value)
                elif isinstance(value, dict):
                    converted[key] = self.convert_objectid_to_string(value)
                elif isinstance(value, list):
                    converted[key] = [
                        self.convert_objectid_to_string(item) if isinstance(item, dict) 
                        else str(item) if isinstance(item, pymongo.collection.ObjectId)
                        else item for item in value
                    ]
                else:
                    converted[key] = value
            return converted
        return data
    
    async def migrate_users(self):
        """Migrate users from MongoDB to DynamoDB"""
        logger.info("Starting user migration...")
        
        try:
            # Get users from MongoDB
            users_collection = self.mongodb.users
            mongo_users = users_collection.find({})
            
            for mongo_user in mongo_users:
                self.migration_stats['users']['attempted'] += 1
                
                try:
                    # Convert ObjectId to string
                    user_data = self.convert_objectid_to_string(mongo_user)
                    
                    # Map MongoDB fields to DynamoDB User model
                    user = User(
                        user_id=user_data.get('_id', user_data.get('user_id')),
                        email=user_data.get('email'),
                        password=user_data.get('password'),
                        full_name=user_data.get('full_name', user_data.get('name', '')),
                        phone=user_data.get('phone'),
                        organization=user_data.get('organization'),
                        role=user_data.get('role', 'user'),
                        is_active=user_data.get('is_active', True),
                        is_email_verified=user_data.get('is_email_verified', False),
                        google_id=user_data.get('google_id'),
                        profile_picture=user_data.get('profile_picture'),
                        created_at=user_data.get('created_at', datetime.utcnow().isoformat()),
                        updated_at=user_data.get('updated_at', datetime.utcnow().isoformat()),
                        last_login=user_data.get('last_login'),
                        login_count=user_data.get('login_count', 0)
                    )
                    
                    # Save to DynamoDB
                    if await user.save():
                        self.migration_stats['users']['successful'] += 1
                        logger.info(f"Migrated user: {user.email}")
                    else:
                        self.migration_stats['users']['failed'] += 1
                        logger.error(f"Failed to save user: {user.email}")
                        
                except Exception as e:
                    self.migration_stats['users']['failed'] += 1
                    logger.error(f"Error migrating user {mongo_user.get('email', 'unknown')}: {str(e)}")
            
            logger.info(f"User migration completed: {self.migration_stats['users']}")
            
        except Exception as e:
            logger.error(f"Error in user migration: {str(e)}")
    
    async def migrate_policies(self):
        """Migrate policies from MongoDB to DynamoDB"""
        logger.info("Starting policy migration...")
        
        try:
            # Get policies from MongoDB
            policies_collection = self.mongodb.policies
            mongo_policies = policies_collection.find({})
            
            for mongo_policy in mongo_policies:
                self.migration_stats['policies']['attempted'] += 1
                
                try:
                    # Convert ObjectId to string
                    policy_data = self.convert_objectid_to_string(mongo_policy)
                    
                    # Map MongoDB fields to DynamoDB Policy model
                    policy = Policy(
                        policy_id=policy_data.get('_id', policy_data.get('policy_id')),
                        user_id=policy_data.get('user_id'),
                        title=policy_data.get('title'),
                        description=policy_data.get('description'),
                        content=policy_data.get('content'),
                        category=policy_data.get('category', 'general'),
                        tags=policy_data.get('tags', []),
                        status=policy_data.get('status', 'draft'),
                        file_paths=policy_data.get('file_paths', []),
                        file_metadata=policy_data.get('file_metadata', {}),
                        ai_analysis=policy_data.get('ai_analysis', {}),
                        created_at=policy_data.get('created_at', datetime.utcnow().isoformat()),
                        updated_at=policy_data.get('updated_at', datetime.utcnow().isoformat()),
                        published_at=policy_data.get('published_at'),
                        version=policy_data.get('version', 1),
                        is_public=policy_data.get('is_public', False)
                    )
                    
                    # Save to DynamoDB
                    if await policy.save():
                        self.migration_stats['policies']['successful'] += 1
                        logger.info(f"Migrated policy: {policy.title}")
                    else:
                        self.migration_stats['policies']['failed'] += 1
                        logger.error(f"Failed to save policy: {policy.title}")
                        
                except Exception as e:
                    self.migration_stats['policies']['failed'] += 1
                    logger.error(f"Error migrating policy {mongo_policy.get('title', 'unknown')}: {str(e)}")
            
            logger.info(f"Policy migration completed: {self.migration_stats['policies']}")
            
        except Exception as e:
            logger.error(f"Error in policy migration: {str(e)}")
    
    async def migrate_chat_messages(self):
        """Migrate chat messages from MongoDB to DynamoDB"""
        logger.info("Starting chat message migration...")
        
        try:
            # Get chat messages from MongoDB
            chat_collection = self.mongodb.chat_messages
            mongo_messages = chat_collection.find({})
            
            for mongo_message in mongo_messages:
                self.migration_stats['chat_messages']['attempted'] += 1
                
                try:
                    # Convert ObjectId to string
                    message_data = self.convert_objectid_to_string(mongo_message)
                    
                    # Map MongoDB fields to DynamoDB ChatMessage model
                    message = ChatMessage(
                        message_id=message_data.get('_id', message_data.get('message_id')),
                        user_id=message_data.get('user_id'),
                        policy_id=message_data.get('policy_id'),
                        session_id=message_data.get('session_id'),
                        message_type=message_data.get('message_type', 'user'),
                        content=message_data.get('content'),
                        metadata=message_data.get('metadata', {}),
                        attachments=message_data.get('attachments', []),
                        ai_context=message_data.get('ai_context', {}),
                        confidence_score=message_data.get('confidence_score'),
                        response_time=message_data.get('response_time'),
                        created_at=message_data.get('created_at', datetime.utcnow().isoformat()),
                        updated_at=message_data.get('updated_at', datetime.utcnow().isoformat()),
                        is_deleted=message_data.get('is_deleted', False),
                        feedback=message_data.get('feedback', {})
                    )
                    
                    # Save to DynamoDB
                    if await message.save():
                        self.migration_stats['chat_messages']['successful'] += 1
                    else:
                        self.migration_stats['chat_messages']['failed'] += 1
                        
                except Exception as e:
                    self.migration_stats['chat_messages']['failed'] += 1
                    logger.error(f"Error migrating chat message: {str(e)}")
            
            logger.info(f"Chat message migration completed: {self.migration_stats['chat_messages']}")
            
        except Exception as e:
            logger.error(f"Error in chat message migration: {str(e)}")
    
    async def run_migration(self):
        """Run the complete migration process"""
        logger.info("Starting MongoDB to DynamoDB migration...")
        
        if not await self.initialize():
            logger.error("Failed to initialize - migration aborted")
            return False
        
        try:
            # Run migrations in order
            await self.migrate_users()
            await self.migrate_policies()
            await self.migrate_chat_messages()
            
            # Print final statistics
            logger.info("Migration completed!")
            logger.info("Final Statistics:")
            for collection, stats in self.migration_stats.items():
                logger.info(f"{collection}: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return False
    
    def export_migration_report(self):
        """Export migration report to file"""
        report = {
            'migration_date': datetime.utcnow().isoformat(),
            'statistics': self.migration_stats,
            'total_attempted': sum(stats['attempted'] for stats in self.migration_stats.values()),
            'total_successful': sum(stats['successful'] for stats in self.migration_stats.values()),
            'total_failed': sum(stats['failed'] for stats in self.migration_stats.values())
        }
        
        with open(f'migration_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Migration report exported")

async def main():
    """Main migration function"""
    migrator = DataMigrator()
    
    print("🔄 MongoDB to DynamoDB Migration Tool")
    print("=====================================")
    print("This tool will migrate your data from MongoDB to DynamoDB.")
    print("Make sure you have:")
    print("1. DynamoDB permissions configured")
    print("2. Both MongoDB and DynamoDB connections working")
    print()
    
    confirm = input("Do you want to proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    success = await migrator.run_migration()
    
    if success:
        migrator.export_migration_report()
        print("✅ Migration completed successfully!")
        print("📊 Check the migration report file for detailed statistics.")
    else:
        print("❌ Migration failed. Check the logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
