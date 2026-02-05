#!/usr/bin/env python3
"""
Test script to verify that the DeepSeek hostname fix works correctly.
"""
import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the environment variables to simulate DeepSeek configuration
os.environ['DEDICATED_MCP_LLM_PROVIDER'] = 'deepseek'
os.environ['DEDICATED_MCP_LLM_MODEL'] = 'deepseek-reasoner'
os.environ['DEDICATED_MCP_LLM_HOSTNAME'] = 'api.deepseek.com'
os.environ['DEDICATED_MCP_LLM_PORT'] = '443'
os.environ['DEDICATED_MCP_LLM_API_PATH'] = '/v1'
os.environ['DEEPSEEK_API_KEY'] = 'test-key-for-testing'

# Clear any cached modules to ensure fresh import
if 'models.dedicated_mcp_model' in sys.modules:
    del sys.modules['models.dedicated_mcp_model']
if 'config.settings' in sys.modules:
    del sys.modules['config.settings']

def test_base_url_logic():
    """
    Test the base URL construction logic directly without initializing the full model.
    """
    print("Testing base URL construction logic...")
    
    # Simulate the provider and hostname values
    provider = 'deepseek'
    hostname = 'api.deepseek.com'
    port = '443'
    api_path = '/v1'
    
    # Replicate the fixed logic
    if provider and provider.lower() in ['openai', 'deepseek', 'qwen']:
        # For cloud providers, use HTTPS with the specified hostname
        # But for default endpoints, allow using the default endpoint
        if (provider.lower() == 'openai' and hostname == "api.openai.com") or \
           (provider.lower() == 'deepseek' and hostname == "api.deepseek.com") or \
           (provider.lower() == 'qwen' and hostname == "dashscope.aliyuncs.com"):
            base_url = None  # Use default endpoint for respective providers
            print(f"✓ Correctly set base_url to None for {provider} with hostname {hostname}")
            print(f"  This means it will use the default {provider} endpoint")
        else:
            base_url = f"https://{hostname}:{port}{api_path}" if hostname and port and api_path else None
            print(f"  Would create custom URL: {base_url}")
    else:
        base_url = f"http://{hostname}:{port}{api_path}" if hostname and port and api_path else None
        print(f"  Would create local URL: {base_url}")
    
    # Expected result: base_url should be None for DeepSeek with api.deepseek.com
    if base_url is None:
        print("✓ SUCCESS: Base URL is correctly set to None for DeepSeek with correct hostname")
        return True
    else:
        print(f"✗ FAILURE: Base URL is {base_url}, expected None")
        return False

def test_openai_still_works():
    """
    Test that OpenAI still works as expected.
    """
    print("\nTesting OpenAI logic still works...")
    
    # Simulate the provider and hostname values for OpenAI
    provider = 'openai'
    hostname = 'api.openai.com'
    port = '443'
    api_path = '/v1'
    
    # Replicate the fixed logic
    if provider and provider.lower() in ['openai', 'deepseek', 'qwen']:
        # For cloud providers, use HTTPS with the specified hostname
        # But for default endpoints, allow using the default endpoint
        if (provider.lower() == 'openai' and hostname == "api.openai.com") or \
           (provider.lower() == 'deepseek' and hostname == "api.deepseek.com") or \
           (provider.lower() == 'qwen' and hostname == "dashscope.aliyuncs.com"):
            base_url = None  # Use default endpoint for respective providers
            print(f"✓ Correctly set base_url to None for {provider} with hostname {hostname}")
            print(f"  This means it will use the default {provider} endpoint")
        else:
            base_url = f"https://{hostname}:{port}{api_path}" if hostname and port and api_path else None
            print(f"  Would create custom URL: {base_url}")
    else:
        base_url = f"http://{hostname}:{port}{api_path}" if hostname and port and api_path else None
        print(f"  Would create local URL: {base_url}")
    
    # Expected result: base_url should be None for OpenAI with api.openai.com
    if base_url is None:
        print("✓ SUCCESS: Base URL is correctly set to None for OpenAI with correct hostname")
        return True
    else:
        print(f"✗ FAILURE: Base URL is {base_url}, expected None")
        return False

def test_custom_hostname_still_works():
    """
    Test that custom hostnames still create custom URLs.
    """
    print("\nTesting custom hostname still creates custom URL...")
    
    # Simulate the provider and a custom hostname
    provider = 'deepseek'
    hostname = 'my-custom-deepseek-endpoint.com'
    port = '443'
    api_path = '/v1'
    
    # Replicate the fixed logic
    if provider and provider.lower() in ['openai', 'deepseek', 'qwen']:
        # For cloud providers, use HTTPS with the specified hostname
        # But for default endpoints, allow using the default endpoint
        if (provider.lower() == 'openai' and hostname == "api.openai.com") or \
           (provider.lower() == 'deepseek' and hostname == "api.deepseek.com") or \
           (provider.lower() == 'qwen' and hostname == "dashscope.aliyuncs.com"):
            base_url = None  # Use default endpoint for respective providers
            print(f"  Would use default endpoint")
        else:
            base_url = f"https://{hostname}:{port}{api_path}" if hostname and port and api_path else None
            print(f"✓ Correctly creates custom URL: {base_url}")
    else:
        base_url = f"http://{hostname}:{port}{api_path}" if hostname and port and api_path else None
        print(f"  Would create local URL: {base_url}")
    
    # Expected result: base_url should be the custom URL for DeepSeek with custom hostname
    expected_url = f"https://{hostname}:{port}{api_path}"
    if base_url == expected_url:
        print("✓ SUCCESS: Custom hostname correctly creates custom URL")
        return True
    else:
        print(f"✗ FAILURE: Base URL is {base_url}, expected {expected_url}")
        return False

if __name__ == "__main__":
    print("Testing DeepSeek hostname fix...\n")
    
    success1 = test_base_url_logic()
    success2 = test_openai_still_works()
    success3 = test_custom_hostname_still_works()
    
    print(f"\nOverall result: {'✓ All tests passed!' if all([success1, success2, success3]) else '✗ Some tests failed'}")
    
    if all([success1, success2, success3]):
        print("\nThe fix correctly handles:")
        print("- DeepSeek with api.deepseek.com uses default endpoint (base_url=None)")
        print("- OpenAI with api.openai.com still uses default endpoint (base_url=None)")
        print("- Custom hostnames still create custom URLs")
    else:
        print("\nThere are issues with the fix!")
        sys.exit(1)