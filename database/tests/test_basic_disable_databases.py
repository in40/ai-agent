#!/usr/bin/env python3
"""
Simple test to verify that the disable databases functionality works without causing infinite loops.
"""

import os
from unittest.mock import patch, MagicMock

def test_basic_functionality():
    """Test basic functionality without complex reloading"""
    print("Testing basic functionality...")
    
    # Test that the setting exists and has a default value
    from config.settings import DISABLE_DATABASES
    print(f"Current DISABLE_DATABASES value: {DISABLE_DATABASES}")
    
    # Test creating an agent with databases enabled (default)
    from core.ai_agent import AIAgent
    agent = AIAgent()
    print(f"Agent db_manager is None: {agent.db_manager is None}")
    print(f"Agent sql_executor is None: {agent.sql_executor is None}")
    
    print("✓ Basic functionality test passed!")


def test_with_env_var():
    """Test with environment variable set"""
    print("\nTesting with environment variable set...")
    
    # Set environment variable
    os.environ['DISABLE_DATABASES'] = 'true'
    
    # Import fresh modules to pick up the environment change
    import sys
    if 'config.settings' in sys.modules:
        del sys.modules['config.settings']
    if 'core.ai_agent' in sys.modules:
        del sys.modules['core.ai_agent']
    
    # Now import and check
    from config.settings import DISABLE_DATABASES
    print(f"DISABLE_DATABASES with env var set to 'true': {DISABLE_DATABASES}")
    
    # Create an agent with databases disabled
    from core.ai_agent import AIAgent
    agent = AIAgent()
    print(f"Agent db_manager is None: {agent.db_manager is None}")
    print(f"Agent sql_executor is None: {agent.sql_executor is None}")
    
    # Verify they are indeed None when disabled
    assert agent.db_manager is None, "db_manager should be None when databases are disabled"
    assert agent.sql_executor is None, "sql_executor should be None when databases are disabled"
    
    print("✓ Environment variable test passed!")
    
    # Clean up environment
    del os.environ['DISABLE_DATABASES']


if __name__ == "__main__":
    test_basic_functionality()
    test_with_env_var()
    print("\n🎉 All basic tests passed!")