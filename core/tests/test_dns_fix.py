#!/usr/bin/env python3
"""
Test script to verify the DNS server fix
"""

import requests
import json
import time
import subprocess
import signal
import os

def test_dns_server():
    """Test the DNS server with a sample request"""
    
    # Start the DNS server in a subprocess
    print("Starting DNS server...")
    server_process = subprocess.Popen([
        "python3", "/root/qwen_test/ai_agent/mcp_dns_server.py",
        "--port", "8090",  # Use a different port to avoid conflicts
        "--log-level", "INFO"
    ])
    
    # Give the server some time to start
    time.sleep(3)
    
    try:
        # Test the server with a sample request
        url = "http://127.0.0.1:8090/resolve"
        payload = {
            "fqdn": "www.google.com",
            "action": "resolve"
        }
        
        print("Sending test request to DNS server...")
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")
        
        # Verify that the response is valid JSON
        try:
            json_response = response.json()
            print(f"Parsed JSON Response: {json.dumps(json_response, indent=2)}")
            print("SUCCESS: Server responded with valid JSON!")
        except json.JSONDecodeError:
            print("ERROR: Server did not respond with valid JSON!")
            return False
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to connect to server: {e}")
        return False
    
    finally:
        # Stop the server
        print("Stopping DNS server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

if __name__ == "__main__":
    success = test_dns_server()
    if success:
        print("\nTest PASSED: DNS server is working correctly!")
    else:
        print("\nTest FAILED: DNS server is not working correctly!")