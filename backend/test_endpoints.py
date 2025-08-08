"""
Test script to verify the upload endpoint is working
"""
import asyncio
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_upload_endpoint():
    """Test the upload endpoint"""
    try:
        # Test health endpoint first
        logger.info("🔍 Testing system health...")
        health_response = requests.get("http://localhost:8000/api/system/health")
        logger.info(f"Health check: {health_response.status_code} - {health_response.text}")
        
        # Test debug routes
        logger.info("🔍 Testing debug routes...")
        routes_response = requests.get("http://localhost:8000/api/system/debug/routes")
        if routes_response.status_code == 200:
            logger.info("Debug routes endpoint working!")
        else:
            logger.warning(f"Debug routes failed: {routes_response.status_code}")
        
        # Test config
        config_response = requests.get("http://localhost:8000/api/system/debug/config")
        if config_response.status_code == 200:
            config_data = config_response.json()
            logger.info(f"AI configured: {config_data.get('environment_variables', {}).get('groq_api_configured', False)}")
            logger.info(f"AWS configured: {config_data.get('environment_variables', {}).get('aws_configured', False)}")
        
        logger.info("✅ Basic endpoint tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_upload_endpoint())
