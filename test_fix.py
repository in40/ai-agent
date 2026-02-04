#!/usr/bin/env python3
"""
Test script to verify the fix for the "Found empty template variable in system prompt: {}" error.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from models.dedicated_mcp_model import DedicatedMCPModel
import json
import logging

# Set up logging to see detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_empty_template_variable_fix():
    """
    Test that the fix for empty template variables works correctly.
    """
    print("Testing the fix for empty template variable error...")
    
    try:
        # Initialize the DedicatedMCPModel
        print("Initializing DedicatedMCPModel...")
        mcp_model = DedicatedMCPModel()
        print("DedicatedMCPModel initialized successfully!")
        
        # Test with a simple user request and empty services list
        user_request = "What services are available?"
        mcp_services = []
        
        print(f"Testing analyze_request_for_mcp_services with request: '{user_request}'")
        result = mcp_model.analyze_request_for_mcp_services(user_request, mcp_services)
        print(f"Result: {result}")
        
        # Test with a simple user request and some mock services
        user_request = "Get information about products"
        mcp_services = [
            {
                "id": "test_service_1",
                "host": "localhost",
                "port": 8080,
                "type": "test",
                "metadata": {"description": "Test service"}
            }
        ]
        
        print(f"Testing analyze_request_for_mcp_services with request: '{user_request}' and mock services")
        result = mcp_model.analyze_request_for_mcp_services(user_request, mcp_services)
        print(f"Result: {result}")
        
        print("All tests passed! The fix appears to be working correctly.")
        return True
        
    except ValueError as e:
        if "Found empty template variable in system prompt" in str(e):
            print(f"ERROR: The original issue still exists: {e}")
            return False
        else:
            print(f"ERROR: Unexpected ValueError: {e}")
            return False
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_empty_template_variable_fix()
    if success:
        print("\n✓ Test PASSED: The fix for empty template variables is working correctly.")
    else:
        print("\n✗ Test FAILED: The issue still exists.")
        sys.exit(1)