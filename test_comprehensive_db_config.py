#!/usr/bin/env python3
"""
Comprehensive test script to verify that additional database configurations work correctly
with both URL and individual component formats.
"""

import os
import tempfile
from pathlib import Path

def test_comprehensive_db_config():
    """Test that both URL and individual component formats work for additional databases."""
    
    # Create a temporary .env file for testing both formats
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as temp_env:
        temp_env_content = """# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=mainuser
DB_PASSWORD=mainpass
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=maindb
DATABASE_URL=postgresql://mainuser:mainpass@localhost:5432/maindb

# Additional Database Configuration (URL format only)
DB_ANALYTICS_URL=postgresql://analytics_user:analytics_pass@analytics_host:5433/analytics_db

# Additional Database Configuration (Individual components format)
DB_REPORTS_TYPE=postgresql
DB_REPORTS_USERNAME=reports_user
DB_REPORTS_PASSWORD=reports_pass
DB_REPORTS_HOSTNAME=reports_host
DB_REPORTS_PORT=5434
DB_REPORTS_NAME=reports_db

# Additional Database Configuration (Both URL and components)
DB_WAREHOUSE_TYPE=mysql
DB_WAREHOUSE_USERNAME=warehouse_user
DB_WAREHOUSE_PASSWORD=warehouse_pass
DB_WAREHOUSE_HOSTNAME=warehouse_host
DB_WAREHOUSE_PORT=3306
DB_WAREHOUSE_NAME=warehouse_db
DB_WAREHOUSE_URL=mysql://warehouse_user:warehouse_pass@warehouse_host:3306/warehouse_db

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

    # Backup the original .env file
    original_env_path = Path("test_env_backup")
    if Path(".env").exists():
        Path(".env").rename(original_env_path)

    try:
        # Copy our test .env file to the main location
        import shutil
        shutil.copy(temp_env_path, ".env")
        
        # Temporarily modify sys.path to include our project
        import sys
        original_path = sys.path[:]
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import the settings module to test configuration loading
        from config import settings
        
        print("Testing comprehensive additional database configuration loading...")
        print(f"Main DATABASE_URL: {settings.DATABASE_URL}")
        print(f"Additional databases found: {list(settings.ADDITIONAL_DATABASES.keys())}")
        
        # Verify that all databases are loaded correctly
        expected_dbs = {'analytics', 'reports', 'warehouse'}
        actual_dbs = set(settings.ADDITIONAL_DATABASES.keys())
        
        if expected_dbs.issubset(actual_dbs):
            print("✓ All additional databases are loaded correctly")
        else:
            print(f"✗ Missing databases. Expected: {expected_dbs}, Got: {actual_dbs}")
        
        # Check specific database URLs
        checks_passed = 0
        total_checks = 0
        
        # Analytics database (URL format)
        total_checks += 1
        if 'analytics' in settings.ADDITIONAL_DATABASES:
            expected_analytics_url = "postgresql://analytics_user:analytics_pass@analytics_host:5433/analytics_db"
            actual_analytics_url = settings.ADDITIONAL_DATABASES['analytics']
            if actual_analytics_url == expected_analytics_url:
                print("✓ Analytics database URL loaded correctly from URL format")
                checks_passed += 1
            else:
                print(f"✗ Analytics database URL mismatch. Expected: {expected_analytics_url}, Got: {actual_analytics_url}")
        else:
            print("✗ Analytics database not found")
        
        # Reports database (individual components format)
        total_checks += 1
        if 'reports' in settings.ADDITIONAL_DATABASES:
            expected_reports_url = "postgresql://reports_user:reports_pass@reports_host:5434/reports_db"
            actual_reports_url = settings.ADDITIONAL_DATABASES['reports']
            if actual_reports_url == expected_reports_url:
                print("✓ Reports database URL constructed correctly from components")
                checks_passed += 1
            else:
                print(f"✗ Reports database URL mismatch. Expected: {expected_reports_url}, Got: {actual_reports_url}")
        else:
            print("✗ Reports database not found")
        
        # Warehouse database (both URL and components - URL should take precedence)
        total_checks += 1
        if 'warehouse' in settings.ADDITIONAL_DATABASES:
            expected_warehouse_url = "mysql://warehouse_user:warehouse_pass@warehouse_host:3306/warehouse_db"
            actual_warehouse_url = settings.ADDITIONAL_DATABASES['warehouse']
            if actual_warehouse_url == expected_warehouse_url:
                print("✓ Warehouse database URL loaded correctly (URL takes precedence over components)")
                checks_passed += 1
            else:
                print(f"✗ Warehouse database URL mismatch. Expected: {expected_warehouse_url}, Got: {actual_warehouse_url}")
        else:
            print("✗ Warehouse database not found")
        
        # Test the multi_database_manager
        from utils import multi_database_manager
        print(f"\nReloading database configuration...")
        
        # Reload the database config to ensure it picks up our test environment
        multi_database_manager.reload_database_config()
        print(f"Databases in MultiDatabaseManager: {multi_database_manager.multi_db_manager.list_databases()}")
        
        # Test that we can get the additional databases
        analytics_db = multi_database_manager.multi_db_manager.get_database('analytics')
        reports_db = multi_database_manager.multi_db_manager.get_database('reports')
        warehouse_db = multi_database_manager.multi_db_manager.get_database('warehouse')
        
        additional_checks = 0
        total_additional_checks = 0
        
        total_additional_checks += 1
        if analytics_db:
            print("✓ Analytics database accessible via MultiDatabaseManager")
            additional_checks += 1
        else:
            print("✗ Analytics database not accessible via MultiDatabaseManager")
            
        total_additional_checks += 1
        if reports_db:
            print("✓ Reports database accessible via MultiDatabaseManager")
            additional_checks += 1
        else:
            print("✗ Reports database not accessible via MultiDatabaseManager")
            
        total_additional_checks += 1
        if warehouse_db:
            print("✓ Warehouse database accessible via MultiDatabaseManager")
            additional_checks += 1
        else:
            print("✗ Warehouse database not accessible via MultiDatabaseManager")
        
        print(f"\nTest Summary:")
        print(f"  Database URL checks: {checks_passed}/{total_checks} passed")
        print(f"  MultiDatabaseManager checks: {additional_checks}/{total_additional_checks} passed")
        
        if checks_passed == total_checks and additional_checks == total_additional_checks:
            print("\n🎉 All tests passed! Additional database configuration works correctly with both formats.")
        else:
            print(f"\n⚠️  Some tests failed. Please review the output above.")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original .env file
        if original_env_path.exists():
            original_env_path.rename(".env")
        
        # Restore original path
        sys.path[:] = original_path
        
        # Clean up temp file
        os.unlink(temp_env_path)

if __name__ == "__main__":
    test_comprehensive_db_config()