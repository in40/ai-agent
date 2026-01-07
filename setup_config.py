#!/usr/bin/env python3
"""
Configuration setup script for AI Agent.

This script will guide the user through setting up the required configuration
values and write them to the appropriate files.
"""

import os
import sys
from pathlib import Path
import getpass
import re


def get_user_input(prompt, default_value=None, sensitive=False, validator=None):
    """
    Get input from the user with an optional default value.
    For sensitive information like API keys, use getpass to hide input.
    """
    while True:
        if default_value:
            prompt_with_default = f"{prompt} (default: {default_value}): "
        else:
            prompt_with_default = f"{prompt}: "

        if sensitive:
            value = getpass.getpass(prompt_with_default)
        else:
            value = input(prompt_with_default)

        if value == "" and default_value is not None:
            value = default_value

        if validator:
            is_valid, error_msg = validator(value)
            if not is_valid:
                print(f"Error: {error_msg}")
                continue

        return value


def validate_database_username(username):
    """
    Basic validation for database username.
    """
    if not username:
        return False, "Database username cannot be empty"

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Database username contains invalid characters"

    return True, ""


def validate_database_password(password):
    """
    Basic validation for database password.
    """
    if not password:
        return False, "Database password cannot be empty"

    return True, ""


def validate_database_hostname(hostname):
    """
    Basic validation for database hostname.
    """
    if not hostname:
        return False, "Database hostname cannot be empty"

    # Simple validation for hostname format
    if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
        return False, "Database hostname contains invalid characters"

    return True, ""


def validate_database_port(port):
    """
    Basic validation for database port.
    """
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, "Database port must be between 1 and 65535"
    except ValueError:
        return False, "Database port must be a number"

    return True, ""


def validate_database_name(db_name):
    """
    Basic validation for database name.
    """
    if not db_name:
        return False, "Database name cannot be empty"

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', db_name):
        return False, "Database name contains invalid characters"

    return True, ""


def validate_database_type(db_type):
    """
    Basic validation for database type.
    """
    valid_types = ['postgresql', 'mysql', 'sqlite', 'oracle', 'mssql']
    if db_type not in valid_types:
        return False, f"Database type must be one of: {', '.join(valid_types)}"

    return True, ""


def validate_openai_api_key(api_key):
    """
    Basic validation for OpenAI API key format.
    """
    if not api_key:
        return False, "API key cannot be empty"

    # OpenAI API keys typically start with 'sk-' and are at least 20 characters
    if not api_key.startswith('sk-'):
        return False, "OpenAI API key should start with 'sk-'"

    if len(api_key) < 20:
        return False, "OpenAI API key should be at least 20 characters long"

    return True, ""


def validate_model_name(model_name):
    """
    Basic validation for model names.
    """
    if not model_name or model_name.strip() == "":
        return False, "Model name cannot be empty"

    # Allow all characters in model names to support complex model names
    return True, ""


def validate_hostname(hostname):
    """
    Basic validation for hostname.
    """
    if not hostname:
        return False, "Hostname cannot be empty"

    # Simple validation for hostname format
    if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
        return False, "Hostname contains invalid characters"

    return True, ""


def validate_port(port):
    """
    Basic validation for port.
    """
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Port must be a number"

    return True, ""


def validate_api_path(api_path):
    """
    Basic validation for API path.
    """
    if not api_path:
        return False, "API path cannot be empty"

    # Check if it starts with a slash
    if not api_path.startswith('/'):
        return False, "API path should start with '/'"

    return True, ""


def validate_provider(provider):
    """
    Basic validation for LLM provider.
    """
    valid_providers = ['OpenAI', 'DeepSeek', 'Qwen', 'LM Studio', 'Ollama', 'GigaChat']
    if provider not in valid_providers:
        return False, f"Provider must be one of: {', '.join(valid_providers)}"

    return True, ""


def validate_gigachat_credentials(credentials):
    """
    Basic validation for GigaChat credentials.
    """
    if not credentials:
        return False, "GigaChat credentials cannot be empty"

    # Basic check: credentials are usually longer strings
    if len(credentials) < 10:
        return False, "GigaChat credentials appear to be too short"

    return True, ""


def validate_oauth_token(token):
    """
    Basic validation for OAuth token.
    """
    if not token:
        return False, "OAuth token cannot be empty"

    # Basic check: tokens are usually longer strings
    if len(token) < 10:
        return False, "OAuth token appears to be too short"

    return True, ""


def main():
    print("AI Agent Configuration Setup")
    print("=" * 40)
    print("This script will help you configure the AI Agent application.")
    print("We'll collect the necessary settings and save them to the appropriate files.\n")

    # Get current directory
    project_root = Path(__file__).parent
    env_file_path = project_root / ".env"

    # Check if .env file already exists and load existing values if available
    existing_values = {}
    if env_file_path.exists():
        response = input(f".env file already exists at {env_file_path}. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Configuration setup cancelled.")
            sys.exit(0)

        # Try to read existing values to use as defaults
        try:
            with open(env_file_path, 'r') as env_file:
                for line in env_file:
                    if '=' in line:
                        key, value = line.split('=', 1)
                        existing_values[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not read existing .env file: {e}")

    # Collect configuration values
    print("\nDatabase Configuration:")
    print("-" * 20)
    db_type = get_user_input(
        "Enter your database type",
        default_value=existing_values.get("DB_TYPE", "postgresql"),
        validator=validate_database_type
    )

    db_username = get_user_input(
        "Enter your database username",
        default_value=existing_values.get("DB_USERNAME", "postgres"),
        validator=validate_database_username
    )

    db_password = get_user_input(
        "Enter your database password",
        default_value=existing_values.get("DB_PASSWORD", ""),  # Don't show password as default
        sensitive=True,
        validator=validate_database_password
    )

    db_hostname = get_user_input(
        "Enter your database hostname",
        default_value=existing_values.get("DB_HOSTNAME", "localhost"),
        validator=validate_database_hostname
    )

    db_port = get_user_input(
        "Enter your database port",
        default_value=existing_values.get("DB_PORT", "5432"),
        validator=validate_database_port
    )

    db_name = get_user_input(
        "Enter your database name",
        default_value=existing_values.get("DB_NAME", "ai_agent_db"),
        validator=validate_database_name
    )

    # Construct the database URL
    db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name}"

    print("\nOpenAI Configuration:")
    print("-" * 20)
    openai_api_key = get_user_input(
        "Enter your OpenAI API key (or leave empty if not using OpenAI)",
        default_value=existing_values.get("OPENAI_API_KEY", ""),
        sensitive=True,
        validator=validate_openai_api_key
    )

    print("\nGigaChat Configuration (optional):")
    print("-" * 30)
    gigachat_credentials = get_user_input(
        "Enter your GigaChat credentials (or leave empty if not using GigaChat)",
        default_value=existing_values.get("GIGACHAT_CREDENTIALS", ""),
        sensitive=True,
        validator=validate_gigachat_credentials
    )

    gigachat_scope = get_user_input(
        "Enter your GigaChat scope",
        default_value=existing_values.get("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        validator=lambda x: (True, "") if x in ["GIGACHAT_API_PERS", "GIGACHAT_API_B2B", "GIGACHAT_API_CORP"] else (False, "Scope must be one of: GIGACHAT_API_PERS, GIGACHAT_API_B2B, GIGACHAT_API_CORP")
    )

    gigachat_access_token = get_user_input(
        "Enter your GigaChat access token (or leave empty to use credentials)",
        default_value=existing_values.get("GIGACHAT_ACCESS_TOKEN", ""),
        sensitive=True,
        validator=lambda x: (True, "") if not x or len(x) >= 10 else (False, "Access token should be at least 10 characters or empty")
    )

    # Convert boolean values from existing config to y/N format for the default
    existing_ssl_value = existing_values.get("GIGACHAT_VERIFY_SSL_CERTS", "Y")
    if existing_ssl_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        ssl_default = "Y" if existing_ssl_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        ssl_default = existing_ssl_value if existing_ssl_value in ['Y', 'N', 'y', 'n'] else "Y"

    gigachat_verify_ssl_certs = get_user_input(
        "Verify SSL certificates for GigaChat? (Y/n)",
        default_value=ssl_default,
        validator=lambda x: (True, "") if x.lower() in ['y', 'n', 'yes', 'no'] else (False, "Please enter y or n")
    )

    print("\nLLM Model Configuration:")
    print("-" * 20)

    # SQL LLM Configuration
    sql_llm_provider = get_user_input(
        "Enter the provider for SQL generation LLM",
        default_value=existing_values.get("SQL_LLM_PROVIDER", "OpenAI"),
        validator=validate_provider
    )

    # Set default values based on provider for SQL LLM
    sql_defaults = {
        'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
        'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
        'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/api/v1'},
        'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
        'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/api/v1'},
        'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/api/v1'}
    }

    sql_default_hostname = sql_defaults[sql_llm_provider]['hostname']
    sql_default_port = sql_defaults[sql_llm_provider]['port']
    sql_default_api_path = sql_defaults[sql_llm_provider]['api_path']

    sql_llm_model = get_user_input(
        "Enter the model name for SQL generation",
        default_value=existing_values.get("SQL_LLM_MODEL", "gpt-3.5-turbo"),
        validator=validate_model_name
    )

    sql_llm_hostname = get_user_input(
        "Enter the hostname for SQL generation LLM",
        default_value=existing_values.get("SQL_LLM_HOSTNAME", sql_default_hostname),
        validator=validate_hostname
    )

    sql_llm_port = get_user_input(
        "Enter the port for SQL generation LLM",
        default_value=existing_values.get("SQL_LLM_PORT", sql_default_port),
        validator=validate_port
    )

    sql_llm_api_path = get_user_input(
        "Enter the API path for SQL generation LLM",
        default_value=existing_values.get("SQL_LLM_API_PATH", sql_default_api_path),
        validator=validate_api_path
    )

    # Response LLM Configuration
    response_llm_provider = get_user_input(
        "Enter the provider for response generation LLM",
        default_value=existing_values.get("RESPONSE_LLM_PROVIDER", "OpenAI"),
        validator=validate_provider
    )

    # Set default values based on provider for Response LLM
    response_defaults = {
        'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
        'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
        'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/v1'},
        'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
        'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/api/v1'},
        'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/api/v1'}
    }

    response_default_hostname = response_defaults[response_llm_provider]['hostname']
    response_default_port = response_defaults[response_llm_provider]['port']
    response_default_api_path = response_defaults[response_llm_provider]['api_path']

    response_llm_model = get_user_input(
        "Enter the model name for response generation",
        default_value=existing_values.get("RESPONSE_LLM_MODEL", "gpt-4"),
        validator=validate_model_name
    )

    response_llm_hostname = get_user_input(
        "Enter the hostname for response generation LLM",
        default_value=existing_values.get("RESPONSE_LLM_HOSTNAME", response_default_hostname),
        validator=validate_hostname
    )

    response_llm_port = get_user_input(
        "Enter the port for response generation LLM",
        default_value=existing_values.get("RESPONSE_LLM_PORT", response_default_port),
        validator=validate_port
    )

    response_llm_api_path = get_user_input(
        "Enter the API path for response generation LLM",
        default_value=existing_values.get("RESPONSE_LLM_API_PATH", response_default_api_path),
        validator=validate_api_path
    )

    # Prompt LLM Configuration
    prompt_llm_provider = get_user_input(
        "Enter the provider for prompt generation LLM",
        default_value=existing_values.get("PROMPT_LLM_PROVIDER", "OpenAI"),
        validator=validate_provider
    )

    # Set default values based on provider for Prompt LLM
    prompt_defaults = {
        'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
        'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
        'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/api/v1'},
        'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
        'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/api/v1'},
        'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/api/v1'}
    }

    prompt_default_hostname = prompt_defaults[prompt_llm_provider]['hostname']
    prompt_default_port = prompt_defaults[prompt_llm_provider]['port']
    prompt_default_api_path = prompt_defaults[prompt_llm_provider]['api_path']

    prompt_llm_model = get_user_input(
        "Enter the model name for prompt generation",
        default_value=existing_values.get("PROMPT_LLM_MODEL", "gpt-3.5-turbo"),
        validator=validate_model_name
    )

    prompt_llm_hostname = get_user_input(
        "Enter the hostname for prompt generation LLM",
        default_value=existing_values.get("PROMPT_LLM_HOSTNAME", prompt_default_hostname),
        validator=validate_hostname
    )

    prompt_llm_port = get_user_input(
        "Enter the port for prompt generation LLM",
        default_value=existing_values.get("PROMPT_LLM_PORT", prompt_default_port),
        validator=validate_port
    )

    prompt_llm_api_path = get_user_input(
        "Enter the API path for prompt generation LLM",
        default_value=existing_values.get("PROMPT_LLM_API_PATH", prompt_default_api_path),
        validator=validate_api_path
    )

    print("\nLogging Configuration:")
    print("-" * 20)
    # Convert boolean values from existing config to y/N format for the default
    existing_logging_value = existing_values.get("ENABLE_SCREEN_LOGGING", "N")
    if existing_logging_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        logging_default = "Y" if existing_logging_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        logging_default = existing_logging_value if existing_logging_value in ['Y', 'N', 'y', 'n'] else "N"

    enable_screen_logging = get_user_input(
        "Enable screen logging? (y/N)",
        default_value=logging_default,
        validator=lambda x: (True, "") if x.lower() in ['y', 'n', 'yes', 'no'] else (False, "Please enter y or n")
    )

    # Create .env file content
    env_content = f"""# Database Configuration
DB_TYPE={db_type}
DB_USERNAME={db_username}
DB_PASSWORD={db_password}
DB_HOSTNAME={db_hostname}
DB_PORT={db_port}
DB_NAME={db_name}
DATABASE_URL={db_url}

# OpenAI API Key
OPENAI_API_KEY={openai_api_key}

# GigaChat Configuration
GIGACHAT_CREDENTIALS={gigachat_credentials}
GIGACHAT_SCOPE={gigachat_scope}
GIGACHAT_ACCESS_TOKEN={gigachat_access_token}
GIGACHAT_VERIFY_SSL_CERTS={gigachat_verify_ssl_certs}

# LLM Model Configuration
SQL_LLM_PROVIDER={sql_llm_provider}
SQL_LLM_MODEL={sql_llm_model}
SQL_LLM_HOSTNAME={sql_llm_hostname}
SQL_LLM_PORT={sql_llm_port}
SQL_LLM_API_PATH={sql_llm_api_path}
RESPONSE_LLM_PROVIDER={response_llm_provider}
RESPONSE_LLM_MODEL={response_llm_model}
RESPONSE_LLM_HOSTNAME={response_llm_hostname}
RESPONSE_LLM_PORT={response_llm_port}
RESPONSE_LLM_API_PATH={response_llm_api_path}
PROMPT_LLM_PROVIDER={prompt_llm_provider}
PROMPT_LLM_MODEL={prompt_llm_model}
PROMPT_LLM_HOSTNAME={prompt_llm_hostname}
PROMPT_LLM_PORT={prompt_llm_port}
PROMPT_LLM_API_PATH={prompt_llm_api_path}

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Logging Configuration
ENABLE_SCREEN_LOGGING={enable_screen_logging}
"""

    # Write to .env file
    try:
        with open(env_file_path, 'w') as env_file:
            env_file.write(env_content)
        print(f"\nConfiguration saved to {env_file_path}")
    except Exception as e:
        print(f"Error writing to .env file: {e}")
        sys.exit(1)

    # Also update the .env.example file to reflect the new defaults (optional)
    example_env_path = project_root / ".env.example"
    try:
        example_env_content = f"""# Database Configuration
DB_TYPE={db_type}
DB_USERNAME={db_username}
DB_PASSWORD={db_password}
DB_HOSTNAME={db_hostname}
DB_PORT={db_port}
DB_NAME={db_name}
DATABASE_URL={db_url}

# OpenAI API Key
OPENAI_API_KEY={openai_api_key}

# GigaChat Configuration
GIGACHAT_CREDENTIALS={gigachat_credentials}
GIGACHAT_SCOPE={gigachat_scope}
GIGACHAT_ACCESS_TOKEN={gigachat_access_token}
GIGACHAT_VERIFY_SSL_CERTS=y

# LLM Model Configuration
SQL_LLM_PROVIDER={sql_llm_provider}
SQL_LLM_MODEL={sql_llm_model}
SQL_LLM_HOSTNAME={sql_llm_hostname}
SQL_LLM_PORT={sql_llm_port}
SQL_LLM_API_PATH={sql_llm_api_path}
RESPONSE_LLM_PROVIDER={response_llm_provider}
RESPONSE_LLM_MODEL={response_llm_model}
RESPONSE_LLM_HOSTNAME={response_llm_hostname}
RESPONSE_LLM_PORT={response_llm_port}
RESPONSE_LLM_API_PATH={response_llm_api_path}
PROMPT_LLM_PROVIDER={prompt_llm_provider}
PROMPT_LLM_MODEL={prompt_llm_model}
PROMPT_LLM_HOSTNAME={prompt_llm_hostname}
PROMPT_LLM_PORT={prompt_llm_port}
PROMPT_LLM_API_PATH={prompt_llm_api_path}

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Logging Configuration
ENABLE_SCREEN_LOGGING=N
"""
        with open(example_env_path, 'w') as example_file:
            example_file.write(example_env_content)
        print(f"Updated .env.example file with your configuration")
    except Exception as e:
        print(f"Warning: Could not update .env.example file: {e}")

    print("\nConfiguration completed successfully!")
    print("You can now run the AI Agent application.")
    print("\nTo run the application:")
    print(f"  python {project_root / 'main.py'}")
    print("\nFor help with command line options:")
    print(f"  python {project_root / 'main.py'} --help")


if __name__ == "__main__":
    main()