"""
Test the TEA scores API endpoint
"""
import requests
import json

def test_tea_scores_api():
    # Backend server URL
    base_url = "http://localhost:8000/api"
    
    # Test data - sample policy text
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
    
    # Create a temporary text file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_file_path = f.name
    
    try:
        # Test the calculate-tea-scores endpoint
        print("Testing TEA scores calculation endpoint...")
        
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('test_policy.txt', f, 'text/plain')}
            
            response = requests.post(
                f"{base_url}/ai-analysis/calculate-tea-scores",
                files=files,
                timeout=30
            )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ TEA scores calculation successful!")
            print(f"📊 Transparency Score: {data.get('scores', {}).get('transparency_score', 0)}/10")
            print(f"📊 Explainability Score: {data.get('scores', {}).get('explainability_score', 0)}/10")
            print(f"📊 Accountability Score: {data.get('scores', {}).get('accountability_score', 0)}/10")
            print(f"🔧 Analysis Method: {data.get('metadata', {}).get('analysis_method', 'unknown')}")
            
            # Show sample detailed analysis
            if data.get('detailed_analysis', {}).get('transparency_analysis'):
                print("\n📋 Sample Transparency Analysis:")
                for i, item in enumerate(data['detailed_analysis']['transparency_analysis'][:2]):
                    print(f"   Q{i+1}: {item['question']}")
                    print(f"       Answer: {item['answer']} (Score: {item['score']}/2)")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

if __name__ == "__main__":
    success = test_tea_scores_api()
    if success:
        print("\n🎉 TEA scores API is working correctly!")
        print("💡 You can now upload documents in the frontend to get automatic TEA scores.")
    else:
        print("\n❌ TEA scores API test failed.")
        print("🔧 Check if the backend server is running and accessible.")
