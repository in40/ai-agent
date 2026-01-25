#!/usr/bin/env python3
"""
Comprehensive test suite to identify the root cause of HTTP 405 error during file uploads
"""
import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5005"
GATEWAY_URL = "http://localhost:5000"
TEST_FILE_PATH = "/root/qwen_test/ai_agent/test_upload.txt"

def create_test_file():
    """Create a test file for upload testing"""
    with open(TEST_FILE_PATH, 'w') as f:
        f.write("This is a test file for upload functionality.\n")
        f.write(f"Created at: {time.time()}\n")
    print(f"Created test file: {TEST_FILE_PATH}")

def get_auth_token():
    """Get a fresh authentication token"""
    try:
        response = requests.post(
            f"{GATEWAY_URL}/auth/login",
            json={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"✓ Got authentication token: {token[:20]}...")
            return token
        else:
            print(f"✗ Failed to get token: {response.status_code} - {response.text}")
            # Try registering admin user if it doesn't exist
            reg_response = requests.post(
                f"{GATEWAY_URL}/auth/register",
                json={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/json"}
            )
            
            if reg_response.status_code == 200:
                print("✓ Registered admin user, trying login again...")
                return get_auth_token()  # Recursive call to try login again
            else:
                print(f"✗ Failed to register admin: {reg_response.status_code} - {reg_response.text}")
                return None
    except Exception as e:
        print(f"✗ Error getting auth token: {e}")
        return None

def test_endpoint(endpoint, method="GET", headers=None, data=None, files=None):
    """Generic function to test an endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n--- Testing {method} {endpoint} ---")
    print(f"URL: {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method.upper() == "OPTIONS":
            response = requests.options(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return None
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        return response
    except Exception as e:
        print(f"✗ Error testing {endpoint}: {e}")
        return None

def test_health_endpoints():
    """Test basic health endpoints"""
    print("\n=== Testing Health Endpoints ===")
    
    # Test web client health
    test_endpoint("/api/health", "GET")
    
    # Test gateway health
    try:
        response = requests.get(f"{GATEWAY_URL}/health")
        print(f"Gateway health: {response.status_code} - {response.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"Gateway health check failed: {e}")

def test_rag_endpoints_with_auth(token):
    """Test all RAG endpoints with authentication"""
    print("\n=== Testing RAG Endpoints with Authentication ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test basic RAG endpoints
    test_endpoint("/api/rag/query", "POST", headers, {"query": "test"})
    test_endpoint("/api/rag/retrieve", "POST", headers, {"query": "test"})
    test_endpoint("/api/rag/ingest", "POST", headers, {"file_paths": ["/tmp/test.txt"]})
    
    # Test upload endpoints specifically
    print("\n--- Testing Upload Endpoints ---")
    
    # Test basic upload endpoint
    if os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            response = test_endpoint("/api/rag/upload", "POST", headers, files=files)
    
    # Test upload with progress endpoint
    if os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            response = test_endpoint("/api/rag/upload_with_progress", "POST", headers, files=files)

def test_method_allowed_scenarios():
    """Test different HTTP methods to see which cause 405 errors"""
    print("\n=== Testing HTTP Methods for 405 Errors ===")
    
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints_to_test = [
        "/api/rag/upload",
        "/api/rag/upload_with_progress",
        "/api/rag/query",
        "/api/rag/retrieve",
        "/api/rag/ingest"
    ]
    
    methods_to_test = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    
    for endpoint in endpoints_to_test:
        print(f"\nTesting methods for {endpoint}:")
        for method in methods_to_test:
            # Skip methods that are known to not be supported
            if method in ["GET", "PUT", "DELETE", "PATCH", "HEAD"]:
                if endpoint in ["/api/rag/upload", "/api/rag/upload_with_progress"] and method != "POST":
                    continue  # These upload endpoints only support POST
                elif endpoint in ["/api/rag/query", "/api/rag/retrieve", "/api/rag/ingest"] and method != "POST":
                    continue  # These endpoints only support POST
            
            response = test_endpoint(endpoint, method, headers)
            if response and response.status_code == 405:
                print(f"  ✗ {method} {endpoint} -> 405 Method Not Allowed")

def test_upload_scenarios():
    """Test various upload scenarios that might cause 405 errors"""
    print("\n=== Testing Upload Scenarios ===")
    
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Scenario 1: Upload without authentication
    print("\n1. Testing upload without authentication:")
    if os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/rag/upload", files=files)
            print(f"   Status: {response.status_code}, Response: {response.text[:100]}")
    
    # Scenario 2: Upload with invalid/malformed token
    print("\n2. Testing upload with invalid token:")
    invalid_headers = {"Authorization": "Bearer invalid_token_here"}
    if os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/rag/upload", headers=invalid_headers, files=files)
            print(f"   Status: {response.status_code}, Response: {response.text[:100]}")
    
    # Scenario 3: Upload with expired token (simulate by using old token)
    print("\n3. Testing upload with potentially expired token:")
    if os.path.exists(TEST_FILE_PATH):
        with open(TEST_FILE_PATH, 'rb') as f:
            files = {'files': ('test_upload.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/api/rag/upload", headers=headers, files=files)
            print(f"   Status: {response.status_code}, Response: {response.text[:100]}")
    
    # Scenario 4: Upload with wrong content type
    print("\n4. Testing upload with wrong method/content:")
    wrong_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(f"{BASE_URL}/api/rag/upload", headers=wrong_headers, 
                             json={"files": "should_be_multipart"})
    print(f"   Status: {response.status_code}, Response: {response.text[:100]}")

def test_specific_405_conditions():
    """Test the specific conditions that might lead to 405 errors"""
    print("\n=== Testing Specific 405 Conditions ===")
    
    # Check if the issue is with CORS preflight requests
    print("\n1. Testing OPTIONS request (CORS preflight):")
    response = requests.options(f"{BASE_URL}/api/rag/upload")
    print(f"   OPTIONS /api/rag/upload -> Status: {response.status_code}")
    print(f"   Allow header: {response.headers.get('Allow', 'Not present')}")
    
    # Check if the issue is with specific file types
    print("\n2. Testing with different file types:")
    token = get_auth_token()
    if not token:
        print("Cannot proceed without authentication token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with different file extensions
    test_files = [
        ("test.txt", "text/plain"),
        ("test.pdf", "application/pdf"),  # Won't create this, just test the upload
        ("test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    ]
    
    for filename, content_type in test_files:
        print(f"   Testing upload with {filename} ({content_type}):")
        # Create a temporary file with the right extension
        temp_path = f"/tmp/{filename}"
        with open(temp_path, 'w') as f:
            f.write(f"Test file for {filename}")
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'files': (filename, f, content_type)}
                response = requests.post(f"{BASE_URL}/api/rag/upload", headers=headers, files=files)
                print(f"     Status: {response.status_code}")
        except Exception as e:
            print(f"     Error: {e}")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

def main():
    """Main test function"""
    print("🔍 Comprehensive Test Suite for Upload 405 Error")
    print("="*60)
    
    # Create test file
    create_test_file()
    
    # Run all tests
    test_health_endpoints()
    test_method_allowed_scenarios()
    test_upload_scenarios()
    test_specific_405_conditions()
    
    print("\n" + "="*60)
    print("Test suite completed. Review the output above to identify the root cause.")
    
    # Clean up
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)
        print(f"Cleaned up test file: {TEST_FILE_PATH}")

if __name__ == "__main__":
    main()