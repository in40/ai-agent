#!/usr/bin/env python3
"""
Test the download functionality after the fix
"""
import requests
import os
from urllib.parse import quote

def test_download_after_fix():
    """Test download functionality after implementing the fix"""
    print("=== Testing download functionality after fix ===")
    
    # Get a valid token
    auth_response = requests.post("http://localhost:5001/login", json={
        'username': 'debug_user',
        'password': 'password123'
    })
    
    if auth_response.status_code != 200:
        print("Could not get valid token")
        return
    
    token = auth_response.json()['token']
    print(f"Got valid token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Test with the exact file from the user's example
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    filename = "ГОСТ_Р_ИСО_МЭК_27001-2021.pdf"  # This is the sanitized version that would be in the URL
    encoded_filename = quote(filename)
    
    print(f"Testing download for file ID: {file_id}")
    print(f"Testing with sanitized filename: {filename}")
    
    # Test direct RAG service
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    print(f"Direct RAG URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Direct RAG response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS: Direct RAG download worked!")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"  Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        elif "Token is missing!" in response.text:
            print("✗ FAILED: Token is still missing!")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ Error in direct RAG download: {e}")
    
    # Test through gateway
    print(f"\nTesting through gateway...")
    gw_encoded_filename = quote(filename)  # Re-encode for gateway URL
    gw_url = f"http://localhost:5000/download/{file_id}/{gw_encoded_filename}"
    print(f"Gateway URL: {gw_url}")
    
    try:
        response = requests.get(gw_url, headers=headers, timeout=30)
        print(f"Gateway response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS: Gateway download worked!")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"  Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        elif "Token is missing!" in response.text:
            print("✗ FAILED: Token is missing at gateway!")
        else:
            print(f"✗ FAILED: {response.text}")
    except Exception as e:
        print(f"✗ Error in gateway download: {e}")

def test_original_filename_as_well():
    """Test with the original filename (with spaces) as well"""
    print(f"\n=== Testing with original filename (spaces) ===")
    
    # Get a valid token
    auth_response = requests.post("http://localhost:5001/login", json={
        'username': 'debug_user',
        'password': 'password123'
    })
    
    if auth_response.status_code != 200:
        print("Could not get valid token")
        return
    
    token = auth_response.json()['token']
    print(f"Got valid token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # Test with the original filename (with spaces)
    file_id = "d43cdd94-0fcc-4849-a0a7-d8cc1a313c3d"
    filename = "ГОСТ Р ИСО МЭК 27001-2021.pdf"  # Original with spaces
    encoded_filename = quote(filename)
    
    print(f"Testing with original filename: {filename}")
    
    # Test direct RAG service
    url = f"http://localhost:5003/download/{file_id}/{encoded_filename}"
    print(f"Direct RAG URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Direct RAG response status: {response.status_code}")
        if response.status_code == 200:
            print("✓ SUCCESS: Direct RAG download with original filename worked!")
        elif "Token is missing!" in response.text:
            print("✗ FAILED: Token is missing!")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error in direct RAG download: {e}")

if __name__ == "__main__":
    test_download_after_fix()
    test_original_filename_as_well()
    print("\n=== Test Complete ===")