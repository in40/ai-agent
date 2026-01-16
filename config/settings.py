import os
from dotenv import load_dotenv

def str_to_bool(value, default=False):
    """
    Convert string value to boolean.
    Handles both 'y'/'n' and 'true'/'false' formats.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    value = value.lower().strip()
    if value in ('true', '1', 'yes', 'y'):
        return True
    elif value in ('false', '0', 'no', 'n'):
        return False
    else:
        # If the value doesn't match known boolean strings, return default
        return default

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "postgresql")
DB_USERNAME = os.getenv("DB_USERNAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOSTNAME = os.getenv("DB_HOSTNAME", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ai_agent_db")
DATABASE_URL = os.getenv("DATABASE_URL", f"{DB_TYPE}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME}")

# Additional database configurations
# These can be used to define multiple databases in the format:
# DB_{NAME}_TYPE, DB_{NAME}_USERNAME, DB_{NAME}_PASSWORD, etc.
# For example: DB_ANALYTICS_TYPE, DB_ANALYTICS_USERNAME, etc.
ADDITIONAL_DATABASES = {}

# Discover additional databases from environment variables
for key, value in os.environ.items():
    if key.startswith("DB_") and key.endswith("_URL"):
        # Extract the database name from the environment variable name
        db_name = key[3:-4].lower()  # Remove "DB_" prefix and "_URL" suffix
        ADDITIONAL_DATABASES[db_name] = value
    elif key.startswith("DB_") and "_TYPE" in key:
        # Extract the database name from the environment variable name
        parts = key.split('_')
        if len(parts) >= 3:
            db_name = '_'.join(parts[1:-1]).lower()  # Everything between "DB_" and "_TYPE"
            # Construct the database URL from individual components
            db_type = os.getenv(f"DB_{db_name.upper()}_TYPE")
            db_username = os.getenv(f"DB_{db_name.upper()}_USERNAME")
            db_password = os.getenv(f"DB_{db_name.upper()}_PASSWORD", "")
            db_hostname = os.getenv(f"DB_{db_name.upper()}_HOSTNAME", "localhost")
            db_port = os.getenv(f"DB_{db_name.upper()}_PORT", "5432")
            db_name_env = os.getenv(f"DB_{db_name.upper()}_NAME")

            if all([db_type, db_username, db_name_env]):
                db_url = f"{db_type}://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_name_env}"
                ADDITIONAL_DATABASES[db_name] = db_url

# Default LLM Model configurations (used when specific model configs are not provided)
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "LM Studio")
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
DEFAULT_LLM_HOSTNAME = os.getenv("DEFAULT_LLM_HOSTNAME", "localhost")
DEFAULT_LLM_PORT = os.getenv("DEFAULT_LLM_PORT", "1234")
DEFAULT_LLM_API_PATH = os.getenv("DEFAULT_LLM_API_PATH", "/v1")

# LLM Model configurations
SQL_LLM_PROVIDER = os.getenv("SQL_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
SQL_LLM_MODEL = os.getenv("SQL_LLM_MODEL", DEFAULT_LLM_MODEL)
SQL_LLM_HOSTNAME = os.getenv("SQL_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
SQL_LLM_PORT = os.getenv("SQL_LLM_PORT", DEFAULT_LLM_PORT)
SQL_LLM_API_PATH = os.getenv("SQL_LLM_API_PATH", DEFAULT_LLM_API_PATH)
RESPONSE_LLM_PROVIDER = os.getenv("RESPONSE_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
RESPONSE_LLM_MODEL = os.getenv("RESPONSE_LLM_MODEL", DEFAULT_LLM_MODEL)
RESPONSE_LLM_HOSTNAME = os.getenv("RESPONSE_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
RESPONSE_LLM_PORT = os.getenv("RESPONSE_LLM_PORT", DEFAULT_LLM_PORT)
RESPONSE_LLM_API_PATH = os.getenv("RESPONSE_LLM_API_PATH", DEFAULT_LLM_API_PATH)
PROMPT_LLM_PROVIDER = os.getenv("PROMPT_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
PROMPT_LLM_MODEL = os.getenv("PROMPT_LLM_MODEL", DEFAULT_LLM_MODEL)
PROMPT_LLM_HOSTNAME = os.getenv("PROMPT_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
PROMPT_LLM_PORT = os.getenv("PROMPT_LLM_PORT", DEFAULT_LLM_PORT)
PROMPT_LLM_API_PATH = os.getenv("PROMPT_LLM_API_PATH", DEFAULT_LLM_API_PATH)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# GigaChat Configuration
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_ACCESS_TOKEN = os.getenv("GIGACHAT_ACCESS_TOKEN")
GIGACHAT_VERIFY_SSL_CERTS = str_to_bool(os.getenv("GIGACHAT_VERIFY_SSL_CERTS"), True)

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL = str_to_bool(os.getenv("TERMINATE_ON_POTENTIALLY_HARMFUL_SQL"), False)

# Security LLM Configuration (for advanced SQL security analysis)
SECURITY_LLM_PROVIDER = os.getenv("SECURITY_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
SECURITY_LLM_MODEL = os.getenv("SECURITY_LLM_MODEL", DEFAULT_LLM_MODEL)
SECURITY_LLM_HOSTNAME = os.getenv("SECURITY_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
SECURITY_LLM_PORT = os.getenv("SECURITY_LLM_PORT", DEFAULT_LLM_PORT)
SECURITY_LLM_API_PATH = os.getenv("SECURITY_LLM_API_PATH", DEFAULT_LLM_API_PATH)
USE_SECURITY_LLM = str_to_bool(os.getenv("USE_SECURITY_LLM"), True)  # Whether to use the security LLM for analysis

# Logging Configuration
ENABLE_SCREEN_LOGGING = str_to_bool(os.getenv("ENABLE_SCREEN_LOGGING"), False)

# Model Disable Configuration
DISABLE_PROMPT_GENERATION = str_to_bool(os.getenv("DISABLE_PROMPT_GENERATION"), False)
DISABLE_RESPONSE_GENERATION = str_to_bool(os.getenv("DISABLE_RESPONSE_GENERATION"), False)

# Handle both DISABLE_DATABASES and DATABASE_ENABLED for backward compatibility
# If DISABLE_DATABASES is set, use it directly
# If DATABASE_ENABLED is set, invert its value (DATABASE_ENABLED=false means DISABLE_DATABASES=true)
# If DEFAULT_DATABASE_ENABLED is set to false, it will disable the default database specifically
disable_databases_env = os.getenv("DISABLE_DATABASES")
database_enabled_env = os.getenv("DATABASE_ENABLED")
default_database_enabled_env = os.getenv("DEFAULT_DATABASE_ENABLED", "true")

if disable_databases_env is not None:
    # Use DISABLE_DATABASES if it's explicitly set
    DISABLE_DATABASES = str_to_bool(disable_databases_env, False)
elif database_enabled_env is not None:
    # If DATABASE_ENABLED is set, invert its value
    # DATABASE_ENABLED=false means databases should be disabled
    database_enabled = str_to_bool(database_enabled_env, True)  # Default to True if not set
    DISABLE_DATABASES = not database_enabled
else:
    # Default to False (databases enabled) if neither is set
    DISABLE_DATABASES = False

# Check if default database is specifically disabled
DEFAULT_DATABASE_ENABLED = str_to_bool(default_database_enabled_env, True)

# MCP LLM Configuration
MCP_LLM_PROVIDER = os.getenv("MCP_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
MCP_LLM_MODEL = os.getenv("MCP_LLM_MODEL", DEFAULT_LLM_MODEL)
MCP_LLM_HOSTNAME = os.getenv("MCP_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
MCP_LLM_PORT = os.getenv("MCP_LLM_PORT", DEFAULT_LLM_PORT)
MCP_LLM_API_PATH = os.getenv("MCP_LLM_API_PATH", DEFAULT_LLM_API_PATH)

# Dedicated MCP LLM Configuration (separate model for MCP-related queries)
DEDICATED_MCP_LLM_PROVIDER = os.getenv("DEDICATED_MCP_LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
DEDICATED_MCP_LLM_MODEL = os.getenv("DEDICATED_MCP_LLM_MODEL", DEFAULT_LLM_MODEL)
DEDICATED_MCP_LLM_HOSTNAME = os.getenv("DEDICATED_MCP_LLM_HOSTNAME", DEFAULT_LLM_HOSTNAME)
DEDICATED_MCP_LLM_PORT = os.getenv("DEDICATED_MCP_LLM_PORT", DEFAULT_LLM_PORT)
DEDICATED_MCP_LLM_API_PATH = os.getenv("DEDICATED_MCP_LLM_API_PATH", DEFAULT_LLM_API_PATH)