"""
Test script for AI Analysis Service
Run this to test the document analysis functionality
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from services.ai_analysis_service import ai_analysis_service

def test_text_analysis():
    """Test AI analysis with sample policy text"""
    
    sample_policy_text = """
    RESPONSIBLE AI STRATEGY 2024-01
    
    Executive Summary
    This Responsible AI Strategy aims to ensure ethical AI deployment across government agencies by prioritizing transparency, accountability, and human oversight. The policy establishes comprehensive guidelines for AI development, deployment, and evaluation.
    
    Policy Objectives:
    - Ensure transparent AI decision-making processes
    - Maintain human control over critical AI systems
    - Protect privacy and individual rights
    - Foster public trust in AI technologies
    
    Target Stakeholders:
    This policy applies to government agencies, industry partners, academic institutions, and research organizations involved in AI development and deployment.
    
    Budget and Implementation:
    The total budget allocated for this initiative is $5,000,000 USD annually. The policy will be implemented starting January 2024, with private sector partnerships contributing additional funding.
    
    Evaluation Framework:
    The policy will undergo both internal and external evaluation. A comprehensive risk assessment has been conducted. Public consultation was held from March 1, 2023, to May 15, 2023, with all comments made publicly available.
    
    AI Principles:
    This policy aligns with core AI principles including transparency, accountability, privacy, ethics, and human rights. Environmental considerations and international cooperation are integral components.
    """
    
    try:
        print("Testing AI Analysis Service...")
        print("-" * 50)
        
        # Analyze the sample text
        result = ai_analysis_service.analyze_policy_document(sample_policy_text)
        
        print("Analysis successful!")
        print(f"Policy Name: {result.get('policyName', 'Not found')}")
        print(f"Policy ID: {result.get('policyId', 'Not found')}")
        print(f"Budget: {result.get('implementation', {}).get('yearlyBudget', 'Not found')} {result.get('implementation', {}).get('budgetCurrency', 'USD')}")
        print(f"Target Groups: {', '.join(result.get('targetGroups', []))}")
        print(f"AI Principles: {', '.join(result.get('alignment', {}).get('aiPrinciples', []))}")
        print(f"Transparency Score: {result.get('evaluation', {}).get('transparencyScore', 0)}/10")
        
        print("\nFull result:")
        import json
        print(json.dumps(result, indent=2))
        
        return True
        
    except Exception as e:
        print(f"Analysis failed: {str(e)}")
        return False

def check_environment():
    """Check if environment is properly configured"""
    print("Checking environment configuration...")
    print("-" * 50)
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key:
        print("❌ GROQ_API_KEY not found in environment variables")
        print("Please set your Groq API key in the .env file")
        return False
    else:
        print(f"✅ GROQ_API_KEY found (length: {len(groq_key)})")
        return True

if __name__ == "__main__":
    print("AI Analysis Service Test")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\nPlease configure your .env file with GROQ_API_KEY and try again.")
        sys.exit(1)
    
    # Test the analysis
    success = test_text_analysis()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("The AI auto-fill feature is ready to use.")
    else:
        print("\n❌ Test failed. Please check your configuration.")
