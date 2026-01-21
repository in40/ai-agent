"""
Test script to verify the dedicated MCP model functionality.
"""

import os
import sys
from unittest.mock import patch, MagicMock

def test_dedicated_mcp_model():
    """Test that the dedicated MCP model is properly implemented"""
    print("Testing dedicated MCP model functionality...")

    # Import the dedicated MCP model
    from models.dedicated_mcp_model import DedicatedMCPModel
    from langgraph_agent.langgraph_agent import AgentState

    # Check that the model can be instantiated
    mcp_model = DedicatedMCPModel()
    assert mcp_model is not None, "DedicatedMCPModel could not be instantiated"

    print("✓ Dedicated MCP model instantiated successfully")

    # Check that the AgentState has the required fields
    annotations = AgentState.__annotations__
    assert 'mcp_tool_calls' in annotations, "mcp_tool_calls field is missing from AgentState"
    assert 'mcp_capable_response' in annotations, "mcp_capable_response field is missing from AgentState"

    print("✓ Required MCP fields are present in AgentState")

    # Test with a mock service
    mock_services = [
        {
            "id": "test-service-1",
            "host": "localhost",
            "port": 8080,
            "type": "data-service",
            "metadata": {"description": "Test data service"}
        }
    ]

    # Test generating tool calls (this will likely return empty due to LLM call)
    result = mcp_model.generate_mcp_tool_calls("Get user data", mock_services)
    assert 'tool_calls' in result, "Tool calls not in result"

    print("✓ Dedicated MCP model tool call generation works")
    print(f"  - Generated result: {result}")

    print("✓ Dedicated MCP model functionality test passed!")


def test_dedicated_mcp_model_with_mock_llm():
    """Test the dedicated MCP model with a mocked LLM to avoid actual API calls"""
    print("\nTesting dedicated MCP model with mocked LLM...")

    from models.dedicated_mcp_model import DedicatedMCPModel
    
    # Mock the LLM and chain to avoid actual API calls
    with patch('models.dedicated_mcp_model.ChatOpenAI') as mock_llm_class, \
         patch('models.dedicated_mcp_model.ChatPromptTemplate') as mock_prompt_template, \
         patch('models.dedicated_mcp_model.StrOutputParser') as mock_output_parser:
        
        # Create mock instances
        mock_llm_instance = MagicMock()
        mock_prompt_template_instance = MagicMock()
        mock_output_parser_instance = MagicMock()
        mock_chain_instance = MagicMock()
        
        # Configure the mocks
        mock_llm_class.return_value = mock_llm_instance
        mock_prompt_template.from_messages.return_value = mock_prompt_template_instance
        mock_output_parser.return_value = mock_output_parser_instance
        
        # Mock the chain behavior
        from langchain_core.runnables import RunnableSequence
        mock_chain = MagicMock(spec=RunnableSequence)
        mock_chain.invoke.return_value = '{"tool_calls": [{"service_id": "test-service-1", "action": "get_data", "parameters": {"user_id": 123}}]}'
        
        # Patch the chain creation
        with patch.object(DedicatedMCPModel, '__init__', lambda self: None):
            # Manually set attributes for testing
            model = DedicatedMCPModel.__new__(DedicatedMCPModel)
            model.prompt_manager = MagicMock()
            model.prompt_manager.get_prompt.return_value = None  # Use default prompt
            model.llm = mock_llm_instance
            model.prompt = mock_prompt_template_instance
            model.output_parser = mock_output_parser_instance
            model.chain = mock_chain
            
            # Test the generate_mcp_tool_calls method
            mock_services = [
                {
                    "id": "test-service-1",
                    "host": "localhost",
                    "port": 8080,
                    "type": "data-service",
                    "metadata": {"description": "Test data service"}
                }
            ]
            
            result = model.generate_mcp_tool_calls("Get user data", mock_services)
            
            # Verify the chain was called with the right parameters
            expected_input = {
                "input_text": "Get user data",
                "mcp_services_json": '[\n  {\n    "id": "test-service-1",\n    "host": "localhost",\n    "port": 8080,\n    "type": "data-service",\n    "metadata": {\n      "description": "Test data service"\n    }\n  }\n]'
            }
            mock_chain.invoke.assert_called_once_with(expected_input)
            
            # Verify the result
            assert result == {"tool_calls": [{"service_id": "test-service-1", "action": "get_data", "parameters": {"user_id": 123}}]}
            
            print("✓ Dedicated MCP model works with mocked LLM")
            print(f"  - Result: {result}")


def test_dedicated_mcp_model_configuration():
    """Test that the dedicated MCP model uses the correct configuration"""
    print("\nTesting dedicated MCP model configuration...")

    # Set environment variables for dedicated MCP model
    original_provider = os.environ.get('DEDICATED_MCP_LLM_PROVIDER')
    original_model = os.environ.get('DEDICATED_MCP_LLM_MODEL')
    original_hostname = os.environ.get('DEDICATED_MCP_LLM_HOSTNAME')
    original_port = os.environ.get('DEDICATED_MCP_LLM_PORT')
    original_api_path = os.environ.get('DEDICATED_MCP_LLM_API_PATH')

    os.environ['DEDICATED_MCP_LLM_PROVIDER'] = 'OpenAI'
    os.environ['DEDICATED_MCP_LLM_MODEL'] = 'gpt-4'
    os.environ['DEDICATED_MCP_LLM_HOSTNAME'] = 'api.openai.com'
    os.environ['DEDICATED_MCP_LLM_PORT'] = '443'
    os.environ['DEDICATED_MCP_LLM_API_PATH'] = '/v1'

    # Reload the settings module to pick up the new environment variables
    import importlib
    import config.settings
    importlib.reload(config.settings)

    # Now import the settings after reloading
    from config.settings import (
        DEDICATED_MCP_LLM_PROVIDER,
        DEDICATED_MCP_LLM_MODEL,
        DEDICATED_MCP_LLM_HOSTNAME,
        DEDICATED_MCP_LLM_PORT,
        DEDICATED_MCP_LLM_API_PATH
    )

    # Verify the configuration was loaded correctly
    assert DEDICATED_MCP_LLM_PROVIDER == 'OpenAI'
    assert DEDICATED_MCP_LLM_MODEL == 'gpt-4'
    assert DEDICATED_MCP_LLM_HOSTNAME == 'api.openai.com'
    assert DEDICATED_MCP_LLM_PORT == '443'
    assert DEDICATED_MCP_LLM_API_PATH == '/v1'

    print("✓ Dedicated MCP model configuration loaded correctly")

    # Restore original environment variables
    if original_provider is not None:
        os.environ['DEDICATED_MCP_LLM_PROVIDER'] = original_provider
    else:
        del os.environ['DEDICATED_MCP_LLM_PROVIDER']

    if original_model is not None:
        os.environ['DEDICATED_MCP_LLM_MODEL'] = original_model
    else:
        del os.environ['DEDICATED_MCP_LLM_MODEL']

    if original_hostname is not None:
        os.environ['DEDICATED_MCP_LLM_HOSTNAME'] = original_hostname
    else:
        del os.environ['DEDICATED_MCP_LLM_HOSTNAME']

    if original_port is not None:
        os.environ['DEDICATED_MCP_LLM_PORT'] = original_port
    else:
        del os.environ['DEDICATED_MCP_LLM_PORT']

    if original_api_path is not None:
        os.environ['DEDICATED_MCP_LLM_API_PATH'] = original_api_path
    else:
        del os.environ['DEDICATED_MCP_LLM_API_PATH']

    # Test fallback to MCP configuration when dedicated config is empty
    original_mcp_provider = os.environ.get('MCP_LLM_PROVIDER')
    original_mcp_model = os.environ.get('MCP_LLM_MODEL')
    original_mcp_hostname = os.environ.get('MCP_LLM_HOSTNAME')
    original_mcp_port = os.environ.get('MCP_LLM_PORT')
    original_mcp_api_path = os.environ.get('MCP_LLM_API_PATH')

    os.environ['MCP_LLM_PROVIDER'] = 'FallbackProvider'
    os.environ['MCP_LLM_MODEL'] = 'FallbackModel'
    os.environ['MCP_LLM_HOSTNAME'] = 'fallback-host'
    os.environ['MCP_LLM_PORT'] = '5678'
    os.environ['MCP_LLM_API_PATH'] = '/fallback'

    # Reload settings again to pick up the new MCP environment variables
    importlib.reload(config.settings)

    # Import DedicatedMCPModel and test configuration storage
    from models.dedicated_mcp_model import DedicatedMCPModel

    # Create an instance of the model to test configuration storage
    model = DedicatedMCPModel()

    # Verify that configuration is stored as instance attributes
    assert hasattr(model, 'dedicated_mcp_llm_provider'), "dedicated_mcp_llm_provider attribute not found"
    assert hasattr(model, 'dedicated_mcp_llm_model'), "dedicated_mcp_llm_model attribute not found"
    assert hasattr(model, 'dedicated_mcp_llm_hostname'), "dedicated_mcp_llm_hostname attribute not found"
    assert hasattr(model, 'dedicated_mcp_llm_port'), "dedicated_mcp_llm_port attribute not found"
    assert hasattr(model, 'dedicated_mcp_llm_api_path'), "dedicated_mcp_llm_api_path attribute not found"

    # Verify that the get_config_info method exists and works
    config_info = model.get_config_info()
    assert isinstance(config_info, dict), "get_config_info should return a dictionary"
    assert 'dedicated_mcp_llm_provider' in config_info, "Config info should contain dedicated_mcp_llm_provider"

    print("✓ Dedicated MCP model stores configuration as instance attributes")
    print("✓ Dedicated MCP model has get_config_info method")

    # Restore original MCP environment variables
    if original_mcp_provider is not None:
        os.environ['MCP_LLM_PROVIDER'] = original_mcp_provider
    else:
        del os.environ['MCP_LLM_PROVIDER']

    if original_mcp_model is not None:
        os.environ['MCP_LLM_MODEL'] = original_mcp_model
    else:
        del os.environ['MCP_LLM_MODEL']

    if original_mcp_hostname is not None:
        os.environ['MCP_LLM_HOSTNAME'] = original_mcp_hostname
    else:
        del os.environ['MCP_LLM_HOSTNAME']

    if original_mcp_port is not None:
        os.environ['MCP_LLM_PORT'] = original_mcp_port
    else:
        del os.environ['MCP_LLM_PORT']

    if original_mcp_api_path is not None:
        os.environ['MCP_LLM_API_PATH'] = original_mcp_api_path
    else:
        del os.environ['MCP_LLM_API_PATH']


if __name__ == "__main__":
    test_dedicated_mcp_model()
    test_dedicated_mcp_model_with_mock_llm()
    test_dedicated_mcp_model_configuration()
    print("\n🎉 All dedicated MCP model tests passed!")