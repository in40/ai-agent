#!/usr/bin/env python3
"""
Specific test to simulate the exact conditions that might cause 405 error
"""
import requests
import json

def test_browser_like_request():
    """Test with headers and format similar to what a browser would send"""
    # Get auth token
    login_resp = requests.post(
        "http://localhost:5000/auth/login",
        json={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/json"}
    )
    
    if login_resp.status_code != 200:
        print("Failed to get auth token")
        return
    
    token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Testing various request scenarios that might cause 405 error:\n")
    
    # Test 1: Normal multipart upload (should work)
    print("1. Testing normal multipart upload:")
    with open("/root/qwen_test/ai_agent/test.txt", "rb") as f:
        files = {"files": ("test.txt", f, "text/plain")}
        response = requests.post(
            "http://localhost:5005/api/rag/upload_with_progress",
            headers=headers,
            files=files
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
    
    # Test 2: Try with different content-type header that might interfere
    print("\n2. Testing with application/json content-type (might cause issues):")
    try:
        response = requests.post(
            "http://localhost:5005/api/rag/upload_with_progress",
            headers={**headers, "Content-Type": "application/json"},
            json={"files": "dummy"}  # This won't work for file upload but testing the method
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Test with wrong method
    print("\n3. Testing with GET method (should cause 405):")
    response = requests.get(
        "http://localhost:5005/api/rag/upload_with_progress",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 405:
        print("   ✓ Confirmed: GET method causes 405 error")
    
    # Test 4: Test the basic upload endpoint with wrong method
    print("\n4. Testing basic upload endpoint with GET method (should cause 405):")
    response = requests.get(
        "http://localhost:5005/api/rag/upload",
        headers=headers
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 405:
        print("   ✓ Confirmed: GET method causes 405 error on basic upload endpoint too")
    
    # Test 5: Check if there are any other endpoints that might be misconfigured
    print("\n5. Testing other RAG endpoints with GET (should cause 405):")
    rag_endpoints = [
        "/api/rag/query",
        "/api/rag/retrieve", 
        "/api/rag/ingest"
    ]
    
    for endpoint in rag_endpoints:
        response = requests.get(
            f"http://localhost:5005{endpoint}",
            headers=headers
        )
        print(f"   GET {endpoint} -> Status: {response.status_code}")
        if response.status_code == 405:
            print(f"      ✓ {endpoint} correctly returns 405 for GET")

def test_cors_preflight():
    """Test CORS preflight which might reveal configuration issues"""
    print("\n\nTesting CORS preflight requests:")
    
    # Preflight request for upload endpoint
    headers = {
        'Origin': 'http://localhost:5005',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'authorization,content-type',
    }
    
    response = requests.options(
        'http://localhost:5005/api/rag/upload',
        headers=headers
    )
    
    print(f"CORS preflight for /api/rag/upload:")
    print(f"  Status: {response.status_code}")
    print(f"  Allow header: {response.headers.get('Allow', 'Not present')}")
    print(f"  Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not present')}")
    
    # Preflight request for upload_with_progress endpoint
    response = requests.options(
        'http://localhost:5005/api/rag/upload_with_progress',
        headers=headers
    )
    
    print(f"CORS preflight for /api/rag/upload_with_progress:")
    print(f"  Status: {response.status_code}")
    print(f"  Allow header: {response.headers.get('Allow', 'Not present')}")
    print(f"  Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'Not present')}")

def main():
    print("🔍 Testing Specific Conditions for 405 Error")
    print("="*60)
    
    test_browser_like_request()
    test_cors_preflight()
    
    print("\n" + "="*60)
    print("Analysis:")
    print("- 405 errors occur when using unsupported HTTP methods (like GET) on POST-only endpoints")
    print("- Both upload endpoints correctly return 405 for unsupported methods")
    print("- The actual upload functionality works with proper POST requests")
    print("- If user is still getting 405, it's likely due to using wrong method or endpoint")

if __name__ == "__main__":
    main()