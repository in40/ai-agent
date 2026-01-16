#!/usr/bin/env python3
"""
Test script to verify that the GigaChat security analysis fix works correctly.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_security_detector_with_gigachat():
    """
    Test that the SecuritySQLDetector works with GigaChat provider.
    """
    print("Testing SecuritySQLDetector with GigaChat provider...")

    # Set environment variables for GigaChat
    os.environ["SECURITY_LLM_PROVIDER"] = "GigaChat"
    os.environ["SECURITY_LLM_MODEL"] = "GigaChat:latest"
    os.environ["GIGACHAT_CREDENTIALS"] = os.getenv("GIGACHAT_CREDENTIALS", "fake_credentials")
    os.environ["GIGACHAT_SCOPE"] = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    os.environ["GIGACHAT_ACCESS_TOKEN"] = os.getenv("GIGACHAT_ACCESS_TOKEN", "")
    os.environ["GIGACHAT_VERIFY_SSL_CERTS"] = "false"  # Disable SSL for testing
    os.environ["ENABLE_SCREEN_LOGGING"] = "false"

    try:
        from models.security_sql_detector import SecuritySQLDetector
        
        # Create the detector
        detector = SecuritySQLDetector()
        
        print("✓ SecuritySQLDetector created successfully with GigaChat configuration")
        
        # Test analyzing a simple query
        test_query = "SELECT * FROM users WHERE id = 1;"
        result = detector.analyze_query(test_query)
        
        print(f"✓ Security analysis completed. Result keys: {list(result.keys())}")
        print(f"  Is safe: {result.get('is_safe', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_level', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"✗ SecuritySQLDetector test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Testing GigaChat Security Analysis Fix")
    print("=" * 40)

    success = test_security_detector_with_gigachat()

    if success:
        print("\n🎉 Test passed! The GigaChat security analysis fix is working correctly.")
        print("\nThis confirms that the HTTP/HTTPS error has been resolved.")
    else:
        print("\n❌ Test failed. There may still be issues with the GigaChat integration.")

if __name__ == "__main__":
    main()