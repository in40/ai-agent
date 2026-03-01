#!/usr/bin/env python3
"""Test the API endpoint directly"""
import requests
import json

url = "http://localhost:5003/api/rag/test_extraction_from_docstore"
data = {
    "document_id": "gost-r-50739-1995=edt2006",
    "job_id": "job_job_90825d5e7b99_rst_gov_ru:8443"
}

print(f"Sending request to {url}...")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=40)
    print(f"\nStatus: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    
    if 'application/json' in response.headers.get('content-type', ''):
        result = response.json()
        print(f"\nResponse:\n{json.dumps(result, indent=2, ensure_ascii=False)[:2000]}")
    else:
        print(f"\nResponse text:\n{response.text[:500]}")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 40 seconds")
except Exception as e:
    print(f"ERROR: {e}")
