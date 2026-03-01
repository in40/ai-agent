#!/usr/bin/env python3
import requests

# First login to get token
login = requests.post('http://localhost:5001/api/auth/login', 
    json={'username': 'admin', 'password': 'admin123'})
token = login.json().get('token', '')
print(f"Token: {token[:50]}..." if token else "No token")

if token:
    # Test retrieve endpoint
    resp = requests.post('http://localhost:5003/api/rag/retrieve',
        headers={'Authorization': f'Bearer {token}'},
        json={'query': 'test', 'mode': 'hybrid'})
    print(f"Retrieve status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Documents: {data.get('count', 0)}")
    else:
        print(f"Error: {resp.text[:200]}")
