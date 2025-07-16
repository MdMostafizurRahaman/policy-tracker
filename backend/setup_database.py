"""
Database Migration and Setup Script
Creates necessary DynamoDB tables and migrates data if needed
"""
import asyncio
import logging
from config.dynamodb import DynamoDBClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_database():
    """Setup and initialize all DynamoDB tables"""
    try:
        logger.info("🚀 Starting database setup...")
        
        # Initialize DynamoDB client
        db_client = DynamoDBClient()
        
        # Connect and create tables
        await db_client.connect()
        
        logger.info("✅ Database setup completed successfully!")
        logger.info("📋 Created/verified tables:")
        for table_name in db_client.table_names.values():
            logger.info(f"   • {table_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {str(e)}")
        return False

async def verify_tables():
    """Verify that all tables exist and are accessible"""
    try:
        logger.info("🔍 Verifying table accessibility...")
        
        db_client = DynamoDBClient()
        await db_client.connect()
        
        # Test each table
        for table_key, table_name in db_client.table_names.items():
            try:
                table = db_client.tables[table_key]
                response = table.describe_table()
                status = response['Table']['TableStatus']
                logger.info(f"   ✅ {table_name}: {status}")
            except Exception as e:
                logger.error(f"   ❌ {table_name}: {str(e)}")
        
        logger.info("✅ Table verification completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Table verification failed: {str(e)}")
        return False

async def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("📝 Creating sample data...")
        
        from config.dynamodb import get_dynamodb
        from datetime import datetime
        import uuid
        
        db = await get_dynamodb()
        
        # Sample user (for testing purposes)
        sample_user = {
            "user_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "is_verified": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Insert sample user
        await db.insert_item('users', sample_user)
        
        # Sample policy submission
        sample_policy = {
            "policy_id": str(uuid.uuid4()),
            "user_id": sample_user["user_id"],
            "user_email": sample_user["email"],
            "country": "United States",
            "status": "pending_review",
            "submission_type": "form",
            "policy_areas": [{
                "area_id": "ai_governance",
                "area_name": "AI Governance",
                "policies": [{
                    "policyName": "National AI Strategy",
                    "policyId": "US-AI-2024-001",
                    "policyDescription": "Comprehensive strategy for responsible AI development and deployment",
                    "targetGroups": ["Government", "Industry", "Academia"],
                    "implementation": {
                        "yearlyBudget": "1000000",
                        "budgetCurrency": "USD",
                        "privateSecFunding": True,
                        "deploymentYear": 2024
                    }
                }]
            }],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        await db.insert_item('policies', sample_policy)
        
        logger.info("✅ Sample data created successfully!")
        logger.info(f"   • Sample user: {sample_user['email']}")
        logger.info(f"   • Sample policy: {sample_policy['policy_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {str(e)}")
        return False

async def main():
    """Main migration function"""
    logger.info("🔧 Policy Tracker Database Migration Tool")
    logger.info("=" * 50)
    
    # Step 1: Setup database
    if not await setup_database():
        return False
    
    # Step 2: Verify tables
    if not await verify_tables():
        return False
    
    # Step 3: Create sample data (optional)
    create_samples = input("\n📝 Create sample data for testing? (y/n): ").lower().strip()
    if create_samples == 'y':
        await create_sample_data()
    
    logger.info("\n🎉 Database migration completed successfully!")
    logger.info("Your Policy Tracker system is ready to use.")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
