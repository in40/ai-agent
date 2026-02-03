#!/usr/bin/env python3
"""
Test script to verify the download timeout functionality
"""
import os
import sys
import time

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.settings import DOWNLOAD_TIMEOUT_SECONDS, MCP_SERVICE_CALL_TIMEOUT

def test_timeout_values():
    """Test that the timeout values are correctly loaded from environment"""
    print(f"Download timeout: {DOWNLOAD_TIMEOUT_SECONDS} seconds")
    print(f"MCP service call timeout: {MCP_SERVICE_CALL_TIMEOUT} seconds")
    
    # Verify the values are as expected
    assert DOWNLOAD_TIMEOUT_SECONDS == 3, f"Expected download timeout to be 3, got {DOWNLOAD_TIMEOUT_SECONDS}"
    assert MCP_SERVICE_CALL_TIMEOUT == 30, f"Expected MCP service timeout to be 30, got {MCP_SERVICE_CALL_TIMEOUT}"
    
    print("✅ Timeout values are correctly loaded from environment")

if __name__ == "__main__":
    test_timeout_values()
    print("All tests passed!")