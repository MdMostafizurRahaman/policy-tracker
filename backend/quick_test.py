import requests

sample_text = "AI Safety Guidelines: All systems must provide transparency, explainability, and accountability."

with open('test_simple.txt', 'w') as f:
    f.write(sample_text)

try:
    with open('test_simple.txt', 'rb') as f:
        files = {'file': ('test_simple.txt', f, 'text/plain')}
        response = requests.post('http://localhost:8000/api/ai-analysis/calculate-tea-scores', files=files)

    if response.status_code == 200:
        result = response.json()
        print('✅ SUCCESS!')
        scores = result.get('tea_scores', {})
        print(f'T: {scores.get("transparency_score", 0)}')
        print(f'E: {scores.get("explainability_score", 0)}')
        print(f'A: {scores.get("accountability_score", 0)}')
        method = result.get('tea_analysis', {}).get('analysis_method', 'N/A')
        print(f'Method: {method}')
    else:
        print(f'❌ Error: {response.status_code}')
        print(response.text)
except Exception as e:
    print(f'Error: {e}')
