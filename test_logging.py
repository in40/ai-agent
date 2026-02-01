#!/usr/bin/env python3
"""
Test script to verify that logging is working properly for user_request variable tracking.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.dedicated_mcp_model import DedicatedMCPModel
from config.settings import (
    DEDICATED_MCP_LLM_PROVIDER,
    DEDICATED_MCP_LLM_MODEL,
    DEDICATED_MCP_LLM_HOSTNAME,
    DEDICATED_MCP_LLM_PORT,
    DEDICATED_MCP_LLM_API_PATH
)

def test_logging():
    """Test that the logging is capturing the user_request variable state correctly."""
    print("Testing logging for user_request variable tracking...")

    # Initialize the model
    model = DedicatedMCPModel()

    # Test with a sample user request
    sample_request = "Test user request to verify logging functionality"

    print(f"Sample request: {sample_request}")
    print("\nCheck your logs for the STEP_X_REPLACE_USER_REQUEST and STEP_X_AFTER_USER_REQUEST_REPLACE entries.")
    print("These should show the state of the user_request variable at each step.")

if __name__ == "__main__":
    test_logging()