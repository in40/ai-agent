#!/usr/bin/env python3
"""
Proper test for the download functionality
"""
import requests
import json
from urllib.parse import quote

def get_token():
    """Get a valid authentication token"""
    # Try to login with an existing user
    users_to_try = [
        ('admin', 'password123'),
        ('admin', 'admin'),
        ('admin', ''),
        ('second_user', 'password123'),
        ('persistent_user', 'password123'),
        ('40in', 'password123'),
        ('testuser', 'password123'),
        ('newuser', 'password123'),
        ('testuser2', 'password123')
    ]
    
    for username, password in users_to_try:
        try:
            response = requests.post(
                "http://localhost:5001/login",
                json={'username': username, 'password': password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    print(f"✓ Got token for user: {username}")
                    return token
        except Exception:
            continue
    
    # If no existing user worked, try to register a new one
    try:
        register_resp = requests.post(
            "http://localhost:5001/register",
            json={'username': 'test_download', 'password': 'password123'},
            timeout=10
        )
        if register_resp.status_code in [200, 201, 400]:  # 400 might mean user exists
            login_resp = requests.post(
                "http://localhost:5001/login",
                json={'username': 'test_download', 'password': 'password123'},
                timeout=10
            )
            if login_resp.status_code == 200:
                data = login_resp.json()
                token = data.get('token')
                if token:
                    print("✓ Got token for test_download user")
                    return token
    except Exception as e:
        print(f"Registration/login failed: {e}")
    
    return None

def test_download_scenario():
    """Test the exact download scenario that's failing"""
    print("=== Testing download scenario ===")
    
    # Get authentication token
    token = get_token()
    if not token:
        print("✗ Could not get authentication token")
        return False
    
    print(f"Token: {token[:20]}...")
    
    # Headers with the token
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # The exact file from the user's example
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    filename = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"  # This is the sanitized version that would be in URL
    encoded_filename = quote(filename)
    
    print(f"Testing file ID: {file_id}")
    print(f"Testing filename: {filename}")
    
    # Test 1: Direct RAG service access
    print("\n1. Testing direct RAG service access...")
    rag_url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    print(f"RAG URL: {rag_url}")
    
    try:
        rag_response = requests.get(rag_url, headers=headers, timeout=30)
        print(f"RAG Response Status: {rag_response.status_code}")
        print(f"RAG Response: {rag_response.text}")
        
        if rag_response.status_code == 200:
            print("✓ Direct RAG download successful!")
            return True
        elif "Token is missing!" in rag_response.text:
            print("✗ Direct RAG: Token is missing!")
        elif "File not found" in rag_response.text:
            print("✗ Direct RAG: File not found")
        else:
            print(f"? Direct RAG: Other issue - {rag_response.text}")
    except Exception as e:
        print(f"✗ Direct RAG: Request failed - {e}")
    
    # Test 2: Gateway access
    print("\n2. Testing gateway access...")
    gateway_url = f"http://localhost:5000/download/{file_id}/{encoded_filename}"
    print(f"Gateway URL: {gateway_url}")
    
    try:
        gw_response = requests.get(gateway_url, headers=headers, timeout=30)
        print(f"Gateway Response Status: {gw_response.status_code}")
        print(f"Gateway Response: {gw_response.text}")
        
        if gw_response.status_code == 200:
            print("✓ Gateway download successful!")
            return True
        elif "Token is missing!" in gw_response.text:
            print("✗ Gateway: Token is missing!")
        elif "File not found" in gw_response.text:
            print("✗ Gateway: File not found")
        else:
            print(f"? Gateway: Other issue - {gw_response.text}")
    except Exception as e:
        print(f"✗ Gateway: Request failed - {e}")
    
    # Test 3: Check if file exists locally
    print("\n3. Checking if file exists locally...")
    import os
    file_path = f"/root/qwen_test/ai_agent/data/rag_uploaded_files/{file_id}/{filename}"
    original_file_path = f"/root/qwen_test/ai_agent/data/rag_uploaded_files/{file_id}/ГОСТ Р ИСО МЭК 27001-2021.pdf"
    
    print(f"Checking path with underscores: {file_path} -> {os.path.exists(file_path)}")
    print(f"Checking path with spaces: {original_file_path} -> {os.path.exists(original_file_path)}")
    
    # List files in the directory
    dir_path = f"/root/qwen_test/ai_agent/data/rag_uploaded_files/{file_id}/"
    if os.path.exists(dir_path):
        files = os.listdir(dir_path)
        print(f"Files in directory: {files}")
    
    return False

if __name__ == "__main__":
    success = test_download_scenario()
    if success:
        print("\n✓ Download test PASSED")
    else:
        print("\n✗ Download test FAILED")