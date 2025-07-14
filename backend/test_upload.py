#!/usr/bin/env python3
"""
Quick test script to verify AWS S3 file upload functionality
"""
import requests
import os

def test_file_upload():
    """Test the file upload endpoint"""
    url = "http://localhost:8000/api/upload-policy-file"
    
    # Create a test file
    test_content = "This is a test policy document for AWS S3 upload verification."
    test_file_path = "test_policy_document.txt"
    
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    try:
        # Upload the file
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_policy_document.txt', f, 'text/plain')}
            headers = {'Authorization': 'Bearer test-token'}
            
            print("Uploading test file to AWS S3...")
            response = requests.post(url, files=files, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ File upload successful!")
                result = response.json()
                print(f"File URL: {result.get('file_url', 'N/A')}")
                print(f"File Key: {result.get('file_key', 'N/A')}")
            else:
                print("❌ File upload failed!")
                
    except Exception as e:
        print(f"❌ Error during upload: {e}")
    
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    test_file_upload()
