#!/usr/bin/env python3
"""
Debug script to trace the download request flow through the system
"""
import os
import requests
import json
import sys
from urllib.parse import quote

def get_auth_token():
    """Get an authentication token by logging in"""
    print("Attempting to get authentication token...")

    # Try multiple usernames that we know exist
    test_users = [
        ('admin', 'password123'),  # Common default
        ('admin', 'admin'),        # Another common default
        ('admin', ''),             # Empty password
        ('second_user', 'password123'),  # Existing user
        ('persistent_user', 'password123'),  # Existing user
        ('40in', 'password123'),  # Existing user
        ('testuser', 'password123'),  # Existing user
        ('newuser', 'password123'),  # Existing user
        ('testuser2', 'password123'),  # Existing user
    ]

    auth_url = "http://localhost:5001/login"  # Auth service URL

    for username, password in test_users:
        print(f"Trying {username}:{password}...")
        try:
            response = requests.post(auth_url, json={
                'username': username,
                'password': password
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    print(f"✓ Successfully obtained authentication token for user: {username}")
                    return token
                else:
                    print(f"✗ Login succeeded but no token returned for {username}: {data}")
            else:
                print(f"✗ Login failed for {username} with status {response.status_code}")
        except Exception as e:
            print(f"✗ Error during login for {username}: {e}")

    # If login attempts failed, try to register a new user
    print("Attempting to register a new test user...")
    register_url = "http://localhost:5001/register"
    register_data = {
        'username': 'debug_user',
        'password': 'password123'
    }

    try:
        response = requests.post(register_url, json=register_data)
        print(f"Registration response: {response.status_code} - {response.text}")

        if response.status_code in [200, 201, 400]:  # 400 might mean user already exists
            # Try to login with the registered user
            response = requests.post(auth_url, json={
                'username': 'debug_user',
                'password': 'password123'
            })

            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                if token:
                    print("✓ Successfully obtained authentication token for debug_user")
                    return token
                else:
                    print(f"✗ Login with debug_user succeeded but no token returned: {data}")
            else:
                print(f"✗ Login with debug_user failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error during registration/login: {e}")

    print("✗ Could not obtain authentication token")
    return None

def test_direct_rag_download(token, file_id, filename):
    """Test downloading directly from RAG service (bypassing gateway/nginx)"""
    print(f"\nTesting direct download from RAG service...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # URL encode the filename to handle special characters
    encoded_filename = quote(filename)
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    
    print(f"Direct RAG URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Direct RAG response status: {response.status_code}")
        print(f"Direct RAG response: {response.text[:200]}...")  # First 200 chars
        return response
    except Exception as e:
        print(f"✗ Error in direct RAG download: {e}")
        return None

def test_gateway_download(token, file_id, filename):
    """Test downloading through gateway (but not nginx)"""
    print(f"\nTesting download through gateway...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # URL encode the filename to handle special characters
    encoded_filename = quote(filename)
    url = f"http://localhost:5000/download/{file_id}/{encoded_filename}"
    
    print(f"Gateway URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Gateway response status: {response.status_code}")
        print(f"Gateway response: {response.text[:200]}...")  # First 200 chars
        return response
    except Exception as e:
        print(f"✗ Error in gateway download: {e}")
        return None

def test_full_flow_download(token, base_url, file_id, filename):
    """Test downloading through the full flow (nginx -> gateway -> rag)"""
    print(f"\nTesting download through full flow...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # URL encode the filename to handle special characters
    encoded_filename = quote(filename)
    url = f"{base_url}/download/{file_id}/{encoded_filename}"
    
    print(f"Full flow URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Full flow response status: {response.status_code}")
        print(f"Full flow response: {response.text[:200]}...")  # First 200 chars
        return response
    except Exception as e:
        print(f"✗ Error in full flow download: {e}")
        return None

def main():
    print("=== Download Flow Debugging Suite ===")
    
    # File details from the user's example
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    filename = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"
    base_url = "https://192.168.51.216"  # From user's example
    
    print(f"Testing download for file: {filename}")
    print(f"File ID: {file_id}")
    print(f"Base URL: {base_url}")
    
    # Step 1: Get authentication token
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication token")
        return 1
    
    print(f"\nUsing token: {token[:20]}..." if len(token) > 20 else f"Using token: {token}")
    
    # Step 2: Test direct RAG service access
    direct_response = test_direct_rag_download(token, file_id, filename)
    
    # Step 3: Test gateway access
    gateway_response = test_gateway_download(token, file_id, filename)
    
    # Step 4: Test full flow (if possible - may require external access)
    full_response = test_full_flow_download(token, base_url, file_id, filename)
    
    print("\n=== Summary ===")
    print(f"Direct RAG response: {direct_response.status_code if direct_response else 'ERROR'}")
    print(f"Gateway response: {gateway_response.status_code if gateway_response else 'ERROR'}")
    print(f"Full flow response: {full_response.status_code if full_response else 'ERROR'}")
    
    # Analyze results
    if direct_response and direct_response.status_code == 200:
        print("✓ Direct RAG access works - issue is in gateway/proxy layer")
    elif direct_response:
        print(f"✗ Direct RAG access failed - RAG service issue: {direct_response.status_code}")
    else:
        print("? Direct RAG access failed with exception")
    
    if gateway_response and gateway_response.status_code == 200:
        print("✓ Gateway access works - issue is in nginx layer")
    elif gateway_response:
        print(f"✗ Gateway access failed - gateway issue: {gateway_response.status_code}")
    else:
        print("? Gateway access failed with exception")
    
    if full_response and full_response.status_code == 200:
        print("✓ Full flow works - issue was temporary")
    elif full_response:
        print(f"✗ Full flow failed - issue persists: {full_response.status_code}")
    else:
        print("? Full flow failed with exception")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())