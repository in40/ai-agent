"""
Client for communicating with the SQL MCP Server
"""

import json
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

class SQLMCPClient:
    """Client for communicating with the SQL MCP server."""

    def __init__(self, server_url: str = "http://127.0.0.1:8092"):
        self.server_url = server_url

    def generate_sql(
        self,
        user_request: str,
        schema_dump: Dict[str, Any],
        attached_files: Optional[List[Dict]] = None,
        previous_sql_queries: Optional[List[str]] = None,
        table_to_db_mapping: Optional[Dict[str, str]] = None,
        table_to_real_db_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Generate SQL query based on user request and schema."""
        try:
            payload = {
                "action": "generate_sql",
                "parameters": {
                    "user_request": user_request,
                    "schema_dump": schema_dump,
                    "attached_files": attached_files or [],
                    "previous_sql_queries": previous_sql_queries or [],
                    "table_to_db_mapping": table_to_db_mapping or {},
                    "table_to_real_db_mapping": table_to_db_mapping or {}
                }
            }

            response = requests.post(
                f"{self.server_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "sql_query": result.get("sql_query"),
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "sql_query": None,
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    }
            else:
                return {
                    "sql_query": None,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            return {
                "sql_query": None,
                "success": False,
                "error": str(e)
            }

    def execute_sql(
        self,
        sql_query: str,
        db_name: Optional[str] = None,
        table_to_db_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute SQL query against the database."""
        try:
            payload = {
                "action": "execute_sql",
                "parameters": {
                    "sql_query": sql_query,
                    "db_name": db_name,
                    "table_to_db_mapping": table_to_db_mapping or {}
                }
            }

            response = requests.post(
                f"{self.server_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "results": result.get("results", []),
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "results": [],
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    }
            else:
                return {
                    "results": [],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}")
            return {
                "results": [],
                "success": False,
                "error": str(e)
            }

    def get_schema(self, db_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            payload = {
                "action": "get_schema",
                "parameters": {
                    "db_name": db_name
                }
            }

            response = requests.post(
                f"{self.server_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    return {
                        "schema": result.get("schema", {}),
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "schema": {},
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    }
            else:
                return {
                    "schema": {},
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            return {
                "schema": {},
                "success": False,
                "error": str(e)
            }

    def validate_sql(
        self,
        sql_query: str,
        schema_dump: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate SQL query for safety and correctness."""
        try:
            payload = {
                "action": "validate_sql",
                "parameters": {
                    "sql_query": sql_query,
                    "schema_dump": schema_dump or {}
                }
            }

            response = requests.post(
                f"{self.server_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success" or result.get("status") == "validation_failed":
                    return {
                        "is_safe": result.get("is_safe", True),
                        "issues": result.get("issues", []),
                        "success": True,
                        "error": None
                    }
                else:
                    return {
                        "is_safe": False,
                        "issues": [],
                        "success": False,
                        "error": result.get("error", "Unknown error")
                    }
            else:
                return {
                    "is_safe": False,
                    "issues": [],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Error validating SQL: {str(e)}")
            return {
                "is_safe": False,
                "issues": [],
                "success": False,
                "error": str(e)
            }