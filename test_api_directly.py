#!/usr/bin/env python3
"""
Test script to call the API directly and troubleshoot the RAG issue.
"""

import requests
import json
import os

# Get the backend URL from environment or use default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://192.168.51.216:5000')

def register_user():
    """Register a new user to get access to the API."""
    register_url = f"{BACKEND_URL}/auth/register"
    register_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    print(f"Registering user at {register_url}")
    response = requests.post(register_url, json=register_data)
    
    if response.status_code == 201:
        print("✓ User registered successfully")
        return True
    elif response.status_code == 400 and "already exists" in response.json().get('message', ''):
        print("✓ User already exists, continuing...")
        return True
    else:
        print(f"✗ Registration failed: {response.status_code} - {response.text}")
        return False

def login_user():
    """Login the user to get an authentication token."""
    login_url = f"{BACKEND_URL}/auth/login"
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    print(f"Logging in at {login_url}")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code == 200:
        token = response.json().get('token')
        print("✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def call_agent_api(token, user_request):
    """Call the agent API with the given token and request."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    api_url = f"{BACKEND_URL}/api/agent/query"
    payload = {
        "user_request": user_request
    }

    print(f"Calling agent API at {api_url}")
    print(f"Request: {user_request}")

    response = requests.post(api_url, headers=headers, json=payload)

    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✓ API call successful")
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"✗ API call failed: {response.status_code} - {response.text}")
        # Try to login again if token is invalid
        if response.status_code == 401:
            print("Token may have expired, trying to get a new one...")
            new_token = login_user()
            if new_token:
                print(f"Got new token: {new_token[:20]}...")
                headers['Authorization'] = f'Bearer {new_token}'
                response = requests.post(api_url, headers=headers, json=payload)
                print(f"Retry response status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print("✓ API call successful on retry")
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return result
                else:
                    print(f"✗ Retry also failed: {response.status_code} - {response.text}")
        return None

def main():
    print("Testing API call directly to troubleshoot RAG issue...")
    
    # Register user
    if not register_user():
        print("Failed to register user, exiting...")
        return
    
    # Login user to get token
    token = login_user()
    if not token:
        print("Failed to get token, exiting...")
        return
    
    print(f"Got token: {token[:20]}...")
    
    # Call the agent API with the problematic request
    user_request = "look into local documents, what is current price for URALS"
    result = call_agent_api(token, user_request)
    
    if result:
        print("\nAPI call completed. Checking for RAG-related errors...")
        final_response = result.get('final_response', '')
        if 'Error generating response using RAG' in final_response:
            print("❌ RAG error still present in response")
        else:
            print("✅ No RAG error in response")
    else:
        print("❌ API call failed")

if __name__ == "__main__":
    main()