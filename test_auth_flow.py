#!/usr/bin/env python3
"""
Test script to specifically check if authentication is working properly in the download flow
"""
import os
import requests
import json
from urllib.parse import quote

def test_auth_with_bad_token():
    """Test download with a deliberately bad token"""
    print("Testing download with bad token...")
    
    headers = {
        'Authorization': 'Bearer this_is_a_bad_token'
    }
    
    # Use a fake file ID and name
    file_id = "fake-id-123"
    filename = "fake_file.pdf"
    encoded_filename = quote(filename)
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Token is missing!" in response.text or response.status_code == 401:
            print("✓ Authentication is properly enforced - bad token rejected")
        else:
            print("? Unexpected response for bad token")
    except Exception as e:
        print(f"Error with bad token test: {e}")

def test_auth_without_token():
    """Test download without any token"""
    print("\nTesting download without token...")
    
    headers = {}  # No Authorization header
    
    # Use a fake file ID and name
    file_id = "fake-id-123"
    filename = "fake_file.pdf"
    encoded_filename = quote(filename)
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Token is missing!" in response.text or response.status_code == 401:
            print("✓ Authentication is properly enforced - missing token detected")
        else:
            print("? Unexpected response for missing token")
    except Exception as e:
        print(f"Error with no token test: {e}")

def test_auth_with_good_token_but_fake_file():
    """Test download with good token but non-existent file"""
    print("\nTesting download with good token but fake file...")
    
    # First, get a valid token
    auth_response = requests.post("http://localhost:5001/login", json={
        'username': 'debug_user',
        'password': 'password123'
    })
    
    if auth_response.status_code == 200:
        token = auth_response.json()['token']
        print(f"Got valid token: {token[:20]}...")
    else:
        print("Could not get valid token")
        return
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Use a fake file ID and name
    file_id = "totally-fake-id-456"
    filename = "nonexistent_file.pdf"
    encoded_filename = quote(filename)
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Token is missing!" in response.text or response.status_code == 401:
            print("✗ Token was rejected - authentication issue exists")
        elif "File not found" in response.text or response.status_code == 404:
            print("✓ Token accepted, file not found - authentication working correctly")
        else:
            print("? Unexpected response")
    except Exception as e:
        print(f"Error with good token test: {e}")

def test_gateway_auth_with_good_token_but_fake_file():
    """Test download through gateway with good token but non-existent file"""
    print("\nTesting download through gateway with good token but fake file...")
    
    # First, get a valid token
    auth_response = requests.post("http://localhost:5001/login", json={
        'username': 'debug_user',
        'password': 'password123'
    })
    
    if auth_response.status_code == 200:
        token = auth_response.json()['token']
        print(f"Got valid token: {token[:20]}...")
    else:
        print("Could not get valid token")
        return
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Use a fake file ID and name
    file_id = "totally-fake-id-789"
    filename = "nonexistent_file.pdf"
    encoded_filename = quote(filename)
    url = f"http://localhost:5000/download/{file_id}/{encoded_filename}"
    
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if "Token is missing!" in response.text or response.status_code == 401:
            print("✗ Token was rejected at gateway - authentication issue exists")
        elif "File not found" in response.text or response.status_code == 404:
            print("✓ Token accepted by gateway, file not found - authentication working correctly")
        else:
            print("? Unexpected response from gateway")
    except Exception as e:
        print(f"Error with gateway test: {e}")

def main():
    print("=== Authentication Flow Test ===")
    
    test_auth_without_token()
    test_auth_with_bad_token()
    test_auth_with_good_token_but_fake_file()
    test_gateway_auth_with_good_token_but_fake_file()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()