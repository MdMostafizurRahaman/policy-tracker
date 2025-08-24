import requests
import json

def test_tea_scores():
    """Test TEA scores calculation with a sample document"""
    
    # Sample policy text for testing
    sample_text = """
    AI Safety Evaluation Guidelines
    
    1. Transparency Requirements:
    - All AI systems must provide clear documentation
    - Decision-making processes must be publicly accessible
    - Regular reporting on system performance is required
    
    2. Explainability Standards:
    - AI outputs must be interpretable by users
    - Explanations must be provided for all decisions
    - Technical documentation must be available
    
    3. Accountability Framework:
    - Clear responsibility assignment for AI decisions
    - Audit mechanisms must be in place
    - Redress procedures for affected individuals
    """
    
    # Save as test file
    with open('test_policy_sample.txt', 'w', encoding='utf-8') as f:
        f.write(sample_text)
    
    # Test API endpoint
    url = "http://localhost:8000/api/ai-analysis/calculate-tea-scores"
    
    try:
        with open('test_policy_sample.txt', 'rb') as f:
            files = {'file': ('test_policy_sample.txt', f, 'text/plain')}
            response = requests.post(url, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ TEA Scores calculated successfully!")
            print(f"📊 Transparency: {result.get('tea_scores', {}).get('transparency_score', 'N/A')}")
            print(f"📊 Explainability: {result.get('tea_scores', {}).get('explainability_score', 'N/A')}")
            print(f"📊 Accountability: {result.get('tea_scores', {}).get('accountability_score', 'N/A')}")
            print(f"🤖 Analysis method: {result.get('tea_analysis', {}).get('analysis_method', 'N/A')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing TEA scores: {str(e)}")

if __name__ == "__main__":
    test_tea_scores()
