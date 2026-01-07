import os
from dotenv import load_dotenv

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

# LLM Model configurations
SQL_LLM_PROVIDER = os.getenv("SQL_LLM_PROVIDER", "OpenAI")
SQL_LLM_MODEL = os.getenv("SQL_LLM_MODEL", "gpt-3.5-turbo")
SQL_LLM_HOSTNAME = os.getenv("SQL_LLM_HOSTNAME", "localhost")
SQL_LLM_PORT = os.getenv("SQL_LLM_PORT", "443")
SQL_LLM_API_PATH = os.getenv("SQL_LLM_API_PATH", "/v1")
RESPONSE_LLM_PROVIDER = os.getenv("RESPONSE_LLM_PROVIDER", "OpenAI")
RESPONSE_LLM_MODEL = os.getenv("RESPONSE_LLM_MODEL", "gpt-4")
RESPONSE_LLM_HOSTNAME = os.getenv("RESPONSE_LLM_HOSTNAME", "localhost")
RESPONSE_LLM_PORT = os.getenv("RESPONSE_LLM_PORT", "443")
RESPONSE_LLM_API_PATH = os.getenv("RESPONSE_LLM_API_PATH", "/v1")
PROMPT_LLM_PROVIDER = os.getenv("PROMPT_LLM_PROVIDER", "OpenAI")
PROMPT_LLM_MODEL = os.getenv("PROMPT_LLM_MODEL", "gpt-3.5-turbo")
PROMPT_LLM_HOSTNAME = os.getenv("PROMPT_LLM_HOSTNAME", "localhost")
PROMPT_LLM_PORT = os.getenv("PROMPT_LLM_PORT", "443")
PROMPT_LLM_API_PATH = os.getenv("PROMPT_LLM_API_PATH", "/v1")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GigaChat Configuration
GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_ACCESS_TOKEN = os.getenv("GIGACHAT_ACCESS_TOKEN")
GIGACHAT_VERIFY_SSL_CERTS = os.getenv("GIGACHAT_VERIFY_SSL_CERTS", "true").lower() == "true"

# Security Configuration
TERMINATE_ON_POTENTIALLY_HARMFUL_SQL = os.getenv("TERMINATE_ON_POTENTIALLY_HARMFUL_SQL", "false").lower() == "true"

# Logging Configuration
ENABLE_SCREEN_LOGGING = os.getenv("ENABLE_SCREEN_LOGGING", "false").lower() == "true"