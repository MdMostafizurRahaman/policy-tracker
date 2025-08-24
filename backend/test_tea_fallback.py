"""
Simple test without requiring AWS Bedrock - uses keyword-based fallback
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

def test_keyword_based_analysis():
    """Test TEA scores with keyword-based fallback analysis"""
    try:
        # Create a mock bedrock service that always uses fallback
        class MockBedrockService:
            def calculate_transparency_explainability_accountability_scores(self, document_text: str):
                # Import the actual fallback methods
                from services.bedrock_service import BedrockService
                bedrock = BedrockService()
                
                # Create a mock prompt to trigger fallback
                prompt = f"""
DOCUMENT TEXT:
{document_text}

Please carefully read the document...
"""
                return bedrock._fallback_analysis(prompt)
        
        mock_service = MockBedrockService()
        
        # Test with a policy document that contains relevant keywords
        sample_text = """
        AI Transparency and Accountability Policy
        
        This policy document is publicly accessible and available to all stakeholders.
        During development, extensive public consultation was conducted with feedback
        from various stakeholder groups. The policy provides open data reporting
        on implementation progress and discloses decision-making criteria.
        
        All AI systems must provide human-interpretable outputs with clear explanations
        tailored to different audiences. Decision-making processes are thoroughly 
        documented, and users are informed about how AI decisions are made.
        The policy includes comprehensive guidance for explainability in deployment.
        
        Clear responsibility is assigned for AI decisions and potential harm.
        Robust auditing and oversight mechanisms are in place. Individuals can
        seek redress and appeal AI decisions through established procedures.
        Liability for misuse or errors is clearly outlined, and a dedicated
        regulatory body has been identified to govern implementation.
        """
        
        print("Testing TEA Scores with keyword-based analysis...")
        print("=" * 60)
        
        # Calculate scores using keyword-based fallback
        result = mock_service.calculate_transparency_explainability_accountability_scores(sample_text)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        # Display results
        scores = result.get('scores', {})
        print("✅ TEA Scores calculated successfully using keyword analysis!")
        print(f"📊 Transparency Score: {scores.get('transparency_score', 0)}/10")
        print(f"📊 Explainability Score: {scores.get('explainability_score', 0)}/10") 
        print(f"📊 Accountability Score: {scores.get('accountability_score', 0)}/10")
        
        # Show which method was used
        if result.get('fallback_used'):
            print(f"\n🔄 Analysis Method: Keyword-based fallback (Bedrock not available)")
        else:
            print(f"\n🤖 Analysis Method: AWS Bedrock")
        
        print(f"\n📝 Analysis Summary:")
        print(f"   - Transparency questions analyzed: {len(result.get('transparency_analysis', []))}")
        print(f"   - Explainability questions analyzed: {len(result.get('explainability_analysis', []))}")
        print(f"   - Accountability questions analyzed: {len(result.get('accountability_analysis', []))}")
        
        # Show sample analysis details
        if result.get('transparency_analysis'):
            print(f"\n📋 Sample Analysis (Transparency):")
            for i, analysis in enumerate(result['transparency_analysis'][:2]):
                print(f"   Q{i+1}: {analysis['question']}")
                print(f"       Answer: {analysis['answer']} (Score: {analysis['score']}/2)")
                print(f"       Justification: {analysis['justification']}")
        
        print("\n🎉 TEA Scores implementation is working!")
        print("💡 To use AWS Bedrock instead of keyword analysis:")
        print("   1. Set up AWS credentials in .env file")
        print("   2. Enable Claude models in AWS Bedrock console")
        print("   3. Ensure proper IAM permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_keyword_based_analysis()
    sys.exit(0 if success else 1)
