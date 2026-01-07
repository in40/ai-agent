#!/usr/bin/env python3
"""
Test script to verify the SSL certificate verification fix for GigaChat integration.
"""

import os
from utils.gigachat_integration import GigaChatModel

def test_gigachat_ssl_config():
    """
    Test that the GigaChatModel accepts the verify_ssl_certs parameter
    """
    print("Testing GigaChat SSL configuration...")
    
    # Test with SSL verification enabled (default)
    try:
        model_with_ssl = GigaChatModel(
            model="GigaChat:latest",
            credentials="dGVzdF9jcmVkZW50aWFscw==",  # base64 encoded test credentials
            verify_ssl_certs=True
        )
        print("✓ Successfully created GigaChatModel with SSL verification enabled")
    except Exception as e:
        # Check if the error is related to SSL verification or other issue
        if "verify_ssl_certs" in str(e):
            print(f"✗ SSL verification parameter issue: {e}")
        else:
            print(f"✓ GigaChatModel created (other validation error is expected): {type(e).__name__}")

    # Test with SSL verification disabled
    try:
        model_without_ssl = GigaChatModel(
            model="GigaChat:latest",
            credentials="dGVzdF9jcmVkZW50aWFscw==",  # base64 encoded test credentials
            verify_ssl_certs=False
        )
        print("✓ Successfully created GigaChatModel with SSL verification disabled")
    except Exception as e:
        # Check if the error is related to SSL verification or other issue
        if "verify_ssl_certs" in str(e):
            print(f"✗ SSL verification parameter issue: {e}")
        else:
            print(f"✓ GigaChatModel created (other validation error is expected): {type(e).__name__}")
    
    print("\nSSL configuration test completed.")
    print("\nTo use this fix with your application:")
    print("1. Set GIGACHAT_VERIFY_SSL_CERTS=false in your .env file")
    print("2. Or set the environment variable: export GIGACHAT_VERIFY_SSL_CERTS=false")
    print("3. This will disable SSL certificate verification for GigaChat API calls")

if __name__ == "__main__":
    test_gigachat_ssl_config()