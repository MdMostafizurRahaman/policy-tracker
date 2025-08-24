"""
Simple utility script to test TEA scores with a sample document
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def main():
    """Quick test of TEA scores functionality"""
    try:
        from services.bedrock_service import bedrock_service
        
        # Sample short policy text for quick testing
        sample_text = """
        AI Transparency Policy
        
        This policy document is publicly available. All stakeholders were consulted during development.
        AI systems must provide clear explanations to users. Decision-making processes are documented.
        Oversight mechanisms are in place with clear accountability structures.
        """
        
        print("Testing TEA Scores with sample text...")
        print("=" * 50)
        
        # Calculate scores
        result = bedrock_service.calculate_transparency_explainability_accountability_scores(sample_text)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            print("\nTroubleshooting tips:")
            print("1. Check your AWS credentials in .env file")
            print("2. Ensure AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION are set")
            print("3. Verify Bedrock access permissions in your AWS account")
            print("4. Make sure Claude 3 Haiku model is available in your region")
            return False
        
        # Display results
        scores = result.get('scores', {})
        print("✅ TEA Scores calculated successfully!")
        print(f"📊 Transparency Score: {scores.get('transparency_score', 0)}/10")
        print(f"📊 Explainability Score: {scores.get('explainability_score', 0)}/10")
        print(f"📊 Accountability Score: {scores.get('accountability_score', 0)}/10")
        
        print(f"\n📝 Analysis Summary:")
        print(f"   - Transparency questions analyzed: {len(result.get('transparency_analysis', []))}")
        print(f"   - Explainability questions analyzed: {len(result.get('explainability_analysis', []))}")
        print(f"   - Accountability questions analyzed: {len(result.get('accountability_analysis', []))}")
        
        print("\n🎉 TEA Scores implementation is working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded from .env file")
    except ImportError:
        print("Warning: python-dotenv not installed, using system environment variables")
    
    # Check required environment variables
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or system environment")
        sys.exit(1)
    
    # Run test
    success = main()
    sys.exit(0 if success else 1)
