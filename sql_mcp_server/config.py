"""
Configuration for SQL MCP Server
"""

import os

# Server configuration
SQL_MCP_HOST = os.getenv('SQL_MCP_HOST', '127.0.0.1')
SQL_MCP_PORT = int(os.getenv('SQL_MCP_PORT', 8092))
SQL_MCP_REGISTRY_URL = os.getenv('SQL_MCP_REGISTRY_URL', 'http://127.0.0.1:8080')

# Logging configuration
SQL_MCP_LOG_LEVEL = os.getenv('SQL_MCP_LOG_LEVEL', 'INFO')

# Database configuration
SQL_MCP_DISABLE_DATABASES = os.getenv('DISABLE_DATABASES', 'false').lower() == 'true'