#!/usr/bin/env python3
"""
Test script to verify smart ingestion prompts endpoint
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    """Login and get token"""
    print("1. Testing login...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin"
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token')
        print(f"   ✅ Login successful, token: {token[:20]}...")
        return token
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_prompts(token):
    """Test prompts endpoint"""
    print("\n2. Testing prompts endpoint...")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{BASE_URL}/api/rag/prompts", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        prompts = data.get('prompts', [])
        print(f"   ✅ Prompts loaded: {len(prompts)} prompts")
        for prompt in prompts[:3]:
            print(f"      - {prompt.get('name', 'Unknown')} ({prompt.get('id', 'N/A')})")
        return data
    else:
        print(f"   ❌ Prompts failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_unified_ingest_health(token):
    """Test unified ingest health endpoint"""
    print("\n3. Testing unified ingestion health...")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{BASE_URL}/api/rag/unified_ingest/health", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Health check passed")
        print(f"      Status: {data.get('status', 'unknown')}")
        integrations = data.get('integrations', {})
        if 'document_store' in integrations:
            ds = integrations['document_store']
            print(f"      Document Store: {'✅' if ds.get('available') else '❌'} ({ds.get('enabled', 'N/A')})")
        if 'graphrag' in integrations:
            gr = integrations['graphrag']
            print(f"      GraphRAG: {'✅' if gr.get('available') else '❌'} ({gr.get('url', 'N/A')})")
        return data
    else:
        # Try without auth on the direct port
        response2 = requests.get("http://localhost:5003/health")
        if response2.status_code == 200:
            data = response2.json()
            print(f"   ✅ Health check passed (direct port)")
            print(f"      Status: {data.get('status', 'unknown')}")
            return data
        print(f"   ❌ Health check failed: {response.status_code}")
        return None

def test_document_store_jobs(token):
    """Test document store jobs endpoint"""
    print("\n4. Testing document store jobs...")
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(f"{BASE_URL}/api/rag/document_store/jobs", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        jobs = data.get('jobs', [])
        print(f"   ✅ Document store jobs: {len(jobs)} jobs")
        return data
    else:
        print(f"   ❌ Document store jobs failed: {response.status_code}")
        # This might be expected if document store is not running
        print(f"      (Document store may not be running)")
        return None

def main():
    print("=" * 60)
    print("Smart Ingestion Endpoints Test")
    print("=" * 60)
    
    # Test login
    token = test_login()
    if not token:
        print("\n⚠️  Cannot test authenticated endpoints without valid login")
        print("   Try creating a user first with:")
        print("   python create_test_user.py")
        return
    
    # Test prompts
    test_prompts(token)
    
    # Test health
    test_unified_ingest_health(token)
    
    # Test document store
    test_document_store_jobs(token)
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
