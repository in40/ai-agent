#!/usr/bin/env python3
"""
Direct test of the parse_additional_databases_from_env function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from setup_config import parse_additional_databases_from_env

def test_parse_additional_databases():
    # Test content with additional databases
    env_content = """# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=postgres
DB_PASSWORD=secret
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=ai_agent_db
DATABASE_URL=postgresql://postgres:secret@localhost:5432/ai_agent_db

# Additional Database Configuration
DB_ANALYTICS_URL=postgresql://analytics_user:analytics_pass@analytics_host:5432/analytics_db
DB_ANALYTICS_TYPE=postgresql
DB_ANALYTICS_USERNAME=analytics_user
DB_ANALYTICS_PASSWORD=analytics_pass
DB_ANALYTICS_HOSTNAME=analytics_host
DB_ANALYTICS_PORT=5432
DB_ANALYTICS_NAME=analytics_db

DB_REPORTS_URL=mysql://reports_user:reports_pass@reports_host:3306/reports_db
DB_REPORTS_TYPE=mysql
DB_REPORTS_USERNAME=reports_user
DB_REPORTS_PASSWORD=reports_pass
DB_REPORTS_HOSTNAME=reports_host
DB_REPORTS_PORT=3306
DB_REPORTS_NAME=reports_db

# OpenAI API Key
OPENAI_API_KEY=test_key
"""

    print("Testing parse_additional_databases_from_env function...")
    print("Input content contains 2 additional databases: analytics and reports")
    
    additional_dbs = parse_additional_databases_from_env(env_content)
    
    print(f"Function returned {len(additional_dbs)} additional databases:")
    for db in additional_dbs:
        print(f"  - {db['name']}: {db['type']} database at {db['hostname']}:{db['port']}/{db['database_name']}")
    
    # Verify the results
    expected_names = {'analytics', 'reports'}
    actual_names = {db['name'] for db in additional_dbs}
    
    if expected_names == actual_names:
        print("\n✓ SUCCESS: Function correctly parsed both additional databases")
        return True
    else:
        print(f"\n✗ FAILURE: Expected {expected_names}, got {actual_names}")
        return False

def test_parse_additional_databases_individual_components():
    # Test content with additional databases defined by individual components
    env_content = """# Database Configuration
DB_TYPE=postgresql
DB_USERNAME=postgres
DB_PASSWORD=secret
DB_HOSTNAME=localhost
DB_PORT=5432
DB_NAME=ai_agent_db
DATABASE_URL=postgresql://postgres:secret@localhost:5432/ai_agent_db

# Additional Database Configuration (defined by individual components)
DB_WAREHOUSE_TYPE=postgresql
DB_WAREHOUSE_USERNAME=warehouse_user
DB_WAREHOUSE_PASSWORD=warehouse_pass
DB_WAREHOUSE_HOSTNAME=warehouse_host
DB_WAREHOUSE_PORT=5433
DB_WAREHOUSE_NAME=warehouse_db

# Another additional database defined by URL
DB_LOGS_URL=sqlite:////var/log/app/logs.db
DB_LOGS_TYPE=sqlite
DB_LOGS_USERNAME=
DB_LOGS_PASSWORD=
DB_LOGS_HOSTNAME=
DB_LOGS_PORT=0
DB_LOGS_NAME=logs

# OpenAI API Key
OPENAI_API_KEY=test_key
"""

    print("\nTesting parse_additional_databases_from_env function with individual components...")
    print("Input content contains 2 additional databases: warehouse (components) and logs (URL)")
    
    additional_dbs = parse_additional_databases_from_env(env_content)
    
    print(f"Function returned {len(additional_dbs)} additional databases:")
    for db in additional_dbs:
        print(f"  - {db['name']}: {db['type']} database at {db['hostname']}:{db['port']}/{db['database_name']}")
    
    # Verify the results
    expected_names = {'warehouse', 'logs'}
    actual_names = {db['name'] for db in additional_dbs}
    
    if expected_names == actual_names:
        print("\n✓ SUCCESS: Function correctly parsed both additional databases defined by different methods")
        return True
    else:
        print(f"\n✗ FAILURE: Expected {expected_names}, got {actual_names}")
        return False

if __name__ == "__main__":
    print("Testing the fix for additional database configuration parsing...")
    print("=" * 70)
    
    success1 = test_parse_additional_databases()
    success2 = test_parse_additional_databases_individual_components()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("✓ All tests passed! The fix for additional database configurations is working correctly.")
    else:
        print("✗ Some tests failed. The fix may need more work.")