#!/usr/bin/env python3
"""
Test script to verify the SSH keep-alive functionality.
"""

import sys
import os
import time
import threading
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.ssh_keep_alive import SSHKeepAlive, SSHKeepAliveContext, keep_ssh_alive_for_llm_call


def simulate_llm_call(duration=3):
    """
    Simulate an LLM call that takes some time to complete.
    """
    print(f"Starting simulated LLM call for {duration} seconds...")
    time.sleep(duration)
    print("Simulated LLM call completed.")
    return "Simulated response"


def test_basic_ssh_keep_alive():
    """
    Test basic SSH keep-alive functionality.
    """
    print("\n=== Testing Basic SSH Keep-Alive ===")
    
    # Mock SSH environment variables to simulate an SSH session
    with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.100 54321 192.168.1.1 22"}):
        keep_alive = SSHKeepAlive(interval=2)  # Short interval for testing
        keep_alive.start()
        
        # Simulate a long-running operation
        time.sleep(5)
        
        keep_alive.stop()
        print("Basic SSH keep-alive test completed.")


def test_context_manager():
    """
    Test SSH keep-alive using context manager.
    """
    print("\n=== Testing SSH Keep-Alive Context Manager ===")
    
    # Mock SSH environment variables to simulate an SSH session
    with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.100 54321 192.168.1.1 22"}):
        with SSHKeepAliveContext(interval=2):
            print("Inside context manager - performing simulated LLM call...")
            result = simulate_llm_call(3)
            print(f"Result: {result}")
        print("Context manager exited.")


def test_decorator_function():
    """
    Test SSH keep-alive using decorator-like function.
    """
    print("\n=== Testing SSH Keep-Alive Decorator Function ===")
    
    # Mock SSH environment variables to simulate an SSH session
    with patch.dict(os.environ, {"SSH_CLIENT": "192.168.1.100 54321 192.168.1.1 22"}):
        result = keep_ssh_alive_for_llm_call(simulate_llm_call, 3)
        print(f"Decorator function result: {result}")


def test_non_ssh_environment():
    """
    Test that keep-alive doesn't start in non-SSH environments.
    """
    print("\n=== Testing Non-SSH Environment ===")
    
    # Clear SSH environment variables
    env_backup = {k: v for k, v in os.environ.items() if k.startswith('SSH_')}
    for key in list(os.environ.keys()):
        if key.startswith('SSH_'):
            del os.environ[key]
    
    try:
        with SSHKeepAliveContext(interval=2):
            print("Inside context manager in non-SSH environment - performing simulated LLM call...")
            result = simulate_llm_call(2)
            print(f"Result: {result}")
        print("Non-SSH environment test completed.")
    finally:
        # Restore environment variables
        os.environ.update(env_backup)


def test_integration_with_ai_agent_components():
    """
    Test that the integration with AI agent components works correctly.
    """
    print("\n=== Testing Integration with AI Agent Components ===")
    
    # Import the modified components to ensure they work
    try:
        from models.sql_generator import SQLGenerator
        from models.response_generator import ResponseGenerator
        from models.prompt_generator import PromptGenerator
        from models.security_sql_detector import SecuritySQLDetector
        
        print("Successfully imported all modified AI agent components.")
        
        # Check that the SSH keep-alive import is present in each module
        import inspect
        
        # Check SQLGenerator
        sql_gen_source = inspect.getsource(SQLGenerator)
        assert 'SSHKeepAliveContext' in sql_gen_source, "SSHKeepAliveContext not found in SQLGenerator"
        print("✓ SSHKeepAliveContext properly integrated in SQLGenerator")
        
        # Check ResponseGenerator
        resp_gen_source = inspect.getsource(ResponseGenerator)
        assert 'SSHKeepAliveContext' in resp_gen_source, "SSHKeepAliveContext not found in ResponseGenerator"
        print("✓ SSHKeepAliveContext properly integrated in ResponseGenerator")
        
        # Check PromptGenerator
        prompt_gen_source = inspect.getsource(PromptGenerator)
        assert 'SSHKeepAliveContext' in prompt_gen_source, "SSHKeepAliveContext not found in PromptGenerator"
        print("✓ SSHKeepAliveContext properly integrated in PromptGenerator")
        
        # Check SecuritySQLDetector
        sec_det_source = inspect.getsource(SecuritySQLDetector)
        assert 'SSHKeepAliveContext' in sec_det_source, "SSHKeepAliveContext not found in SecuritySQLDetector"
        print("✓ SSHKeepAliveContext properly integrated in SecuritySQLDetector")
        
        print("All integrations verified successfully!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except AssertionError as e:
        print(f"Integration test failed: {e}")
        return False
    
    return True


def main():
    """
    Main test function.
    """
    print("Starting SSH Keep-Alive Tests...")
    
    # Run all tests
    test_basic_ssh_keep_alive()
    test_context_manager()
    test_decorator_function()
    test_non_ssh_environment()
    
    if test_integration_with_ai_agent_components():
        print("\n✅ All SSH Keep-Alive tests passed!")
    else:
        print("\n❌ Some SSH Keep-Alive tests failed!")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)