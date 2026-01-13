"""
Simple validation that the DeepSeek response_format fix is in place.
"""
import os
from unittest.mock import Mock, patch
from models.sql_generator import SQLGenerator

def validate_fix():
    """
    Validate that the fix for DeepSeek response_format error is properly implemented.
    """
    print("Validating the fix for DeepSeek response_format error...")
    
    # Set up environment for DeepSeek
    original_provider = os.environ.get('SQL_LLM_PROVIDER', '')
    original_hostname = os.environ.get('SQL_LLM_HOSTNAME', '')
    original_model = os.environ.get('SQL_LLM_MODEL', '')
    
    os.environ['SQL_LLM_PROVIDER'] = 'deepseek'
    os.environ['SQL_LLM_HOSTNAME'] = 'api.deepseek.com'
    os.environ['SQL_LLM_MODEL'] = 'deepseek-chat'
    
    try:
        # Mock the ChatOpenAI to prevent actual API calls
        with patch('models.sql_generator.ChatOpenAI') as mock_chat_openai:
            mock_llm_instance = Mock()
            mock_chat_openai.return_value = mock_llm_instance
            
            # Create the SQLGenerator
            sql_gen = SQLGenerator()
            
            # Verify that the fix is in place
            assert hasattr(sql_gen, 'use_structured_output'), "SQLGenerator should have use_structured_output attribute"
            assert sql_gen.use_structured_output is False, "DeepSeek should not use structured output to avoid response_format error"
            
            print("✓ DeepSeek provider correctly disables structured output")
            print("✓ This prevents the 'response_format type is unavailable' error")
            print("✓ The fix is properly implemented")
            
            return True
            
    except Exception as e:
        print(f"Validation failed with error: {e}")
        return False
    finally:
        # Restore environment
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
    success = validate_fix()
    if success:
        print("\n✓ Validation successful! The fix for DeepSeek response_format error is in place.")
    else:
        print("\n✗ Validation failed!")
        exit(1)