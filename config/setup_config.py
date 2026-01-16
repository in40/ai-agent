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


def get_user_input(prompt, default_value=None, sensitive=False, validator=None, is_db_password=False):
    """
    Get input from the user with an optional default value.
    For sensitive information like API keys, use getpass to hide input.
    is_db_password: If True, all characters of the password will be masked (not just after the first 5).
    """
    while True:
        if default_value:
            # Mask sensitive data in the default value display
            display_default = mask_sensitive_data(default_value, is_db_password) if sensitive else default_value
            prompt_with_default = f"{prompt} (default: {display_default}): "
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


def validate_brave_search_api_key(api_key):
    """
    Basic validation for Brave Search API key format.
    Brave Search API keys typically start with 'BSA' and have alphanumeric characters and underscores.
    """
    if not api_key:
        return False, "Brave Search API key cannot be empty"

    # Check if it looks like a valid API key (starts with BSA and has reasonable length)
    import re
    if not re.match(r'^BSA[a-zA-Z0-9_]{26,}$', api_key):  # At least 29 chars: BSA + 26+
        return False, "Brave Search API key should start with 'BSA' and contain alphanumeric characters and underscores"

    return True, ""


def validate_boolean_input(value):
    """
    Validation for boolean input (Y/N).
    """
    if value.lower() in ['y', 'n', 'yes', 'no']:
        return True, ""
    return False, "Please enter y or n"


def mask_sensitive_data(value, is_db_password=False):
    """
    Mask sensitive data.
    For database passwords: all characters are replaced with asterisks.
    For other sensitive data: show first 5 characters followed by asterisks.
    If the value is empty or None, return as is.
    """
    if not value:
        return value

    if is_db_password:
        # For database passwords, mask all characters
        return "*" * len(value)
    else:
        # For other sensitive data, show first 5 characters and mask the rest
        if len(value) <= 5:
            return "*" * len(value)

        # Show first 5 characters and mask the rest
        return value[:5] + "*" * (len(value) - 5)


def parse_additional_databases_from_env(env_content):
    """
    Parse additional database configurations from existing .env content.
    Returns a list of database configuration dictionaries.
    """
    additional_db_configs = []

    # Split the content into lines
    lines = env_content.split('\n')

    # Dictionary to hold all environment variables
    env_vars = {}
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()

    # Find all database names by looking for DB_{NAME}_URL or DB_{NAME}_TYPE patterns
    db_names = set()
    for key in env_vars.keys():
        if key.startswith('DB_') and (key.endswith('_URL') or '_TYPE' in key):
            db_name = None  # Initialize db_name

            # Extract the database name part
            if key.endswith('_URL'):
                db_name = key[3:-4]  # Remove "DB_" prefix and "_URL" suffix
            else:  # Contains _TYPE
                parts = key.split('_')
                if len(parts) >= 3:
                    db_name = '_'.join(parts[1:-1])  # Everything between "DB_" and "_TYPE"

            if db_name and db_name not in ['TYPE', 'USERNAME', 'PASSWORD', 'HOSTNAME', 'PORT', 'NAME']:
                db_names.add(db_name.lower())  # Use lowercase for consistency

    # For each database name, extract the configuration
    for db_name in db_names:
        db_name_upper = db_name.upper()

        # Check if it's defined by URL
        if f'DB_{db_name_upper}_URL' in env_vars:
            # If defined by URL, get the individual components by parsing the URL
            db_url = env_vars[f'DB_{db_name_upper}_URL']

            # Parse the URL to extract components
            import re
            # Handle different URL formats including sqlite with file paths
            if db_url.startswith('sqlite:///'):
                # Special handling for SQLite file paths
                db_type = 'sqlite'
                db_username = ''
                db_password = ''
                db_hostname = ''
                db_port = '0'
                db_name_db = db_url[len('sqlite:///'):]  # Get the file path
            else:
                url_match = re.match(r'(\w+)://([^:]*):([^@]*)@([^:]+):(\d+)/(.+)', db_url)
                if url_match:
                    db_type, db_username, db_password, db_hostname, db_port, db_name_db = url_match.groups()
                else:
                    # If the URL doesn't match the standard format, skip this entry
                    continue

            additional_db_configs.append({
                'name': db_name,
                'url': db_url,
                'type': db_type,
                'username': db_username,
                'password': db_password,
                'hostname': db_hostname,
                'port': db_port,
                'database_name': db_name_db
            })
        # Check if it's defined by individual components
        elif all(key in env_vars for key in [
            f'DB_{db_name_upper}_TYPE',
            f'DB_{db_name_upper}_USERNAME',
            f'DB_{db_name_upper}_NAME'
        ]):
            # Get individual components
            db_type = env_vars[f'DB_{db_name_upper}_TYPE']
            db_username = env_vars[f'DB_{db_name_upper}_USERNAME']
            db_password = env_vars.get(f'DB_{db_name_upper}_PASSWORD', '')
            db_hostname = env_vars.get(f'DB_{db_name_upper}_HOSTNAME', 'localhost')
            db_port = env_vars.get(f'DB_{db_name_upper}_PORT', '5432')
            db_name_db = env_vars[f'DB_{db_name_upper}_NAME']

            # Construct the URL
            db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name_db}"

            additional_db_configs.append({
                'name': db_name,
                'url': db_url,
                'type': db_type,
                'username': db_username,
                'password': db_password,
                'hostname': db_hostname,
                'port': db_port,
                'database_name': db_name_db
            })

    return additional_db_configs


def main():
    print("AI Agent Configuration Setup")
    print("=" * 40)
    print("This script will help you configure the AI Agent application.")
    print("We'll collect the necessary settings and save them to the appropriate files.\n")

    # Get project root directory (one level up from the config directory)
    project_root = Path(__file__).parent.parent
    env_file_path = project_root / ".env"

    # Check if .env file already exists and load existing values if available
    existing_values = {}
    additional_db_configs = []  # Initialize with empty list

    if env_file_path.exists():
        response = input(f".env file already exists at {env_file_path}. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Configuration setup cancelled.")
            sys.exit(0)

        # Try to read existing values to use as defaults
        try:
            with open(env_file_path, 'r') as env_file:
                env_content = env_file.read()

            # Parse the content to get existing values
            for line in env_content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    existing_values[key.strip()] = value.strip()

            # Parse additional database configurations from the existing .env file
            additional_db_configs = parse_additional_databases_from_env(env_content)

        except Exception as e:
            print(f"Warning: Could not read existing .env file: {e}")

    # Collect configuration values
    print("\nDefault Database Configuration:")
    print("-" * 30)
    print("This is the primary database that the application will use by default.")
    print("You can later add additional databases if needed.\n")

    db_type = get_user_input(
        "Enter your default database type",
        default_value=existing_values.get("DB_TYPE", "postgresql"),
        validator=validate_database_type
    )

    db_username = get_user_input(
        "Enter your default database username",
        default_value=existing_values.get("DB_USERNAME", "postgres"),
        validator=validate_database_username
    )

    db_password = get_user_input(
        "Enter your default database password",
        default_value=existing_values.get("DB_PASSWORD", ""),  # Don't show password as default
        sensitive=True,
        is_db_password=True,
        validator=validate_database_password
    )

    db_hostname = get_user_input(
        "Enter your default database hostname",
        default_value=existing_values.get("DB_HOSTNAME", "localhost"),
        validator=validate_database_hostname
    )

    db_port = get_user_input(
        "Enter your default database port",
        default_value=existing_values.get("DB_PORT", "5432"),
        validator=validate_database_port
    )

    db_name = get_user_input(
        "Enter your default database name",
        default_value=existing_values.get("DB_NAME", "ai_agent_db"),
        validator=validate_database_name
    )

    # Construct the database URL
    db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name}"

    # Ask if user wants to use this as the default database
    print("\nDefault Database Usage Configuration:")
    print("-" * 35)
    # Convert boolean values from existing config to y/N format for the default
    existing_default_db_enabled_value = existing_values.get("DEFAULT_DATABASE_ENABLED", "Y")
    if existing_default_db_enabled_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        default_db_enabled_default = "Y" if existing_default_db_enabled_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        default_db_enabled_default = existing_default_db_enabled_value if existing_default_db_enabled_value in ['Y', 'N', 'y', 'n'] else "Y"

    default_database_enabled_input = get_user_input(
        "Enable this as the default database? (Y/n)",
        default_value=default_db_enabled_default,
        validator=validate_boolean_input
    )

    # Convert user input to appropriate value for DEFAULT_DATABASE_ENABLED
    # Y (yes enable) should result in DEFAULT_DATABASE_ENABLED=true
    # N (no disable) should result in DEFAULT_DATABASE_ENABLED=false
    default_database_enabled = "true" if default_database_enabled_input.lower() in ['y', 'yes'] else "false"

    # Ask if user wants to configure additional databases
    print("\nAdditional Databases Configuration:")
    print("-" * 35)

    # Show existing additional databases if any
    if additional_db_configs:
        print(f"Found {len(additional_db_configs)} existing additional database configuration(s):")
        for db_config in additional_db_configs:
            # Mask password in the display
            masked_url = db_config['url'].replace(db_config['password'], mask_sensitive_data(db_config['password'], True))
            print(f"  - {db_config['name']}: {db_config['type']} database at {db_config['hostname']}:{db_config['port']}/{db_config['database_name']} (URL: {masked_url})")

    add_additional_dbs = get_user_input(
        "Do you want to configure additional databases? (y/n)",
        default_value="y" if additional_db_configs else "n"  # Default to 'y' if there are existing configs
    ).lower() in ['y', 'yes']

    if add_additional_dbs:
        while True:
            # Show existing databases and ask if user wants to modify them or add new ones
            if additional_db_configs:
                modify_existing = get_user_input(
                    f"Modify existing databases ({len(additional_db_configs)} found) or add new? (m/a)",
                    default_value="m"
                ).lower()

                if modify_existing == 'm':
                    # Let user select which database to modify or remove
                    print("Select database to modify or remove:")
                    for i, db_config in enumerate(additional_db_configs):
                        print(f"  {i+1}. {db_config['name']} ({db_config['type']} at {db_config['hostname']})")
                    print(f"  {len(additional_db_configs) + 1}. Add new database")
                    print(f"  {len(additional_db_configs) + 2}. Done")

                    choice = get_user_input(
                        f"Enter choice (1-{len(additional_db_configs) + 2})",
                        validator=lambda x: (x.isdigit() and 1 <= int(x) <= len(additional_db_configs) + 2,
                                           f"Please enter a number between 1 and {len(additional_db_configs) + 2}")
                    )
                    choice_num = int(choice)

                    if choice_num <= len(additional_db_configs):
                        # Modify existing database
                        idx = choice_num - 1
                        db_config = additional_db_configs[idx]

                        print(f"\nModifying database: {db_config['name']}")

                        # Ask for new values, using existing ones as defaults
                        db_name_input = get_user_input(
                            "Enter database name (used as identifier, e.g., 'analytics', 'reports')",
                            default_value=db_config['name'],
                            validator=lambda x: (bool(x and x.replace('_', '').replace('-', '').isalnum()),
                                               "Database name must be alphanumeric with optional underscores or hyphens")
                        )

                        db_type_input = get_user_input(
                            "Enter database type (postgresql, mysql, sqlite, etc.)",
                            default_value=db_config['type'],
                            validator=validate_database_type
                        )

                        db_username_input = get_user_input(
                            "Enter database username",
                            default_value=db_config['username'],
                            validator=validate_database_username
                        )

                        db_password_input = get_user_input(
                            "Enter database password",
                            default_value=db_config['password'],  # Show existing password as default
                            sensitive=True,
                            is_db_password=True,
                            validator=validate_database_password
                        )

                        db_hostname_input = get_user_input(
                            "Enter database hostname",
                            default_value=db_config['hostname'],
                            validator=validate_database_hostname
                        )

                        db_port_input = get_user_input(
                            "Enter database port",
                            default_value=db_config['port'],
                            validator=validate_database_port
                        )

                        db_name_db = get_user_input(
                            "Enter database name (actual database name)",
                            default_value=db_config['database_name'],
                            validator=validate_database_name
                        )

                        # Update the existing configuration
                        additional_db_url = f"{db_type_input}://{db_username_input}:{db_password_input}@{db_hostname_input}:{db_port_input}/{db_name_db}"

                        additional_db_configs[idx] = {
                            'name': db_name_input,
                            'url': additional_db_url,
                            'type': db_type_input,
                            'username': db_username_input,
                            'password': db_password_input,
                            'hostname': db_hostname_input,
                            'port': db_port_input,
                            'database_name': db_name_db
                        }

                        print(f"Updated database: {db_name_input}")

                    elif choice_num == len(additional_db_configs) + 1:
                        # Add new database
                        print("\nEnter details for new additional database:")
                        db_name_input = get_user_input(
                            "Enter database name (used as identifier, e.g., 'analytics', 'reports')",
                            validator=lambda x: (bool(x and x.replace('_', '').replace('-', '').isalnum()),
                                               "Database name must be alphanumeric with optional underscores or hyphens")
                        )

                        db_type_input = get_user_input(
                            "Enter database type (postgresql, mysql, sqlite, etc.)",
                            default_value="postgresql",
                            validator=validate_database_type
                        )

                        db_username_input = get_user_input(
                            "Enter database username",
                            default_value="postgres",
                            validator=validate_database_username
                        )

                        db_password_input = get_user_input(
                            "Enter database password",
                            sensitive=True,
                            validator=validate_database_password
                        )

                        db_hostname_input = get_user_input(
                            "Enter database hostname",
                            default_value="localhost",
                            validator=validate_database_hostname
                        )

                        db_port_input = get_user_input(
                            "Enter database port",
                            default_value="5432",
                            validator=validate_database_port
                        )

                        db_name_db = get_user_input(
                            "Enter database name (actual database name)",
                            validator=validate_database_name
                        )

                        # Construct the additional database URL
                        additional_db_url = f"{db_type_input}://{db_username_input}:{db_password_input}@{db_hostname_input}:{db_port_input}/{db_name_db}"

                        additional_db_configs.append({
                            'name': db_name_input,
                            'url': additional_db_url,
                            'type': db_type_input,
                            'username': db_username_input,
                            'password': db_password_input,
                            'hostname': db_hostname_input,
                            'port': db_port_input,
                            'database_name': db_name_db
                        })

                        print(f"Added database: {db_name_input}")

                    elif choice_num == len(additional_db_configs) + 2:
                        # Done
                        break
                else:
                    # Add new database option
                    print("\nEnter details for additional database:")
                    db_name_input = get_user_input(
                        "Enter database name (used as identifier, e.g., 'analytics', 'reports')",
                        validator=lambda x: (bool(x and x.replace('_', '').replace('-', '').isalnum()),
                                           "Database name must be alphanumeric with optional underscores or hyphens")
                    )

                    db_type_input = get_user_input(
                        "Enter database type (postgresql, mysql, sqlite, etc.)",
                        default_value="postgresql",
                        validator=validate_database_type
                    )

                    db_username_input = get_user_input(
                        "Enter database username",
                        default_value="postgres",
                        validator=validate_database_username
                    )

                    db_password_input = get_user_input(
                        "Enter database password",
                        sensitive=True,
                        is_db_password=True,
                        validator=validate_database_password
                    )

                    db_hostname_input = get_user_input(
                        "Enter database hostname",
                        default_value="localhost",
                        validator=validate_database_hostname
                    )

                    db_port_input = get_user_input(
                        "Enter database port",
                        default_value="5432",
                        validator=validate_database_port
                    )

                    db_name_db = get_user_input(
                        "Enter database name (actual database name)",
                        validator=validate_database_name
                    )

                    # Construct the additional database URL
                    additional_db_url = f"{db_type_input}://{db_username_input}:{db_password_input}@{db_hostname_input}:{db_port_input}/{db_name_db}"

                    additional_db_configs.append({
                        'name': db_name_input,
                        'url': additional_db_url,
                        'type': db_type_input,
                        'username': db_username_input,
                        'password': db_password_input,
                        'hostname': db_hostname_input,
                        'port': db_port_input,
                        'database_name': db_name_db
                    })

                    print(f"Added database: {db_name_input}")
            else:
                # No existing additional databases, just add new ones
                add_another = get_user_input(
                    "Add another database? (y/n)",
                    default_value="y"
                ).lower()

                if add_another not in ['y', 'yes']:
                    break

                print("\nEnter details for additional database:")
                db_name_input = get_user_input(
                    "Enter database name (used as identifier, e.g., 'analytics', 'reports')",
                    validator=lambda x: (bool(x and x.replace('_', '').replace('-', '').isalnum()),
                                       "Database name must be alphanumeric with optional underscores or hyphens")
                )

                db_type_input = get_user_input(
                    "Enter database type (postgresql, mysql, sqlite, etc.)",
                    default_value="postgresql",
                    validator=validate_database_type
                )

                db_username_input = get_user_input(
                    "Enter database username",
                    default_value="postgres",
                    validator=validate_database_username
                )

                db_password_input = get_user_input(
                    "Enter database password",
                    sensitive=True,
                    validator=validate_database_password
                )

                db_hostname_input = get_user_input(
                    "Enter database hostname",
                    default_value="localhost",
                    validator=validate_database_hostname
                )

                db_port_input = get_user_input(
                    "Enter database port",
                    default_value="5432",
                    validator=validate_database_port
                )

                db_name_db = get_user_input(
                    "Enter database name (actual database name)",
                    validator=validate_database_name
                )

                # Construct the additional database URL
                additional_db_url = f"{db_type_input}://{db_username_input}:{db_password_input}@{db_hostname_input}:{db_port_input}/{db_name_db}"

                additional_db_configs.append({
                    'name': db_name_input,
                    'url': additional_db_url,
                    'type': db_type_input,
                    'username': db_username_input,
                    'password': db_password_input,
                    'hostname': db_hostname_input,
                    'port': db_port_input,
                    'database_name': db_name_db
                })

                print(f"Added database: {db_name_input}")

    print("\nOpenAI Configuration:")
    print("-" * 20)
    openai_api_key = get_user_input(
        "Enter your OpenAI API key (or leave empty if not using OpenAI)",
        default_value=existing_values.get("OPENAI_API_KEY", ""),
        sensitive=True,
        validator=validate_openai_api_key
    )

    print("\nDeepSeek Configuration (optional):")
    print("-" * 30)
    deepseek_api_key = get_user_input(
        "Enter your DeepSeek API key (or leave empty if not using DeepSeek)",
        default_value=existing_values.get("DEEPSEEK_API_KEY", ""),
        sensitive=True,
        validator=validate_openai_api_key  # Using the same validation as OpenAI since they have similar format
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

    print("\nBrave Search Configuration (optional):")
    print("-" * 35)
    brave_search_api_key = get_user_input(
        "Enter your Brave Search API key (or leave empty if not using Brave Search)",
        default_value=existing_values.get("BRAVE_SEARCH_API_KEY", ""),
        sensitive=True,
        validator=validate_brave_search_api_key
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
        default_value=existing_values.get("SQL_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
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
        default_value=existing_values.get("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
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
        default_value=existing_values.get("PROMPT_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
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

    print("\nMCP Capable Model Configuration:")
    print("-" * 30)

    # Ask if user wants to configure MCP models separately
    # Convert boolean values from existing config to y/N format for the default
    existing_configure_mcp_value = existing_values.get("CONFIGURE_MCP_MODELS", "N")
    if existing_configure_mcp_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        configure_mcp_default = "Y" if existing_configure_mcp_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        configure_mcp_default = existing_configure_mcp_value if existing_configure_mcp_value in ['Y', 'N', 'y', 'n'] else "N"

    configure_mcp_models_input = get_user_input(
        "Configure MCP capable models separately? (y/N)",
        default_value=configure_mcp_default,
        validator=validate_boolean_input
    )
    configure_mcp_models = configure_mcp_models_input.lower() in ['y', 'yes']

    if configure_mcp_models:
        # MCP SQL LLM Configuration
        mcp_sql_llm_provider = get_user_input(
            "Enter the provider for MCP SQL generation LLM",
            default_value=existing_values.get("MCP_SQL_LLM_PROVIDER", "OpenAI"),
            validator=validate_provider
        )

        # Set default values based on provider for MCP SQL LLM
        mcp_sql_defaults = {
            'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
            'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
            'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/api/v1'},
            'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
            'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/api/v1'},
            'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/api/v1'}
        }

        mcp_sql_default_hostname = mcp_sql_defaults[mcp_sql_llm_provider]['hostname']
        mcp_sql_default_port = mcp_sql_defaults[mcp_sql_llm_provider]['port']
        mcp_sql_default_api_path = mcp_sql_defaults[mcp_sql_llm_provider]['api_path']

        mcp_sql_llm_model = get_user_input(
            "Enter the model name for MCP SQL generation",
            default_value=existing_values.get("MCP_SQL_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
            validator=validate_model_name
        )

        mcp_sql_llm_hostname = get_user_input(
            "Enter the hostname for MCP SQL generation LLM",
            default_value=existing_values.get("MCP_SQL_LLM_HOSTNAME", mcp_sql_default_hostname),
            validator=validate_hostname
        )

        mcp_sql_llm_port = get_user_input(
            "Enter the port for MCP SQL generation LLM",
            default_value=existing_values.get("MCP_SQL_LLM_PORT", mcp_sql_default_port),
            validator=validate_port
        )

        mcp_sql_llm_api_path = get_user_input(
            "Enter the API path for MCP SQL generation LLM",
            default_value=existing_values.get("MCP_SQL_LLM_API_PATH", mcp_sql_default_api_path),
            validator=validate_api_path
        )

        # MCP Response LLM Configuration
        mcp_response_llm_provider = get_user_input(
            "Enter the provider for MCP response generation LLM",
            default_value=existing_values.get("MCP_RESPONSE_LLM_PROVIDER", "OpenAI"),
            validator=validate_provider
        )

        # Set default values based on provider for MCP Response LLM
        mcp_response_defaults = {
            'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
            'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
            'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/v1'},
            'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
            'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/v1'},
            'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/v1'}
        }

        mcp_response_default_hostname = mcp_response_defaults[mcp_response_llm_provider]['hostname']
        mcp_response_default_port = mcp_response_defaults[mcp_response_llm_provider]['port']
        mcp_response_default_api_path = mcp_response_defaults[mcp_response_llm_provider]['api_path']

        mcp_response_llm_model = get_user_input(
            "Enter the model name for MCP response generation",
            default_value=existing_values.get("MCP_RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
            validator=validate_model_name
        )

        mcp_response_llm_hostname = get_user_input(
            "Enter the hostname for MCP response generation LLM",
            default_value=existing_values.get("MCP_RESPONSE_LLM_HOSTNAME", mcp_response_default_hostname),
            validator=validate_hostname
        )

        mcp_response_llm_port = get_user_input(
            "Enter the port for MCP response generation LLM",
            default_value=existing_values.get("MCP_RESPONSE_LLM_PORT", mcp_response_default_port),
            validator=validate_port
        )

        mcp_response_llm_api_path = get_user_input(
            "Enter the API path for MCP response generation LLM",
            default_value=existing_values.get("MCP_RESPONSE_LLM_API_PATH", mcp_response_default_api_path),
            validator=validate_api_path
        )

        # MCP Prompt LLM Configuration
        mcp_prompt_llm_provider = get_user_input(
            "Enter the provider for MCP prompt generation LLM",
            default_value=existing_values.get("MCP_PROMPT_LLM_PROVIDER", "OpenAI"),
            validator=validate_provider
        )

        # Set default values based on provider for MCP Prompt LLM
        mcp_prompt_defaults = {
            'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
            'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
            'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/api/v1'},
            'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
            'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/v1'},
            'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/v1'}
        }

        mcp_prompt_default_hostname = mcp_prompt_defaults[mcp_prompt_llm_provider]['hostname']
        mcp_prompt_default_port = mcp_prompt_defaults[mcp_prompt_llm_provider]['port']
        mcp_prompt_default_api_path = mcp_prompt_defaults[mcp_prompt_llm_provider]['api_path']

        mcp_prompt_llm_model = get_user_input(
            "Enter the model name for MCP prompt generation",
            default_value=existing_values.get("MCP_PROMPT_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
            validator=validate_model_name
        )

        mcp_prompt_llm_hostname = get_user_input(
            "Enter the hostname for MCP prompt generation LLM",
            default_value=existing_values.get("MCP_PROMPT_LLM_HOSTNAME", mcp_prompt_default_hostname),
            validator=validate_hostname
        )

        mcp_prompt_llm_port = get_user_input(
            "Enter the port for MCP prompt generation LLM",
            default_value=existing_values.get("MCP_PROMPT_LLM_PORT", mcp_prompt_default_port),
            validator=validate_port
        )

        mcp_prompt_llm_api_path = get_user_input(
            "Enter the API path for MCP prompt generation LLM",
            default_value=existing_values.get("MCP_PROMPT_LLM_API_PATH", mcp_prompt_default_api_path),
            validator=validate_api_path
        )
    else:
        # If not configuring MCP models separately, use the same as regular models
        mcp_sql_llm_provider = sql_llm_provider
        mcp_sql_llm_model = sql_llm_model
        mcp_sql_llm_hostname = sql_llm_hostname
        mcp_sql_llm_port = sql_llm_port
        mcp_sql_llm_api_path = sql_llm_api_path

        mcp_response_llm_provider = response_llm_provider
        mcp_response_llm_model = response_llm_model
        mcp_response_llm_hostname = response_llm_hostname
        mcp_response_llm_port = response_llm_port
        mcp_response_llm_api_path = response_llm_api_path

        mcp_prompt_llm_provider = prompt_llm_provider
        mcp_prompt_llm_model = prompt_llm_model
        mcp_prompt_llm_hostname = prompt_llm_hostname
        mcp_prompt_llm_port = prompt_llm_port
        mcp_prompt_llm_api_path = prompt_llm_api_path

    print("\nDedicated MCP Model Configuration:")
    print("-" * 35)

    # Ask if user wants to configure dedicated MCP model separately
    existing_dedicated_mcp_value = existing_values.get("DEDICATED_MCP_LLM_PROVIDER", "")
    has_dedicated_config = bool(existing_dedicated_mcp_value)

    dedicated_mcp_enabled_input = get_user_input(
        "Configure dedicated model for MCP-specific tasks? (y/N)",
        default_value="y" if has_dedicated_config else "n"
    ).lower() in ['y', 'yes']

    if dedicated_mcp_enabled_input:
        # Dedicated MCP LLM Configuration
        dedicated_mcp_llm_provider = get_user_input(
            "Enter the provider for dedicated MCP LLM",
            default_value=existing_values.get("DEDICATED_MCP_LLM_PROVIDER", "LM Studio"),
            validator=validate_provider
        )

        # Set default values based on provider for Dedicated MCP LLM
        dedicated_mcp_defaults = {
            'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
            'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
            'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/v1'},
            'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
            'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/v1'},
            'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/v1'}
        }

        dedicated_mcp_default_hostname = dedicated_mcp_defaults[dedicated_mcp_llm_provider]['hostname']
        dedicated_mcp_default_port = dedicated_mcp_defaults[dedicated_mcp_llm_provider]['port']
        dedicated_mcp_default_api_path = dedicated_mcp_defaults[dedicated_mcp_llm_provider]['api_path']

        dedicated_mcp_llm_model = get_user_input(
            "Enter the model name for dedicated MCP tasks",
            default_value=existing_values.get("DEDICATED_MCP_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
            validator=validate_model_name
        )

        dedicated_mcp_llm_hostname = get_user_input(
            "Enter the hostname for dedicated MCP LLM",
            default_value=existing_values.get("DEDICATED_MCP_LLM_HOSTNAME", dedicated_mcp_default_hostname),
            validator=validate_hostname
        )

        dedicated_mcp_llm_port = get_user_input(
            "Enter the port for dedicated MCP LLM",
            default_value=existing_values.get("DEDICATED_MCP_LLM_PORT", dedicated_mcp_default_port),
            validator=validate_port
        )

        dedicated_mcp_llm_api_path = get_user_input(
            "Enter the API path for dedicated MCP LLM",
            default_value=existing_values.get("DEDICATED_MCP_LLM_API_PATH", dedicated_mcp_default_api_path),
            validator=validate_api_path
        )
    else:
        # If not configuring dedicated MCP model, set values to empty
        dedicated_mcp_llm_provider = ""
        dedicated_mcp_llm_model = ""
        dedicated_mcp_llm_hostname = ""
        dedicated_mcp_llm_port = ""
        dedicated_mcp_llm_api_path = ""

    print("\nSecurity Configuration:")
    print("-" * 20)
    # Convert boolean values from existing config to y/N format for the default
    existing_security_value = existing_values.get("USE_SECURITY_LLM", "Y")
    if existing_security_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        security_default = "Y" if existing_security_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        security_default = existing_security_value if existing_security_value in ['Y', 'N', 'y', 'n'] else "Y"

    use_security_llm = get_user_input(
        "Use advanced security LLM for SQL analysis? (Y/n)",
        default_value=security_default,
        validator=lambda x: (True, "") if x.lower() in ['y', 'n', 'yes', 'no'] else (False, "Please enter y or n")
    )

    # Security LLM Configuration (only if security LLM is enabled)
    if use_security_llm.lower() in ['y', 'yes']:
        security_llm_provider = get_user_input(
            "Enter the provider for security LLM",
            default_value=existing_values.get("SECURITY_LLM_PROVIDER", "OpenAI"),
            validator=validate_provider
        )

        # Set default values based on provider for Security LLM
        security_defaults = {
            'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
            'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
            'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/v1'},
            'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
            'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/api/v1'},
            'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/api/v1'}
        }

        security_default_hostname = security_defaults[security_llm_provider]['hostname']
        security_default_port = security_defaults[security_llm_provider]['port']
        security_default_api_path = security_defaults[security_llm_provider]['api_path']

        security_llm_model = get_user_input(
            "Enter the model name for security analysis",
            default_value=existing_values.get("SECURITY_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
            validator=validate_model_name
        )

        security_llm_hostname = get_user_input(
            "Enter the hostname for security LLM",
            default_value=existing_values.get("SECURITY_LLM_HOSTNAME", security_default_hostname),
            validator=validate_hostname
        )

        security_llm_port = get_user_input(
            "Enter the port for security LLM",
            default_value=existing_values.get("SECURITY_LLM_PORT", security_default_port),
            validator=validate_port
        )

        security_llm_api_path = get_user_input(
            "Enter the API path for security LLM",
            default_value=existing_values.get("SECURITY_LLM_API_PATH", security_default_api_path),
            validator=validate_api_path
        )
    else:
        # Set default values when security LLM is disabled
        security_llm_provider = "OpenAI"
        security_llm_model = "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"
        security_llm_hostname = "api.openai.com"
        security_llm_port = "443"
        security_llm_api_path = "/v1"

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
        validator=validate_boolean_input
    )

    print("\nDatabase Usage Configuration:")
    print("-" * 20)
    # Convert boolean values from existing config to y/N format for the default
    existing_db_enabled_value = existing_values.get("DATABASE_ENABLED", "Y")
    if existing_db_enabled_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        db_enabled_default = "Y" if existing_db_enabled_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        db_enabled_default = existing_db_enabled_value if existing_db_enabled_value in ['Y', 'N', 'y', 'n'] else "Y"

    database_enabled_input = get_user_input(
        "Enable database usage? (Y/n)",
        default_value=db_enabled_default,
        validator=validate_boolean_input
    )

    # Fix the inverted logic: when user enters Y/N, convert to appropriate value for DATABASE_ENABLED
    # Y (yes enable) should result in DATABASE_ENABLED=true
    # N (no disable) should result in DATABASE_ENABLED=false
    database_enabled = "true" if database_enabled_input.lower() in ['y', 'yes'] else "false"

    print("\nDefault LLM Model Configuration:")
    print("-" * 30)
    print("Configure the default LLM model settings that will be used across the application.")
    print("Specific model configurations (SQL, Response, Prompt) will inherit from these defaults unless overridden.\n")

    # Default LLM Configuration
    default_llm_provider = get_user_input(
        "Enter the default provider for LLM models",
        default_value=existing_values.get("DEFAULT_LLM_PROVIDER", "LM Studio"),
        validator=validate_provider
    )

    # Set default values based on provider for Default LLM
    default_llm_defaults = {
        'OpenAI': {'hostname': 'api.openai.com', 'port': '443', 'api_path': '/v1'},
        'DeepSeek': {'hostname': 'api.deepseek.com', 'port': '443', 'api_path': '/v1'},
        'Qwen': {'hostname': 'dashscope.aliyuncs.com', 'port': '443', 'api_path': '/v1'},
        'LM Studio': {'hostname': 'localhost', 'port': '1234', 'api_path': '/v1'},
        'Ollama': {'hostname': 'localhost', 'port': '11434', 'api_path': '/v1'},
        'GigaChat': {'hostname': 'gigachat.devices.sberbank.ru', 'port': '443', 'api_path': '/v1'}
    }

    default_llm_default_hostname = default_llm_defaults[default_llm_provider]['hostname']
    default_llm_default_port = default_llm_defaults[default_llm_provider]['port']
    default_llm_default_api_path = default_llm_defaults[default_llm_provider]['api_path']

    default_llm_model = get_user_input(
        "Enter the default model name",
        default_value=existing_values.get("DEFAULT_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m"),
        validator=validate_model_name
    )

    default_llm_hostname = get_user_input(
        "Enter the default hostname for LLM models",
        default_value=existing_values.get("DEFAULT_LLM_HOSTNAME", default_llm_default_hostname),
        validator=validate_hostname
    )

    default_llm_port = get_user_input(
        "Enter the default port for LLM models",
        default_value=existing_values.get("DEFAULT_LLM_PORT", default_llm_default_port),
        validator=validate_port
    )

    default_llm_api_path = get_user_input(
        "Enter the default API path for LLM models",
        default_value=existing_values.get("DEFAULT_LLM_API_PATH", default_llm_default_api_path),
        validator=validate_api_path
    )

    print("\nMCP (Model Context Protocol) Usage Configuration:")
    print("-" * 20)
    # Convert boolean values from existing config to y/N format for the default
    existing_mcp_enabled_value = existing_values.get("MCP_ENABLED", "Y")
    if existing_mcp_enabled_value.lower() in ['true', 'false']:
        # Convert boolean string to y/N format
        mcp_enabled_default = "Y" if existing_mcp_enabled_value.lower() == 'true' else "N"
    else:
        # Value is already in y/N format
        mcp_enabled_default = existing_mcp_enabled_value if existing_mcp_enabled_value in ['Y', 'N', 'y', 'n'] else "Y"

    mcp_enabled_input = get_user_input(
        "Enable MCP (Model Context Protocol) usage? (Y/n)",
        default_value=mcp_enabled_default,
        validator=validate_boolean_input
    )

    # Convert user input to appropriate value for MCP_ENABLED
    # Y (yes enable) should result in MCP_ENABLED=true
    # N (no disable) should result in MCP_ENABLED=false
    mcp_enabled = "true" if mcp_enabled_input.lower() in ['y', 'yes'] else "false"

    # Convert configure_mcp_models to appropriate value for CONFIGURE_MCP_MODELS
    # Y (yes enable) should result in CONFIGURE_MCP_MODELS=true
    # N (no disable) should result in CONFIGURE_MCP_MODELS=false
    configure_mcp_models_value = "true" if configure_mcp_models_input.lower() in ['y', 'yes'] else "false"

    # Create .env file content
    env_content = f"""# Database Configuration
DB_TYPE={db_type}
DB_USERNAME={db_username}
DB_PASSWORD={db_password}
DB_HOSTNAME={db_hostname}
DB_PORT={db_port}
DB_NAME={db_name}
DATABASE_URL={db_url}
DEFAULT_DATABASE_ENABLED={default_database_enabled}
DATABASE_ENABLED={database_enabled}
MCP_ENABLED={mcp_enabled}
CONFIGURE_MCP_MODELS={configure_mcp_models_value}

# Default LLM Model Configuration
DEFAULT_LLM_PROVIDER={default_llm_provider}
DEFAULT_LLM_MODEL={default_llm_model}
DEFAULT_LLM_HOSTNAME={default_llm_hostname}
DEFAULT_LLM_PORT={default_llm_port}
DEFAULT_LLM_API_PATH={default_llm_api_path}
"""

    # Add additional database configurations to the .env file
    for db_config in additional_db_configs:
        db_name_upper = db_config['name'].upper()
        env_content += f"DB_{db_name_upper}_URL={db_config['url']}\n"
        env_content += f"DB_{db_name_upper}_TYPE={db_config['type']}\n"
        env_content += f"DB_{db_name_upper}_USERNAME={db_config['username']}\n"
        env_content += f"DB_{db_name_upper}_PASSWORD={db_config['password']}\n"
        env_content += f"DB_{db_name_upper}_HOSTNAME={db_config['hostname']}\n"
        env_content += f"DB_{db_name_upper}_PORT={db_config['port']}\n"
        env_content += f"DB_{db_name_upper}_NAME={db_config['database_name']}\n"

    env_content += f"""
# OpenAI API Key
OPENAI_API_KEY={openai_api_key}

# DeepSeek API Key
DEEPSEEK_API_KEY={deepseek_api_key}

# GigaChat Configuration
GIGACHAT_CREDENTIALS={gigachat_credentials}
GIGACHAT_SCOPE={gigachat_scope}
GIGACHAT_ACCESS_TOKEN={gigachat_access_token}
GIGACHAT_VERIFY_SSL_CERTS={gigachat_verify_ssl_certs}

# Brave Search API Key
BRAVE_SEARCH_API_KEY={brave_search_api_key}

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

# MCP Capable Model Configuration
MCP_SQL_LLM_PROVIDER={mcp_sql_llm_provider}
MCP_SQL_LLM_MODEL={mcp_sql_llm_model}
MCP_SQL_LLM_HOSTNAME={mcp_sql_llm_hostname}
MCP_SQL_LLM_PORT={mcp_sql_llm_port}
MCP_SQL_LLM_API_PATH={mcp_sql_llm_api_path}
MCP_RESPONSE_LLM_PROVIDER={mcp_response_llm_provider}
MCP_RESPONSE_LLM_MODEL={mcp_response_llm_model}
MCP_RESPONSE_LLM_HOSTNAME={mcp_response_llm_hostname}
MCP_RESPONSE_LLM_PORT={mcp_response_llm_port}
MCP_RESPONSE_LLM_API_PATH={mcp_response_llm_api_path}
MCP_PROMPT_LLM_PROVIDER={mcp_prompt_llm_provider}
MCP_PROMPT_LLM_MODEL={mcp_prompt_llm_model}
MCP_PROMPT_LLM_HOSTNAME={mcp_prompt_llm_hostname}
MCP_PROMPT_LLM_PORT={mcp_prompt_llm_port}
MCP_PROMPT_LLM_API_PATH={mcp_prompt_llm_api_path}

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Security LLM Configuration (for advanced SQL security analysis)
# Whether to use the security LLM for analysis (set to false to use basic keyword matching only)
USE_SECURITY_LLM={use_security_llm}
SECURITY_LLM_PROVIDER={security_llm_provider}
SECURITY_LLM_MODEL={security_llm_model}
SECURITY_LLM_HOSTNAME={security_llm_hostname}
SECURITY_LLM_PORT={security_llm_port}
SECURITY_LLM_API_PATH={security_llm_api_path}

# Dedicated MCP Model Configuration (separate model specifically for MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER={dedicated_mcp_llm_provider}
DEDICATED_MCP_LLM_MODEL={dedicated_mcp_llm_model}
DEDICATED_MCP_LLM_HOSTNAME={dedicated_mcp_llm_hostname}
DEDICATED_MCP_LLM_PORT={dedicated_mcp_llm_port}
DEDICATED_MCP_LLM_API_PATH={dedicated_mcp_llm_api_path}

# Logging Configuration
ENABLE_SCREEN_LOGGING={enable_screen_logging}
"""

    # Create a masked version of the content for display purposes
    masked_env_content = f"""# Database Configuration
DB_TYPE={db_type}
DB_USERNAME={db_username}
DB_PASSWORD={mask_sensitive_data(db_password, True)}
DB_HOSTNAME={db_hostname}
DB_PORT={db_port}
DB_NAME={db_name}
DATABASE_URL={db_url.replace(db_password, mask_sensitive_data(db_password, True))}
DEFAULT_DATABASE_ENABLED={default_database_enabled}
DATABASE_ENABLED={database_enabled}
MCP_ENABLED={mcp_enabled}
CONFIGURE_MCP_MODELS={configure_mcp_models_value}

# Default LLM Model Configuration
DEFAULT_LLM_PROVIDER={default_llm_provider}
DEFAULT_LLM_MODEL={default_llm_model}
DEFAULT_LLM_HOSTNAME={default_llm_hostname}
DEFAULT_LLM_PORT={default_llm_port}
DEFAULT_LLM_API_PATH={default_llm_api_path}
"""

    # Add additional database configurations to the masked .env file
    for db_config in additional_db_configs:
        db_name_upper = db_config['name'].upper()
        masked_db_url = db_config['url'].replace(db_config['password'], mask_sensitive_data(db_config['password'], True))
        masked_env_content += f"DB_{db_name_upper}_URL={masked_db_url}\n"
        masked_env_content += f"DB_{db_name_upper}_TYPE={db_config['type']}\n"
        masked_env_content += f"DB_{db_name_upper}_USERNAME={db_config['username']}\n"
        masked_env_content += f"DB_{db_name_upper}_PASSWORD={mask_sensitive_data(db_config['password'], True)}\n"
        masked_env_content += f"DB_{db_name_upper}_HOSTNAME={db_config['hostname']}\n"
        masked_env_content += f"DB_{db_name_upper}_PORT={db_config['port']}\n"
        masked_env_content += f"DB_{db_name_upper}_NAME={db_config['database_name']}\n"

    masked_env_content += f"""
# OpenAI API Key
OPENAI_API_KEY={mask_sensitive_data(openai_api_key)}

# DeepSeek API Key
DEEPSEEK_API_KEY={mask_sensitive_data(deepseek_api_key)}

# GigaChat Configuration
GIGACHAT_CREDENTIALS={mask_sensitive_data(gigachat_credentials)}
GIGACHAT_SCOPE={gigachat_scope}
GIGACHAT_ACCESS_TOKEN={mask_sensitive_data(gigachat_access_token)}
GIGACHAT_VERIFY_SSL_CERTS={gigachat_verify_ssl_certs}

# Brave Search API Key
BRAVE_SEARCH_API_KEY={mask_sensitive_data(brave_search_api_key)}

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

# MCP Capable Model Configuration
MCP_SQL_LLM_PROVIDER={mcp_sql_llm_provider}
MCP_SQL_LLM_MODEL={mcp_sql_llm_model}
MCP_SQL_LLM_HOSTNAME={mcp_sql_llm_hostname}
MCP_SQL_LLM_PORT={mcp_sql_llm_port}
MCP_SQL_LLM_API_PATH={mcp_sql_llm_api_path}
MCP_RESPONSE_LLM_PROVIDER={mcp_response_llm_provider}
MCP_RESPONSE_LLM_MODEL={mcp_response_llm_model}
MCP_RESPONSE_LLM_HOSTNAME={mcp_response_llm_hostname}
MCP_RESPONSE_LLM_PORT={mcp_response_llm_port}
MCP_RESPONSE_LLM_API_PATH={mcp_response_llm_api_path}
MCP_PROMPT_LLM_PROVIDER={mcp_prompt_llm_provider}
MCP_PROMPT_LLM_MODEL={mcp_prompt_llm_model}
MCP_PROMPT_LLM_HOSTNAME={mcp_prompt_llm_hostname}
MCP_PROMPT_LLM_PORT={mcp_prompt_llm_port}
MCP_PROMPT_LLM_API_PATH={mcp_prompt_llm_api_path}

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Security LLM Configuration (for advanced SQL security analysis)
# Whether to use the security LLM for analysis (set to false to use basic keyword matching only)
USE_SECURITY_LLM={use_security_llm}
SECURITY_LLM_PROVIDER={security_llm_provider}
SECURITY_LLM_MODEL={security_llm_model}
SECURITY_LLM_HOSTNAME={security_llm_hostname}
SECURITY_LLM_PORT={security_llm_port}
SECURITY_LLM_API_PATH={security_llm_api_path}

# Dedicated MCP Model Configuration (separate model specifically for MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER={dedicated_mcp_llm_provider}
DEDICATED_MCP_LLM_MODEL={dedicated_mcp_llm_model}
DEDICATED_MCP_LLM_HOSTNAME={dedicated_mcp_llm_hostname}
DEDICATED_MCP_LLM_PORT={dedicated_mcp_llm_port}
DEDICATED_MCP_LLM_API_PATH={dedicated_mcp_llm_api_path}

# Logging Configuration
ENABLE_SCREEN_LOGGING={enable_screen_logging}
"""

    # Write to .env file with unmasked content
    try:
        with open(env_file_path, 'w') as env_file:
            env_file.write(env_content)
        print(f"\nConfiguration saved to {env_file_path}")

        # Display masked content to the user for security
        print("\nSaved configuration (sensitive data masked for display):")
        print("-" * 50)
        print(masked_env_content)
        print("-" * 50)

        # Reload the database configuration to ensure it's available
        # Add the project root directory to the Python path if not already present
        current_project_root = Path(__file__).parent.parent  # Go up two levels to project root
        if str(current_project_root) not in sys.path:
            sys.path.insert(0, str(current_project_root))

        from database.utils.multi_database_manager import reload_database_config
        reload_database_config()
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
DEFAULT_DATABASE_ENABLED={default_database_enabled}
DATABASE_ENABLED={database_enabled}
MCP_ENABLED={mcp_enabled}
CONFIGURE_MCP_MODELS={configure_mcp_models_value}

# Default LLM Model Configuration
DEFAULT_LLM_PROVIDER={default_llm_provider}
DEFAULT_LLM_MODEL={default_llm_model}
DEFAULT_LLM_HOSTNAME={default_llm_hostname}
DEFAULT_LLM_PORT={default_llm_port}
DEFAULT_LLM_API_PATH={default_llm_api_path}
"""

        # Add example entries for additional database configurations
        if additional_db_configs:
            for db_config in additional_db_configs:
                db_name_upper = db_config['name'].upper()
                example_env_content += f"# Example: DB_{db_name_upper}_URL={db_config['url']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_TYPE={db_config['type']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_USERNAME={db_config['username']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_PASSWORD={db_config['password']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_HOSTNAME={db_config['hostname']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_PORT={db_config['port']}\n"
                example_env_content += f"# Example: DB_{db_name_upper}_NAME={db_config['database_name']}\n"
        else:
            example_env_content += f"# Example additional database:\n# DB_ANALYTICS_URL=postgresql://username:password@hostname:port/dbname\n"
            example_env_content += f"# DB_ANALYTICS_TYPE=postgresql\n"
            example_env_content += f"# DB_ANALYTICS_USERNAME=username\n"
            example_env_content += f"# DB_ANALYTICS_PASSWORD=password\n"
            example_env_content += f"# DB_ANALYTICS_HOSTNAME=hostname\n"
            example_env_content += f"# DB_ANALYTICS_PORT=5432\n"
            example_env_content += f"# DB_ANALYTICS_NAME=dbname\n"

        example_env_content += f"""
# OpenAI API Key
OPENAI_API_KEY={mask_sensitive_data(openai_api_key)}

# DeepSeek API Key
DEEPSEEK_API_KEY={mask_sensitive_data(deepseek_api_key)}

# GigaChat Configuration
GIGACHAT_CREDENTIALS={mask_sensitive_data(gigachat_credentials)}
GIGACHAT_SCOPE={gigachat_scope}
GIGACHAT_ACCESS_TOKEN={mask_sensitive_data(gigachat_access_token)}
GIGACHAT_VERIFY_SSL_CERTS=y

# Brave Search API Key
BRAVE_SEARCH_API_KEY={mask_sensitive_data(brave_search_api_key)}

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

# MCP Capable Model Configuration
MCP_SQL_LLM_PROVIDER={mcp_sql_llm_provider}
MCP_SQL_LLM_MODEL={mcp_sql_llm_model}
MCP_SQL_LLM_HOSTNAME={mcp_sql_llm_hostname}
MCP_SQL_LLM_PORT={mcp_sql_llm_port}
MCP_SQL_LLM_API_PATH={mcp_sql_llm_api_path}
MCP_RESPONSE_LLM_PROVIDER={mcp_response_llm_provider}
MCP_RESPONSE_LLM_MODEL={mcp_response_llm_model}
MCP_RESPONSE_LLM_HOSTNAME={mcp_response_llm_hostname}
MCP_RESPONSE_LLM_PORT={mcp_response_llm_port}
MCP_RESPONSE_LLM_API_PATH={mcp_response_llm_api_path}
MCP_PROMPT_LLM_PROVIDER={mcp_prompt_llm_provider}
MCP_PROMPT_LLM_MODEL={mcp_prompt_llm_model}
MCP_PROMPT_LLM_HOSTNAME={mcp_prompt_llm_hostname}
MCP_PROMPT_LLM_PORT={mcp_prompt_llm_port}
MCP_PROMPT_LLM_API_PATH={mcp_prompt_llm_api_path}

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL=false

# Security LLM Configuration (for advanced SQL security analysis)
# Whether to use the security LLM for analysis (set to false to use basic keyword matching only)
USE_SECURITY_LLM=Y
SECURITY_LLM_PROVIDER=LM Studio
SECURITY_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
SECURITY_LLM_HOSTNAME=api.openai.com
SECURITY_LLM_PORT=1234
SECURITY_LLM_API_PATH=/v1

# Dedicated MCP Model Configuration (separate model specifically for MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER=LM Studio
DEDICATED_MCP_LLM_MODEL=qwen2.5-coder-7b-instruct-abliterated@q3_k_m
DEDICATED_MCP_LLM_HOSTNAME=localhost
DEDICATED_MCP_LLM_PORT=1234
DEDICATED_MCP_LLM_API_PATH=/v1

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