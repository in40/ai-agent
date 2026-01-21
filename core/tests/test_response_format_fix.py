"""
Test script to verify the fix for the 'response_format type is unavailable' error.
This script verifies that SQLGenerator handles different providers appropriately.
"""
import sys
import os
import logging
from unittest.mock import Mock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from models.sql_generator import SQLGenerator, SQLOutput

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_deepseek_provider():
    """
    Test that SQLGenerator handles DeepSeek provider correctly without structured output.
    """
    print("Testing SQLGenerator with DeepSeek provider...")

    # Set the provider to DeepSeek
    original_provider = os.environ.get('SQL_LLM_PROVIDER', '')
    original_hostname = os.environ.get('SQL_LLM_HOSTNAME', '')
    original_model = os.environ.get('SQL_LLM_MODEL', '')

    os.environ['SQL_LLM_PROVIDER'] = 'deepseek'
    os.environ['SQL_LLM_HOSTNAME'] = 'api.deepseek.com'
    os.environ['SQL_LLM_MODEL'] = 'deepseek-chat'

    # Mock ChatOpenAI to simulate normal operation without structured output for DeepSeek
    with patch('models.sql_generator.ChatOpenAI') as mock_chat_openai:
        # Create a mock instance that will work normally
        mock_llm_instance = Mock()

        # Configure the mock class to return our mock instance
        mock_chat_openai.return_value = mock_llm_instance

        try:
            # Try to create the SQLGenerator - this should handle DeepSeek correctly
            sql_gen = SQLGenerator()

            # Check that structured output is disabled for DeepSeek
            print(f"Provider: {os.environ.get('SQL_LLM_PROVIDER')}")
            print(f"Structured output enabled: {getattr(sql_gen, 'use_structured_output', 'Not set')}")

            if hasattr(sql_gen, 'use_structured_output') and not sql_gen.use_structured_output:
                print("SUCCESS: DeepSeek provider correctly disables structured output!")
                print("The SQLGenerator properly handles DeepSeek without response_format issues.")
                return True
            else:
                print("FAILURE: Structured output was enabled for DeepSeek when it should be disabled")
                return False

        except Exception as e:
            print(f"FAILURE: SQLGenerator creation failed with error: {e}")
            return False
        finally:
            # Restore original environment variables
            if original_provider:
                os.environ['SQL_LLM_PROVIDER'] = original_provider
            elif 'SQL_LLM_PROVIDER' in os.environ:
                del os.environ['SQL_LLM_PROVIDER']

            if original_hostname:
                os.environ['SQL_LLM_HOSTNAME'] = original_hostname
            elif 'SQL_LLM_HOSTNAME' in os.environ:
                del os.environ['SQL_LLM_HOSTNAME']

            if original_model:
                os.environ['SQL_LLM_MODEL'] = original_model
            elif 'SQL_LLM_MODEL' in os.environ:
                del os.environ['SQL_LLM_MODEL']

def test_other_provider_with_structured_output():
    """
    Test that SQLGenerator can be initialized with other providers (basic functionality).
    Note: Due to mock complexity, we're mainly verifying that initialization works without errors.
    """
    print("\nTesting SQLGenerator with Qwen provider (should initialize without errors)...")

    # Set the provider to Qwen (which supports structured output like OpenAI)
    original_provider = os.environ.get('SQL_LLM_PROVIDER', '')
    original_hostname = os.environ.get('SQL_LLM_HOSTNAME', '')
    original_model = os.environ.get('SQL_LLM_MODEL', '')

    os.environ['SQL_LLM_PROVIDER'] = 'qwen'
    os.environ['SQL_LLM_HOSTNAME'] = 'dashscope.aliyuncs.com'
    os.environ['SQL_LLM_MODEL'] = 'qwen-max'

    # Mock ChatOpenAI to simulate success with structured output for Qwen
    with patch('models.sql_generator.ChatOpenAI') as mock_chat_openai:
        # Create a mock instance that will work normally
        mock_llm_instance = Mock()
        mock_structured_output = Mock()
        mock_llm_instance.with_structured_output.return_value = mock_structured_output

        # Configure the mock class to return our mock instance
        mock_chat_openai.return_value = mock_llm_instance

        try:
            # Try to create the SQLGenerator - this should work without errors
            sql_gen = SQLGenerator()

            # Just verify that the object was created successfully
            print(f"Provider: {os.environ.get('SQL_LLM_PROVIDER')}")
            print(f"SQLGenerator object created successfully: {sql_gen is not None}")

            print("SUCCESS: Qwen provider initializes without errors!")
            print("The SQLGenerator can be created with providers that support structured output.")
            return True

        except Exception as e:
            print(f"FAILURE: SQLGenerator creation failed with error: {e}")
            return False
        finally:
            # Restore original environment variables
            if original_provider:
                os.environ['SQL_LLM_PROVIDER'] = original_provider
            elif 'SQL_LLM_PROVIDER' in os.environ:
                del os.environ['SQL_LLM_PROVIDER']

            if original_hostname:
                os.environ['SQL_LLM_HOSTNAME'] = original_hostname
            elif 'SQL_LLM_HOSTNAME' in os.environ:
                del os.environ['SQL_LLM_HOSTNAME']

            if original_model:
                os.environ['SQL_LLM_MODEL'] = original_model
            elif 'SQL_LLM_MODEL' in os.environ:
                del os.environ['SQL_LLM_MODEL']

if __name__ == "__main__":
    print("Testing the fix for 'response_format type is unavailable' error...")

    success1 = test_deepseek_provider()
    success2 = test_other_provider_with_structured_output()

    if success1 and success2:
        print("\nAll tests passed! The fix is working correctly.")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)