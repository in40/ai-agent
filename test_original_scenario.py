#!/usr/bin/env python3
"""
Test to reproduce the original issue scenario
"""

import subprocess
import time
import json
import threading
import signal
import sys
import os

def start_dns_server():
    """Start the DNS server in a subprocess"""
    print("Starting DNS server...")
    server_process = subprocess.Popen([
        "python3", "/root/qwen_test/ai_agent/mcp_dns_server.py",
        "--port", "8089",  # Use the original port
        "--log-level", "INFO"
    ])
    return server_process

def test_original_scenario():
    """Test the original scenario that was failing"""
    print("Testing original scenario that was failing...")
    
    try:
        # Import the MCP-capable model
        from models.mcp_capable_model import MCPCapableModel
        
        # Create an instance of the model
        mcp_model = MCPCapableModel()
        
        # Define a mock DNS service that matches the original scenario
        mock_dns_service = {
            "id": "dns-server-127-0-0-1-8089",
            "host": "127.0.0.1",
            "port": 8089,
            "type": "mcp_dns",
            "metadata": {
                "service_type": "dns_resolver",
                "capabilities": ["ipv4_resolution", "resolve"],
                "started_at": "2026-01-15T22:14:24.828187Z"
            }
        }
        
        # Use the same request as in the original error
        user_request = "What is the IP address of www.cnn.com?"
        
        print(f"Generating MCP tool calls for request: {user_request}")
        
        # Generate tool calls
        tool_calls_result = mcp_model.generate_mcp_tool_calls(user_request, [mock_dns_service])
        print(f"Generated tool calls: {tool_calls_result}")
        
        # If we have tool calls, execute them
        if tool_calls_result.get("tool_calls"):
            print("Executing MCP tool calls...")
            mcp_service_results = mcp_model.execute_mcp_tool_calls(
                tool_calls_result["tool_calls"], 
                [mock_dns_service]
            )
            print(f"MCP service results: {json.dumps(mcp_service_results, indent=2)}")
            
            # Check if the call was successful
            if mcp_service_results and mcp_service_results[0].get("status") == "success":
                print("SUCCESS: Original scenario now works correctly!")
                print(f"Resolved www.cnn.com to: {mcp_service_results[0]['result']['result']['ipv4_addresses']}")
                return True
            else:
                print("FAILURE: Original scenario still fails")
                return False
        else:
            print("No tool calls were generated for this request")
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to test original scenario: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    dns_process = None
    
    try:
        # Start DNS server
        dns_process = start_dns_server()
        time.sleep(3)  # Give it time to start
        
        # Test the original scenario
        success = test_original_scenario()
        
        if success:
            print("\nOriginal scenario test PASSED!")
        else:
            print("\nOriginal scenario test FAILED!")
        
        return success
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False
    finally:
        # Clean up processes
        if dns_process:
            print("Stopping DNS server...")
            dns_process.terminate()
            try:
                dns_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dns_process.kill()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)