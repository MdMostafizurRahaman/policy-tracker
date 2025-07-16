"""
Test script to verify policy submission and admin retrieval
"""
import asyncio
import requests
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_policy_submission_flow():
    """Test the complete policy submission and admin flow"""
    try:
        base_url = "http://localhost:8000"
        
        logger.info("🔍 Testing policy submission and admin retrieval flow...")
        
        # Test 1: Check if we have any existing submissions
        logger.info("📋 Checking existing submissions...")
        try:
            admin_response = requests.get(f"{base_url}/api/admin/submissions")
            if admin_response.status_code == 200:
                data = admin_response.json()
                logger.info(f"Current submissions count: {len(data.get('data', []))}")
                
                if data.get('data'):
                    logger.info("📄 Sample submission structure:")
                    sample = data['data'][0]
                    for key, value in sample.items():
                        logger.info(f"  {key}: {type(value).__name__}")
                else:
                    logger.info("❌ No submissions found in admin panel")
            else:
                logger.error(f"Admin submissions endpoint failed: {admin_response.status_code}")
        except Exception as e:
            logger.error(f"Failed to check admin submissions: {str(e)}")
        
        # Test 2: Check database directly
        logger.info("🗄️ Checking database directly...")
        try:
            db_response = requests.get(f"{base_url}/api/system/debug/test-db")
            if db_response.status_code == 200:
                db_data = db_response.json()
                logger.info(f"Database status: {db_data.get('database_status')}")
            else:
                logger.error(f"Database test failed: {db_response.status_code}")
        except Exception as e:
            logger.error(f"Database test error: {str(e)}")
        
        # Test 3: Create a test policy submission (if we had auth token)
        logger.info("📝 Note: To test policy submission, you need to:")
        logger.info("   1. Login to get auth token")
        logger.info("   2. Upload a file via frontend")
        logger.info("   3. Check admin panel")
        
        # Test 4: Check pending submissions specifically
        logger.info("⏳ Checking pending submissions...")
        try:
            pending_response = requests.get(f"{base_url}/api/admin/submissions?status=pending_review")
            if pending_response.status_code == 200:
                pending_data = pending_response.json()
                logger.info(f"Pending submissions: {len(pending_data.get('data', []))}")
            else:
                logger.error(f"Pending submissions check failed: {pending_response.status_code}")
        except Exception as e:
            logger.error(f"Pending submissions error: {str(e)}")
        
        logger.info("✅ Policy submission flow test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_policy_submission_flow())
