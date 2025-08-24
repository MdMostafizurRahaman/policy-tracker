#!/usr/bin/env python3
"""
Test script to check which Claude models are accessible
"""
import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bedrock_models():
    """Test which Bedrock Claude models are accessible"""
    
    # Initialize Bedrock client
    bedrock_client = boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    # Models to test (updated list with inference profiles)
    models_to_test = [
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet inference profile
        "us.anthropic.claude-3-5-haiku-20241022-v1:0",   # Claude 3.5 Haiku inference profile
        "anthropic.claude-3-sonnet-20240229-v1:0",       # Claude 3 Sonnet
        "anthropic.claude-3-haiku-20240307-v1:0",        # Claude 3 Haiku
    ]
    
    simple_prompt = "What is 2+2? Answer briefly."
    
    for model_id in models_to_test:
        try:
            print(f"\n🧪 Testing model: {model_id}")
            
            # Claude 3+ models use different message format
            if "claude-3" in model_id or "claude-3-5" in model_id:
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 100,
                    "messages": [
                        {"role": "user", "content": simple_prompt}
                    ]
                }
            else:
                # Claude v2 and instant use older format
                request_body = {
                    "prompt": f"\n\nHuman: {simple_prompt}\n\nAssistant:",
                    "max_tokens_to_sample": 100
                }
            
            response = bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract response text
            if "claude-3" in model_id or "claude-3-5" in model_id:
                answer = response_body.get('content', [{}])[0].get('text', 'No response')
            else:
                answer = response_body.get('completion', 'No response')
            
            print(f"✅ SUCCESS: {model_id}")
            print(f"   Response: {answer.strip()}")
            break  # Stop at first working model
            
        except Exception as e:
            print(f"❌ FAILED: {model_id}")
            print(f"   Error: {str(e)}")
    
    print("\n" + "="*50)
    print("Model testing completed!")

if __name__ == "__main__":
    test_bedrock_models()
