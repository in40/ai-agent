#!/usr/bin/env python3
"""
Test script for the processed document import functionality
"""
import requests
import json
import os

# Configuration
GATEWAY_URL = os.getenv('GATEWAY_URL', 'http://localhost:5000')
TEST_AUTH_TOKEN = os.getenv('TEST_AUTH_TOKEN', 'your-test-token-here')

def test_processed_import():
    """Test the processed document import functionality"""
    
    # Path to the sample processed document
    sample_file_path = '/root/qwen/ai_agent/imports/GOST_R_52633.3-2011.json'
    
    # Check if the file exists
    if not os.path.exists(sample_file_path):
        print(f"Sample file not found: {sample_file_path}")
        return False
    
    # Prepare the request
    url = f"{GATEWAY_URL}/api/rag/import_processed"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {TEST_AUTH_TOKEN}'
    }
    
    # Open and send the file
    with open(sample_file_path, 'rb') as f:
        files = {'file': ('GOST_R_52633.3-2011.json', f, 'application/json')}
        
        print("Sending request to import processed document...")
        response = requests.post(url, files=files, headers=headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        print("✅ Processed document import test PASSED")
        return True
    else:
        print("❌ Processed document import test FAILED")
        return False

def test_invalid_file():
    """Test importing an invalid file type"""
    
    # Create a temporary invalid file
    with open('/tmp/invalid_file.txt', 'w') as f:
        f.write("This is not a JSON file")
    
    # Prepare the request
    url = f"{GATEWAY_URL}/api/rag/import_processed"
    
    # Headers
    headers = {
        'Authorization': f'Bearer {TEST_AUTH_TOKEN}'
    }
    
    # Open and send the file
    with open('/tmp/invalid_file.txt', 'rb') as f:
        files = {'file': ('invalid_file.txt', f, 'text/plain')}
        
        print("\nSending request to import invalid file type...")
        response = requests.post(url, files=files, headers=headers)
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 400:
        print("✅ Invalid file type test PASSED (correctly rejected)")
        return True
    else:
        print("❌ Invalid file type test FAILED (should have been rejected)")
        return False

if __name__ == "__main__":
    print("Testing processed document import functionality...\n")
    
    success1 = test_processed_import()
    success2 = test_invalid_file()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")