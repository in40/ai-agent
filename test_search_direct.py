#!/usr/bin/env python3
"""
Test script to directly call the search server and see what's happening
"""
import requests
import json

# Test the search server directly
search_url = "http://127.0.0.1:8090"

test_query = {
    "query": "что мы знаем про правила малых баз?"
}

print("Making direct request to search server...")
try:
    response = requests.post(
        search_url,
        json=test_query,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"Response JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
    except ValueError:
        print(f"Response text: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    
# Also test the Brave Search API directly
print("\nTesting Brave Search API directly...")
brave_api_key = "BSAh1LVPlS2vl5hVq4j_yClWvqmKymX"  # From environment

headers = {
    'X-Subscription-Token': brave_api_key,
    'Content-Type': 'application/json'
}

params = {
    'q': 'что мы знаем про правила малых баз?',
    'text_decorations': 0,
    'spellcheck': 1
}

try:
    brave_response = requests.get(
        'https://api.search.brave.com/res/v1/web/search',
        headers=headers,
        params=params,
        timeout=30
    )
    
    print(f"Brave API response status: {brave_response.status_code}")
    
    if brave_response.status_code == 200:
        try:
            brave_data = brave_response.json()
            print(f"Brave API results count: {len(brave_data.get('web', {}).get('results', []))}")
            print(f"First few results:")
            for i, result in enumerate(brave_data.get('web', {}).get('results', [])[:3]):
                print(f"  {i+1}. {result.get('title', 'No title')}")
                print(f"     {result.get('description', 'No description')[:100]}...")
        except ValueError:
            print(f"Brave API response text: {brave_response.text[:500]}...")
    else:
        print(f"Brave API error: {brave_response.status_code} - {brave_response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Brave API request failed: {e}")