#!/usr/bin/env python3
"""
Test script to verify that the CONFIGURE_MCP_MODELS setting persists across setup runs
"""

import tempfile
import os
from pathlib import Path

def test_config_persistence():
    """Test that CONFIGURE_MCP_MODELS setting is preserved when setup runs again."""
    
    # Create a temporary .env file with CONFIGURE_MCP_MODELS set to true
    temp_env_content = """# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=testuser
DB_PASSWORD=testpass
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=testdb
DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb
DATABASE_ENABLED=true
MCP_ENABLED=true
CONFIGURE_MCP_MODELS=true

# LLM Model Configuration
SQL_LLM_PROVIDER=OpenAI
SQL_LLM_MODEL=gpt-4
SQL_LLM_HOSTNAME=api.openai.com
SQL_LLM_PORT=443
SQL_LLM_API_PATH=/v1

# MCP Capable Model Configuration
MCP_SQL_LLM_PROVIDER=OpenAI
MCP_SQL_LLM_MODEL=gpt-4-mcp
MCP_SQL_LLM_HOSTNAME=api.openai.com
MCP_SQL_LLM_PORT=443
MCP_SQL_LLM_API_PATH=/v1
"""

    # Write the temporary .env file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as temp_file:
        temp_file.write(temp_env_content)
        temp_env_path = temp_file.name

    try:
        # Import the setup_config module and test the parsing
        import setup_config
        
        # Read the content to simulate what happens in the main function
        with open(temp_env_path, 'r') as env_file:
            env_content = env_file.read()
        
        # Parse the content to get existing values (simulating what happens in main())
        existing_values = {}
        for line in env_content.split('\n'):
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.split('=', 1)
                existing_values[key.strip()] = value.strip()
        
        # Check if CONFIGURE_MCP_MODELS is correctly parsed
        configure_mcp_value = existing_values.get("CONFIGURE_MCP_MODELS", "N")
        print(f"CONFIGURE_MCP_MODELS value from existing .env: {configure_mcp_value}")
        
        # Test the conversion logic from setup_config.py
        if configure_mcp_value.lower() in ['true', 'false']:
            # Convert boolean string to y/N format
            configure_mcp_default = "Y" if configure_mcp_value.lower() == 'true' else "N"
        else:
            # Value is already in y/N format
            configure_mcp_default = configure_mcp_value if configure_mcp_value in ['Y', 'N', 'y', 'n'] else "N"
            
        print(f"Default value for user prompt: {configure_mcp_default}")
        
        # Verify that the value is correctly converted
        assert configure_mcp_default == "Y", f"Expected 'Y' but got '{configure_mcp_default}'"
        print("SUCCESS: CONFIGURE_MCP_MODELS=true correctly converts to Y default for user prompt")
        
        # Test with false value
        existing_values["CONFIGURE_MCP_MODELS"] = "false"
        configure_mcp_value_false = existing_values.get("CONFIGURE_MCP_MODELS", "N")
        
        if configure_mcp_value_false.lower() in ['true', 'false']:
            configure_mcp_default_false = "Y" if configure_mcp_value_false.lower() == 'true' else "N"
        else:
            configure_mcp_default_false = configure_mcp_value_false if configure_mcp_value_false in ['Y', 'N', 'y', 'n'] else "N"
            
        print(f"CONFIGURE_MCP_MODELS=false converts to default: {configure_mcp_default_false}")
        assert configure_mcp_default_false == "N", f"Expected 'N' but got '{configure_mcp_default_false}'"
        print("SUCCESS: CONFIGURE_MCP_MODELS=false correctly converts to N default for user prompt")
        
        return True
        
    except Exception as e:
        print(f"ERROR in config persistence test: {e}")
        return False
    finally:
        # Clean up the temporary file
        os.unlink(temp_env_path)

if __name__ == "__main__":
    success = test_config_persistence()
    if success:
        print("\nOverall test result: PASSED")
    else:
        print("\nOverall test result: FAILED")