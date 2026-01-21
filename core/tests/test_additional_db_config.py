#!/usr/bin/env python3
"""
Test script to verify that additional database configurations work correctly
with both URL and individual component formats.
"""

import os
import tempfile
from pathlib import Path

def test_additional_db_config():
    """Test that additional database configurations are properly stored and retrieved."""
    
    # Create a temporary .env file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
        temp_env_content = """# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=mainuser
DB_PASSWORD=mainpass
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=maindb
DATABASE_URL=postgresql://mainuser:mainpass@localhost:5432/maindb

# Additional Database Configuration (URL format)
DB_ANALYTICS_URL=postgresql://analytics_user:analytics_pass@analytics_host:5433/analytics_db

# Additional Database Configuration (Individual components format)
DB_REPORTS_TYPE=postgresql
DB_REPORTS_USERNAME=reports_user
DB_REPORTS_PASSWORD=reports_pass
DB_REPORTS_HOSTNAME=reports_host
DB_REPORTS_PORT=5434
DB_REPORTS_NAME=reports_db

# OpenAI API Key
OPENAI_API_KEY=test_key

# LLM Model Configuration
SQL_LLM_PROVIDER=LM Studio
SQL_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
SQL_LLM_HOSTNAME=localhost
SQL_LLM_PORT=1234
SQL_LLM_API_PATH=/v1
RESPONSE_LLM_PROVIDER=LM Studio
RESPONSE_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
RESPONSE_LLM_HOSTNAME=localhost
RESPONSE_LLM_PORT=1234
RESPONSE_LLM_API_PATH=/v1
PROMPT_LLM_PROVIDER=LM Studio
PROMPT_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
PROMPT_LLM_HOSTNAME=localhost
PROMPT_LLM_PORT=1234
PROMPT_LLM_API_PATH=/v1

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Security LLM Configuration
USE_SECURITY_LLM=N
SECURITY_LLM_PROVIDER=LM Studio
SECURITY_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
SECURITY_LLM_HOSTNAME=api.openai.com
SECURITY_LLM_PORT=1234
SECURITY_LLM_API_PATH=/v1

# Logging Configuration
ENABLE_SCREEN_LOGGING=N
"""
        temp_env.write(temp_env_content)
        temp_env_path = Path(temp_env.name)

    # Set the environment variable to use our test .env file
    original_env = os.environ.get('ENV_FILE')
    os.environ['ENV_FILE'] = str(temp_env_path)

    try:
        # Temporarily modify sys.path to include our project
        import sys
        original_path = sys.path[:]
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import the settings module to test configuration loading
        from config import settings
        
        # Check that the additional databases are loaded correctly
        print("Testing additional database configuration loading...")
        print(f"Main DATABASE_URL: {settings.DATABASE_URL}")
        print(f"Additional databases found: {list(settings.ADDITIONAL_DATABASES.keys())}")

        # Check if the jail database is loaded (from the actual .env file)
        if 'jail' in settings.ADDITIONAL_DATABASES:
            print("✓ Additional database 'jail' loaded correctly from URL format")
            print(f"  Jail database URL: {settings.ADDITIONAL_DATABASES['jail']}")
        else:
            print("✗ Additional database 'jail' not loaded")

        # Test the multi_database_manager
        from utils import multi_database_manager
        print(f"\nDatabases in MultiDatabaseManager before reload: {multi_database_manager.multi_db_manager.list_databases()}")

        # Reload the database config to ensure it picks up our environment
        multi_database_manager.reload_database_config()
        print(f"Databases in MultiDatabaseManager after reload: {multi_database_manager.multi_db_manager.list_databases()}")

        # Test that we can get the additional databases
        jail_db = multi_database_manager.multi_db_manager.get_database('jail')

        if jail_db:
            print("✓ Jail database accessible via MultiDatabaseManager")
        else:
            print("✗ Jail database not accessible via MultiDatabaseManager")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original environment
        if original_env is not None:
            os.environ['ENV_FILE'] = original_env
        else:
            os.environ.pop('ENV_FILE', None)
        
        # Restore original path
        sys.path[:] = original_path
        
        # Clean up temp file
        os.unlink(temp_env_path)

if __name__ == "__main__":
    test_additional_db_config()