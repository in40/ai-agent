#!/usr/bin/env python3
"""
Test script to verify concurrent download functionality
"""

import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Test server details
SERVER_URL = "http://127.0.0.1:8093"

# Sample URLs to test with (these should be URLs that return quickly for testing)
TEST_URLS = [
    "https://httpbin.org/delay/1",  # Will delay for 1 second
    "https://httpbin.org/delay/2",  # Will delay for 2 seconds  
    "https://httpbin.org/json",     # Quick response
    "https://httpbin.org/uuid",     # Quick response
    "https://httpbin.org/ip",       # Quick response
]


def make_download_request(url_to_download):
    """Make a single download request to the server"""
    payload = {
        "url": url_to_download
    }
    
    try:
        start_time = time.time()
        response = requests.post(SERVER_URL, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Request to {url_to_download} completed in {end_time - start_time:.2f}s with status {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Success: {result.get('success', 'Unknown')}")
            if result.get('result'):
                print(f"  File path: {result['result'].get('file_path', 'N/A')}")
                print(f"  Error: {result['result'].get('error', 'None')}")
        else:
            print(f"  Error response: {response.text[:200]}...")
            
        return response.status_code, response.json() if response.status_code == 200 else response.text
        
    except requests.exceptions.Timeout:
        print(f"Request to {url_to_download} timed out")
        return "TIMEOUT", "Request timed out"
    except requests.exceptions.RequestException as e:
        print(f"Request to {url_to_download} failed: {str(e)}")
        return "ERROR", str(e)


def test_sequential_downloads():
    """Test sequential downloads (baseline)"""
    print("Testing sequential downloads...")
    start_time = time.time()
    
    for url in TEST_URLS:
        make_download_request(url)
    
    end_time = time.time()
    print(f"Sequential downloads completed in {end_time - start_time:.2f}s\n")


def test_concurrent_downloads(max_workers=4):
    """Test concurrent downloads using ThreadPoolExecutor"""
    print(f"Testing concurrent downloads with {max_workers} workers...")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download requests
        future_to_url = {executor.submit(make_download_request, url): url for url in TEST_URLS}
        
        # Wait for all to complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                status, result = future.result()
                print(f"Completed download for {url}: {status}")
            except Exception as e:
                print(f"Download for {url} generated an exception: {e}")
    
    end_time = time.time()
    print(f"Concurrent downloads completed in {end_time - start_time:.2f}s\n")


def test_stress_downloads(num_requests=10, max_workers=5):
    """Test with more requests than workers to test queue handling"""
    print(f"Testing stress scenario with {num_requests} requests and {max_workers} workers...")
    start_time = time.time()
    
    urls = [TEST_URLS[i % len(TEST_URLS)] for i in range(num_requests)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download requests
        future_to_url = {executor.submit(make_download_request, url): url for url in urls}
        
        # Wait for all to complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                status, result = future.result()
                print(f"Completed download for {url}: {status}")
            except Exception as e:
                print(f"Download for {url} generated an exception: {e}")
    
    end_time = time.time()
    print(f"Stress test completed in {end_time - start_time:.2f}s\n")


if __name__ == "__main__":
    print("Testing concurrent download functionality...")
    print(f"Using server at: {SERVER_URL}")
    print(f"Test URLs: {len(TEST_URLS)}\n")
    
    # Run different test scenarios
    test_sequential_downloads()
    test_concurrent_downloads(max_workers=4)
    test_stress_downloads(num_requests=8, max_workers=3)
    
    print("All tests completed!")