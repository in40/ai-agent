#!/usr/bin/env python3
"""
Test script to verify the environment variable configuration for GigaChat SSL.
"""

import os
from config.settings import GIGACHAT_VERIFY_SSL_CERTS

def test_env_config():
    """
    Test that the environment variable is properly read
    """
    print("Testing GigaChat SSL environment variable configuration...")
    print(f"Current GIGACHAT_VERIFY_SSL_CERTS setting: {GIGACHAT_VERIFY_SSL_CERTS}")
    print(f"Type: {type(GIGACHAT_VERIFY_SSL_CERTS)}")
    
    # Test setting the environment variable temporarily
    original_env = os.environ.get('GIGACHAT_VERIFY_SSL_CERTS')
    
    # Test with 'false' value
    os.environ['GIGACHAT_VERIFY_SSL_CERTS'] = 'false'
    from config.settings import GIGACHAT_VERIFY_SSL_CERTS as verify_false
    print(f"With GIGACHAT_VERIFY_SSL_CERTS='false': {verify_false}")
    
    # Test with 'true' value
    os.environ['GIGACHAT_VERIFY_SSL_CERTS'] = 'true'
    from config.settings import GIGACHAT_VERIFY_SSL_CERTS as verify_true
    print(f"With GIGACHAT_VERIFY_SSL_CERTS='true': {verify_true}")
    
    # Restore original value
    if original_env is not None:
        os.environ['GIGACHAT_VERIFY_SSL_CERTS'] = original_env
    elif 'GIGACHAT_VERIFY_SSL_CERTS' in os.environ:
        del os.environ['GIGACHAT_VERIFY_SSL_CERTS']
    
    print("\nEnvironment variable test completed successfully!")

if __name__ == "__main__":
    test_env_config()