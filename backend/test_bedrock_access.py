#!/usr/bin/env python3
"""
Test AWS Bedrock access and permissions
"""
import boto3
import json
from botocore.exceptions import ClientError, NoCredentialsError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_bedrock_access():
    """Test Bedrock access with current credentials"""
    
    print("🔍 Testing AWS Bedrock Access...")
    print(f"Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    
    try:
        # Initialize Bedrock client
        bedrock = boto3.client(
            'bedrock',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        print("✅ Bedrock client created successfully")
        
        # List available foundation models
        print("\n📋 Listing available foundation models...")
        response = bedrock.list_foundation_models()
        
        claude_models = []
        all_models = []
        
        for model in response.get('modelSummaries', []):
            model_id = model['modelId']
            all_models.append(model_id)
            
            if 'claude' in model_id.lower():
                claude_models.append(model_id)
                print(f"🤖 Found Claude model: {model_id}")
        
        print(f"\n📊 Total models available: {len(all_models)}")
        print(f"🎯 Claude models available: {len(claude_models)}")
        
        if not claude_models:
            print("❌ No Claude models found!")
            print("💡 This means you need to request model access in AWS Bedrock console")
            return False
        
        # Initialize bedrock runtime client for model invocation
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Test model invocation with multiple models
        test_models = [
            "anthropic.claude-instant-v1",
            "anthropic.claude-v2",
            "anthropic.claude-v2:1",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0"
        ]
        
        for model_id in test_models:
            if model_id in claude_models:
                print(f"\n🧪 Testing model invocation with: {model_id}")
                
                try:
                    # Simple test prompt
                    test_prompt = "Hello, can you respond with just 'Test successful'?"
                    
                    if 'claude-3' in model_id:
                        # Claude 3 format
                        body = json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 100,
                            "messages": [{"role": "user", "content": test_prompt}]
                        })
                    else:
                        # Claude 2/Instant format
                        body = json.dumps({
                            "prompt": f"\n\nHuman: {test_prompt}\n\nAssistant:",
                            "max_tokens_to_sample": 100
                        })
                    
                    response = bedrock_runtime.invoke_model(
                        modelId=model_id,
                        body=body,
                        contentType='application/json'
                    )
                    
                    response_body = json.loads(response['body'].read())
                    print(f"✅ Model {model_id} invocation successful!")
                    print(f"📝 Response: {response_body}")
                    return True
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    print(f"❌ Model {model_id} failed: {error_code}")
                    continue
                except Exception as e:
                    print(f"❌ Model {model_id} error: {str(e)}")
                    continue
        
        print("❌ All test models failed!")
        return False
        
    except NoCredentialsError:
        print("❌ AWS credentials not found or invalid")
        print("💡 Check your .env file or AWS configuration")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS API Error: {error_code}")
        print(f"📝 Message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            print("💡 This means your IAM permissions are incorrect")
        elif error_code == 'ValidationException':
            print("💡 This might mean the model is not available in your region")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bedrock_access()
    
    if not success:
        print("\n🛠️  How to fix:")
        print("1. Go to AWS Bedrock console")
        print("2. Navigate to 'Model access' section")
        print("3. Request access for Claude models")
        print("4. Wait for approval (can take hours/days)")
        print("5. Make sure your IAM user has bedrock:* permissions")
        print("6. Verify you're using the correct AWS region")
