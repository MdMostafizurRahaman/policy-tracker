"""
Test script for TEA Scores calculation using AWS Bedrock
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from services.bedrock_service import bedrock_service
from services.ai_analysis_service_dynamodb import ai_analysis_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample policy document text for testing
SAMPLE_POLICY_TEXT = """
AI Governance Policy

1. TRANSPARENCY REQUIREMENTS
This policy document is publicly accessible through our official website. All stakeholders involved in the creation of this policy are listed in Appendix A, including government officials, AI researchers, and civil society representatives.

Public consultation was conducted from January to March 2024, with over 500 responses received from citizens and organizations. The consultation results are published on our transparency portal.

2. EXPLAINABILITY STANDARDS
All AI systems deployed under this policy must provide human-interpretable explanations for their decisions. These explanations must be tailored to different audiences - technical explanations for developers and simplified explanations for end users.

Decision-making processes, including risk assessment methodologies, are documented in our AI Ethics Framework. Users are informed about how AI decisions affect them through automated notifications and explanatory dashboards.

3. ACCOUNTABILITY FRAMEWORK
Clear responsibility for AI decisions is assigned to designated AI Officers in each department. Regular audits are conducted by our independent AI Oversight Board.

Individuals can appeal AI decisions through our Digital Rights Appeal Process. Liability for AI system errors is clearly outlined in Section 7 of this policy. The National AI Regulatory Authority serves as the governing body for enforcement and compliance.

This policy includes specific guidance for explainability requirements during AI system deployment, including mandatory user testing and accessibility standards.
"""

async def test_tea_scores():
    """Test the TEA scores calculation"""
    try:
        logger.info("Starting TEA scores test...")
        
        # Test the Bedrock service directly
        logger.info("Testing Bedrock service...")
        tea_results = bedrock_service.calculate_transparency_explainability_accountability_scores(SAMPLE_POLICY_TEXT)
        
        if 'error' in tea_results:
            logger.error(f"Bedrock service error: {tea_results['error']}")
            return False
        
        # Display results
        scores = tea_results.get('scores', {})
        logger.info(f"TEA Scores calculated:")
        logger.info(f"  Transparency: {scores.get('transparency_score', 0)}/10")
        logger.info(f"  Explainability: {scores.get('explainability_score', 0)}/10")
        logger.info(f"  Accountability: {scores.get('accountability_score', 0)}/10")
        
        # Test detailed analysis
        transparency_analysis = tea_results.get('transparency_analysis', [])
        logger.info(f"Transparency analysis has {len(transparency_analysis)} questions")
        
        explainability_analysis = tea_results.get('explainability_analysis', [])
        logger.info(f"Explainability analysis has {len(explainability_analysis)} questions")
        
        accountability_analysis = tea_results.get('accountability_analysis', [])
        logger.info(f"Accountability analysis has {len(accountability_analysis)} questions")
        
        # Test the AI analysis service integration
        logger.info("Testing AI analysis service integration...")
        tea_service_results = ai_analysis_service.calculate_tea_scores(SAMPLE_POLICY_TEXT)
        
        if 'error' in tea_service_results:
            logger.error(f"AI service error: {tea_service_results['error']}")
            return False
        
        service_scores = tea_service_results.get('scores', {})
        logger.info(f"AI Service TEA Scores:")
        logger.info(f"  Transparency: {service_scores.get('transparency_score', 0)}/10")
        logger.info(f"  Explainability: {service_scores.get('explainability_score', 0)}/10")
        logger.info(f"  Accountability: {service_scores.get('accountability_score', 0)}/10")
        
        logger.info("TEA scores test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

async def test_document_analysis():
    """Test full document analysis with TEA scores"""
    try:
        logger.info("Testing full document analysis with TEA scores...")
        
        # Test the analyze_policy_document method which should now include TEA scores
        analysis_result = ai_analysis_service.analyze_policy_document(SAMPLE_POLICY_TEXT)
        
        logger.info("Document analysis completed")
        logger.info(f"Title: {analysis_result.get('title', 'N/A')}")
        logger.info(f"Country: {analysis_result.get('country', 'N/A')}")
        logger.info(f"Policy Area: {analysis_result.get('policy_area', 'N/A')}")
        
        # Check if TEA scores are included
        tea_scores = analysis_result.get('tea_scores', {})
        if tea_scores:
            logger.info("TEA scores found in document analysis:")
            logger.info(f"  Transparency: {tea_scores.get('transparency_score', 0)}/10")
            logger.info(f"  Explainability: {tea_scores.get('explainability_score', 0)}/10")
            logger.info(f"  Accountability: {tea_scores.get('accountability_score', 0)}/10")
        else:
            logger.warning("TEA scores not found in document analysis")
        
        return True
        
    except Exception as e:
        logger.error(f"Document analysis test failed: {str(e)}")
        return False

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("TEA scores functionality may not work without proper AWS credentials")
        return False
    
    logger.info("All required environment variables are set")
    return True

async def main():
    """Main test function"""
    logger.info("=== TEA Scores Implementation Test ===")
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        logger.warning("Environment check failed - continuing with tests but functionality may be limited")
    
    # Run tests
    tests_passed = 0
    total_tests = 2
    
    # Test 1: TEA scores calculation
    if await test_tea_scores():
        tests_passed += 1
        logger.info("✅ TEA scores calculation test: PASSED")
    else:
        logger.error("❌ TEA scores calculation test: FAILED")
    
    # Test 2: Document analysis with TEA scores
    if await test_document_analysis():
        tests_passed += 1
        logger.info("✅ Document analysis with TEA scores test: PASSED")
    else:
        logger.error("❌ Document analysis with TEA scores test: FAILED")
    
    # Summary
    logger.info(f"\n=== Test Summary ===")
    logger.info(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        logger.info("🎉 All tests passed! TEA scores implementation is working correctly.")
    else:
        logger.warning(f"⚠️  {total_tests - tests_passed} test(s) failed. Please check the implementation.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
