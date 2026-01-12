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

# LLM Model configurations
SQL_LLM_PROVIDER = os.getenv("SQL_LLM_PROVIDER", "LM Studio")
SQL_LLM_MODEL = os.getenv("SQL_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
SQL_LLM_HOSTNAME = os.getenv("SQL_LLM_HOSTNAME", "localhost")
SQL_LLM_PORT = os.getenv("SQL_LLM_PORT", "1234")
SQL_LLM_API_PATH = os.getenv("SQL_LLM_API_PATH", "/v1")
RESPONSE_LLM_PROVIDER = os.getenv("RESPONSE_LLM_PROVIDER", "LM Studio")
RESPONSE_LLM_MODEL = os.getenv("RESPONSE_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
RESPONSE_LLM_HOSTNAME = os.getenv("RESPONSE_LLM_HOSTNAME", "localhost")
RESPONSE_LLM_PORT = os.getenv("RESPONSE_LLM_PORT", "1234")
RESPONSE_LLM_API_PATH = os.getenv("RESPONSE_LLM_API_PATH", "/v1")
PROMPT_LLM_PROVIDER = os.getenv("PROMPT_LLM_PROVIDER", "LM Studio")
PROMPT_LLM_MODEL = os.getenv("PROMPT_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
PROMPT_LLM_HOSTNAME = os.getenv("PROMPT_LLM_HOSTNAME", "localhost")
PROMPT_LLM_PORT = os.getenv("PROMPT_LLM_PORT", "1234")
PROMPT_LLM_API_PATH = os.getenv("PROMPT_LLM_API_PATH", "/v1")

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
SECURITY_LLM_PROVIDER = os.getenv("SECURITY_LLM_PROVIDER", "LM Studio")
SECURITY_LLM_MODEL = os.getenv("SECURITY_LLM_MODEL", "qwen2.5-coder-7b-instruct-abliterated@q3_k_m")
SECURITY_LLM_HOSTNAME = os.getenv("SECURITY_LLM_HOSTNAME", "localhost")
SECURITY_LLM_PORT = os.getenv("SECURITY_LLM_PORT", "1234")
SECURITY_LLM_API_PATH = os.getenv("SECURITY_LLM_API_PATH", "/v1")
USE_SECURITY_LLM = str_to_bool(os.getenv("USE_SECURITY_LLM"), True)  # Whether to use the security LLM for analysis

# Logging Configuration
ENABLE_SCREEN_LOGGING = str_to_bool(os.getenv("ENABLE_SCREEN_LOGGING"), False)