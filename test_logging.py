#!/usr/bin/env python3
"""
Test script to verify that full LLM requests are displayed on screen logging.
"""

import os
import sys
import logging

# Set the environment variable to enable screen logging
os.environ["ENABLE_SCREEN_LOGGING"] = "true"

# Set up logging to ensure we can see the logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
    ]
)

# Import the necessary modules after setting the environment variable
from models.sql_generator import SQLGenerator
from models.response_generator import ResponseGenerator
from models.security_sql_detector import SecuritySQLDetector
from models.prompt_generator import PromptGenerator
from models.dedicated_mcp_model import DedicatedMCPModel

def test_sql_generator():
    print("Testing SQLGenerator...")
    try:
        generator = SQLGenerator()
        # This will trigger the LLM call and logging
        result = generator.generate_sql(
            "Show all users", 
            {"users": [{"name": {"type": "VARCHAR", "nullable": False}}]}
        )
        print(f"SQLGenerator result: {result}")
    except Exception as e:
        print(f"SQLGenerator error (expected if LLM not configured): {e}")
    print()

def test_response_generator():
    print("Testing ResponseGenerator...")
    try:
        generator = ResponseGenerator()
        # This will trigger the LLM call and logging
        result = generator.generate_natural_language_response("Summarize the following data: [{'name': 'John'}]")
        print(f"ResponseGenerator result: {result}")
    except Exception as e:
        print(f"ResponseGenerator error (expected if LLM not configured): {e}")
    print()

def test_security_detector():
    print("Testing SecuritySQLDetector...")
    try:
        detector = SecuritySQLDetector()
        # This will trigger the LLM call and logging
        is_safe, reason = detector.is_query_safe("SELECT * FROM users;")
        print(f"SecuritySQLDetector result - Safe: {is_safe}, Reason: {reason}")
    except Exception as e:
        print(f"SecuritySQLDetector error (expected if LLM not configured): {e}")
    print()

def test_prompt_generator():
    print("Testing PromptGenerator...")
    try:
        generator = PromptGenerator()
        # This will trigger the LLM call and logging
        result = generator.generate_prompt_for_response_llm("Show all users", [{"name": "John"}])
        print(f"PromptGenerator result: {result}")
    except Exception as e:
        print(f"PromptGenerator error (expected if LLM not configured): {e}")
    print()

def test_dedicated_mcp_model():
    print("Testing DedicatedMCPModel...")
    try:
        model = DedicatedMCPModel()
        # This will trigger the LLM call and logging
        result = model.generate_mcp_tool_calls("Get weather information", [])
        print(f"DedicatedMCPModel result: {result}")
    except Exception as e:
        print(f"DedicatedMCPModel error (expected if LLM not configured): {e}")
    print()

if __name__ == "__main__":
    print("Starting test of LLM request logging...")
    print("="*50)
    
    # Test each component
    test_sql_generator()
    test_response_generator()
    test_security_detector()
    test_prompt_generator()
    test_dedicated_mcp_model()
    
    print("="*50)
    print("Test completed. Check the logs above to verify that full LLM requests are being logged.")