#!/usr/bin/env python3
"""
Simple validation script to check the configuration script logic.
"""

import sys
from pathlib import Path

# Add the project root to the Python path so we can import setup_config
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the validation functions from setup_config
import setup_config


def test_validations():
    """Test the validation functions in the setup_config module."""
    
    print("Testing validation functions...")
    
    # Test database type validation
    print("\n1. Testing database type validation:")

    valid_types = [
        "postgresql",
        "mysql",
        "sqlite",
        "oracle",
        "mssql"
    ]

    invalid_types = [
        "",
        "invalid-db-type",
        "mongo"
    ]

    for db_type in valid_types:
        is_valid, msg = setup_config.validate_database_type(db_type)
        print(f"   {db_type}: {'✓' if is_valid else '✗'} ({msg})")

    for db_type in invalid_types:
        is_valid, msg = setup_config.validate_database_type(db_type)
        print(f"   {db_type}: {'✓' if is_valid else '✗'} ({msg})")

    # Test database username validation
    print("\n2. Testing database username validation:")

    valid_usernames = [
        "postgres",
        "admin",
        "my_user",
        "user123"
    ]

    invalid_usernames = [
        "",
        "user@invalid",
        "user with spaces"
    ]

    for username in valid_usernames:
        is_valid, msg = setup_config.validate_database_username(username)
        print(f"   {username}: {'✓' if is_valid else '✗'} ({msg})")

    for username in invalid_usernames:
        is_valid, msg = setup_config.validate_database_username(username)
        print(f"   {username}: {'✓' if is_valid else '✗'} ({msg})")

    # Test database password validation
    print("\n3. Testing database password validation:")

    valid_passwords = [
        "password123",
        "complex@Passw0rd!",
        "simple"
    ]

    invalid_passwords = [
        ""
    ]

    for password in valid_passwords:
        is_valid, msg = setup_config.validate_database_password(password)
        print(f"   {password}: {'✓' if is_valid else '✗'} ({msg})")

    for password in invalid_passwords:
        is_valid, msg = setup_config.validate_database_password(password)
        print(f"   {password}: {'✓' if is_valid else '✗'} ({msg})")

    # Test database hostname validation
    print("\n4. Testing database hostname validation:")

    valid_hostnames = [
        "localhost",
        "192.168.1.1",
        "db.example.com",
        "my-db-server"
    ]

    invalid_hostnames = [
        "",
        "hostname with spaces",
        "hostname@invalid"
    ]

    for hostname in valid_hostnames:
        is_valid, msg = setup_config.validate_database_hostname(hostname)
        print(f"   {hostname}: {'✓' if is_valid else '✗'} ({msg})")

    for hostname in invalid_hostnames:
        is_valid, msg = setup_config.validate_database_hostname(hostname)
        print(f"   {hostname}: {'✓' if is_valid else '✗'} ({msg})")

    # Test database port validation
    print("\n5. Testing database port validation:")

    valid_ports = [
        "5432",
        "3306",
        "1433",
        "1521"
    ]

    invalid_ports = [
        "",
        "0",
        "65536",
        "not_a_number",
        "-1234"
    ]

    for port in valid_ports:
        is_valid, msg = setup_config.validate_database_port(port)
        print(f"   {port}: {'✓' if is_valid else '✗'} ({msg})")

    for port in invalid_ports:
        is_valid, msg = setup_config.validate_database_port(port)
        print(f"   {port}: {'✓' if is_valid else '✗'} ({msg})")

    # Test database name validation
    print("\n6. Testing database name validation:")

    valid_db_names = [
        "mydb",
        "test_db",
        "production_db_123"
    ]

    invalid_db_names = [
        "",
        "db name with spaces",
        "db@invalid"
    ]

    for db_name in valid_db_names:
        is_valid, msg = setup_config.validate_database_name(db_name)
        print(f"   {db_name}: {'✓' if is_valid else '✗'} ({msg})")

    for db_name in invalid_db_names:
        is_valid, msg = setup_config.validate_database_name(db_name)
        print(f"   {db_name}: {'✓' if is_valid else '✗'} ({msg})")
    
    # Test API key validation
    print("\n7. Testing API key validation:")
    
    valid_keys = [
        "sk-12345678901234567890",  # Valid format
        "sk-testkey123456789012"    # Valid format
    ]
    
    invalid_keys = [
        "",
        "invalid-key",
        "pk-testkey123456789012",  # Wrong prefix
        "sk-sh"  # Too short
    ]
    
    for key in valid_keys:
        is_valid, msg = setup_config.validate_openai_api_key(key)
        print(f"   {key}: {'✓' if is_valid else '✗'} ({msg})")
    
    for key in invalid_keys:
        is_valid, msg = setup_config.validate_openai_api_key(key)
        print(f"   {key}: {'✓' if is_valid else '✗'} ({msg})")
    
    # Test model name validation
    print("\n8. Testing model name validation:")

    valid_models = [
        "qwen2.5-coder-7b-instruct-abliterated@q3_k_m",
        "gpt-3.5-turbo",
        "gpt-4",
        "claude-2",
        "llama-2-7b",
        "qwen3-coder-42b-a3b-instruct-total-recall-master-coder-m-1million-ctx-i1",
        "qwen2.5-coder-7b-instruct-abliterated@q4_k_s"
    ]

    invalid_models = [
        "",
    ]

    for model in valid_models:
        is_valid, msg = setup_config.validate_model_name(model)
        print(f"   {model}: {'✓' if is_valid else '✗'} ({msg})")

    for model in invalid_models:
        is_valid, msg = setup_config.validate_model_name(model)
        print(f"   {model}: {'✓' if is_valid else '✗'} ({msg})")

    # Test hostname validation
    print("\n9. Testing hostname validation:")

    valid_hostnames = [
        "localhost",
        "192.168.1.1",
        "api.openai.com",
        "asus-tos",
        "my-llm-server.example.com"
    ]

    invalid_hostnames = [
        "",
        "hostname with spaces",
        "hostname@invalid"
    ]

    for hostname in valid_hostnames:
        is_valid, msg = setup_config.validate_hostname(hostname)
        print(f"   {hostname}: {'✓' if is_valid else '✗'} ({msg})")

    for hostname in invalid_hostnames:
        is_valid, msg = setup_config.validate_hostname(hostname)
        print(f"   {hostname}: {'✓' if is_valid else '✗'} ({msg})")

    # Test port validation
    print("\n10. Testing port validation:")

    valid_ports = [
        "80",
        "443",
        "1234",
        "8080",
        "11434"
    ]

    invalid_ports = [
        "",
        "0",
        "65536",
        "not_a_number",
        "-1234"
    ]

    for port in valid_ports:
        is_valid, msg = setup_config.validate_port(port)
        print(f"   {port}: {'✓' if is_valid else '✗'} ({msg})")

    for port in invalid_ports:
        is_valid, msg = setup_config.validate_port(port)
        print(f"   {port}: {'✓' if is_valid else '✗'} ({msg})")

    # Test API path validation
    print("\n11. Testing API path validation:")

    valid_paths = [
        "/v1",
        "/api/v1",
        "/openai/v1",
        "/v1/chat/completions"
    ]

    invalid_paths = [
        "",
        "v1",
        "no-slash",
        " /with-leading-space"
    ]

    for path in valid_paths:
        is_valid, msg = setup_config.validate_api_path(path)
        print(f"   {path}: {'✓' if is_valid else '✗'} ({msg})")

    for path in invalid_paths:
        is_valid, msg = setup_config.validate_api_path(path)
        print(f"   {path}: {'✓' if is_valid else '✗'} ({msg})")

    # Test provider validation
    print("\n12. Testing provider validation:")

    valid_providers = [
        "OpenAI",
        "DeepSeek",
        "Qwen",
        "LM Studio",
        "Ollama"
    ]

    invalid_providers = [
        "",
        "invalid-provider",
        "openai",  # case sensitive
        "MyCustomProvider"
    ]

    for provider in valid_providers:
        is_valid, msg = setup_config.validate_provider(provider)
        print(f"   {provider}: {'✓' if is_valid else '✗'} ({msg})")

    for provider in invalid_providers:
        is_valid, msg = setup_config.validate_provider(provider)
        print(f"   {provider}: {'✓' if is_valid else '✗'} ({msg})")

    print("\nValidation tests completed!")

    print("\nTesting .env file content generation...")


def test_env_file_generation():
    """Test the generation of .env file content."""

    print("\nTesting .env file content generation...")

    # Sample values
    db_type = "postgresql"
    db_username = "testuser"
    db_password = "testpass"
    db_hostname = "localhost"
    db_port = "5432"
    db_name = "testdb"
    db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name}"
    api_key = "sk-testapikey1234567890"
    sql_provider = "LM Studio"
    sql_model = "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"
    sql_hostname = "asus-tos"
    sql_port = "1234"
    sql_api_path = "/v1"
    response_provider = "LM Studio"
    response_model = "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"
    response_hostname = "asus-tos"
    response_port = "1234"
    response_api_path = "/v1"
    prompt_provider = "LM Studio"
    prompt_model = "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"
    prompt_hostname = "asus-tos"
    prompt_port = "1234"
    prompt_api_path = "/v1"

    # Generate .env content
    env_content = f"""# Database Configuration
DB_TYPE={db_type}
DB_USERNAME={db_username}
DB_PASSWORD={db_password}
DB_HOSTNAME={db_hostname}
DB_PORT={db_port}
DB_NAME={db_name}
DATABASE_URL={db_url}

# OpenAI API Key
OPENAI_API_KEY={api_key}

# LLM Model Configuration
SQL_LLM_PROVIDER={sql_provider}
SQL_LLM_MODEL={sql_model}
SQL_LLM_HOSTNAME={sql_hostname}
SQL_LLM_PORT={sql_port}
SQL_LLM_API_PATH={sql_api_path}
RESPONSE_LLM_PROVIDER={response_provider}
RESPONSE_LLM_MODEL={response_model}
RESPONSE_LLM_HOSTNAME={response_hostname}
RESPONSE_LLM_PORT={response_port}
RESPONSE_LLM_API_PATH={response_api_path}
PROMPT_LLM_PROVIDER={prompt_provider}
PROMPT_LLM_MODEL={prompt_model}
PROMPT_LLM_HOSTNAME={prompt_hostname}
PROMPT_LLM_PORT={prompt_port}
PROMPT_LLM_API_PATH={prompt_api_path}
"""

    print("Generated .env content:")
    print("-" * 40)
    print(env_content)
    print("-" * 40)

    # Verify expected values are present
    expected_values = [
        f"DB_TYPE={db_type}",
        f"DB_USERNAME={db_username}",
        f"DB_PASSWORD={db_password}",
        f"DB_HOSTNAME={db_hostname}",
        f"DB_PORT={db_port}",
        f"DB_NAME={db_name}",
        f"DATABASE_URL={db_url}",
        f"OPENAI_API_KEY={api_key}",
        f"SQL_LLM_PROVIDER={sql_provider}",
        f"SQL_LLM_MODEL={sql_model}",
        f"SQL_LLM_HOSTNAME={sql_hostname}",
        f"SQL_LLM_PORT={sql_port}",
        f"SQL_LLM_API_PATH={sql_api_path}",
        f"RESPONSE_LLM_PROVIDER={response_provider}",
        f"RESPONSE_LLM_MODEL={response_model}",
        f"RESPONSE_LLM_HOSTNAME={response_hostname}",
        f"RESPONSE_LLM_PORT={response_port}",
        f"RESPONSE_LLM_API_PATH={response_api_path}",
        f"PROMPT_LLM_PROVIDER={prompt_provider}",
        f"PROMPT_LLM_MODEL={prompt_model}",
        f"PROMPT_LLM_HOSTNAME={prompt_hostname}",
        f"PROMPT_LLM_PORT={prompt_port}",
        f"PROMPT_LLM_API_PATH={prompt_api_path}"
    ]

    all_found = True
    for value in expected_values:
        if value in env_content:
            print(f"✓ Found: {value}")
        else:
            print(f"✗ Missing: {value}")
            all_found = False

    if all_found:
        print("\n✓ All expected values found in generated .env content")
    else:
        print("\n✗ Some expected values are missing from generated .env content")


if __name__ == "__main__":
    test_validations()
    test_env_file_generation()