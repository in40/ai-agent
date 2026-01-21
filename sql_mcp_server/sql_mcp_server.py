#!/usr/bin/env python3
"""
SQL MCP Server - An MCP server that provides SQL generation and execution services
and registers itself with the service registry.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the path so we can import from models and database modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.sql_generator import SQLGenerator
from models.sql_executor import SQLExecutor
from database.utils.multi_database_manager import multi_db_manager
from registry.registry_client import ServiceRegistryClient as RegistryClient
from config.settings import DISABLE_DATABASES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MCPServer.SQL')

class SQLRequestHandler:
    """Handler for SQL-related requests from the MCP framework."""

    def __init__(self, sql_generator: SQLGenerator, sql_executor: SQLExecutor):
        self.sql_generator = sql_generator
        self.sql_executor = sql_executor

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming SQL requests."""
        try:
            logger.info(f"Received SQL request: {request}")

            action = request.get("action")
            parameters = request.get("parameters", {})

            if action == "generate_sql":
                return await self.generate_sql(parameters)
            elif action == "execute_sql":
                return await self.execute_sql(parameters)
            elif action == "get_schema":
                return await self.get_schema(parameters)
            elif action == "validate_sql":
                return await self.validate_sql(parameters)
            else:
                return {
                    "error": f"Unknown action: {action}",
                    "status": "error"
                }

        except Exception as e:
            logger.error(f"Error handling SQL request: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def generate_sql(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query based on user request and schema."""
        try:
            user_request = parameters.get("user_request", "")
            schema_dump = parameters.get("schema_dump", {})
            attached_files = parameters.get("attached_files", None)
            previous_sql_queries = parameters.get("previous_sql_queries", None)
            table_to_db_mapping = parameters.get("table_to_db_mapping", None)
            table_to_real_db_mapping = parameters.get("table_to_real_db_mapping", None)

            if not user_request:
                return {
                    "error": "User request is required",
                    "status": "error"
                }

            # Generate SQL using the SQLGenerator
            sql_query = self.sql_generator.generate_sql(
                user_request=user_request,
                schema_dump=schema_dump,
                attached_files=attached_files,
                previous_sql_queries=previous_sql_queries,
                table_to_db_mapping=table_to_db_mapping,
                table_to_real_db_mapping=table_to_real_db_mapping
            )

            return {
                "sql_query": sql_query,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def execute_sql(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query against the database."""
        try:
            sql_query = parameters.get("sql_query", "")
            db_name = parameters.get("db_name", None)
            table_to_db_mapping = parameters.get("table_to_db_mapping", None)

            if not sql_query:
                return {
                    "error": "SQL query is required",
                    "status": "error"
                }

            # Execute SQL using the SQLExecutor
            results = self.sql_executor.execute_sql_and_get_results(
                sql_query=sql_query,
                db_name=db_name,
                table_to_db_mapping=table_to_db_mapping
            )

            return {
                "results": results,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error executing SQL: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def get_schema(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            db_name = parameters.get("db_name", None)

            # Get schema from the database manager
            schema = multi_db_manager.get_schema_dump(db_name)

            return {
                "schema": schema,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }

    async def validate_sql(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SQL query for safety and correctness."""
        try:
            sql_query = parameters.get("sql_query", "")
            schema_dump = parameters.get("schema_dump", "")

            if not sql_query:
                return {
                    "error": "SQL query is required",
                    "status": "error"
                }

            # Check for potentially harmful commands
            is_safe, issues = self.sql_executor.check_for_harmful_commands(sql_query)

            if not is_safe:
                return {
                    "is_safe": False,
                    "issues": issues,
                    "status": "validation_failed"
                }

            # Additional validation could be added here
            # For now, we'll just return that the query passed basic safety checks
            return {
                "is_safe": True,
                "issues": [],
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Error validating SQL: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "status": "error"
            }


class SQLMCPServer:
    """MCP Server for SQL services."""

    def __init__(self, host="127.0.0.1", port=8092, registry_url="http://127.0.0.1:8080"):
        self.host = host
        self.port = port
        self.registry_url = registry_url
        self.registry_client = RegistryClient(registry_url)
        self.sql_generator = None
        self.sql_executor = None
        self.request_handler = None
        self.server = None
        self.running = False

    async def start(self):
        """Start the SQL MCP server."""
        try:
            logger.info(f"Initializing SQL MCP Server on {self.host}:{self.port}")

            # Check if databases are disabled
            if DISABLE_DATABASES:
                logger.warning("Databases are disabled according to configuration")

            # Initialize the SQL components
            self.sql_generator = SQLGenerator()
            self.sql_executor = SQLExecutor(multi_db_manager)
            self.request_handler = SQLRequestHandler(self.sql_generator, self.sql_executor)

            # Start the server (using aiohttp)
            await self._start_server()

            # Register with the MCP registry (optional for testing)
            try:
                await self.register_with_registry()
            except Exception as reg_error:
                logger.warning(f"Registry registration failed (this is OK for testing): {reg_error}")

            self.running = True
            logger.info(f"SQL MCP Server listening on {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Error starting SQL MCP Server: {str(e)}", exc_info=True)
            raise

    async def _start_server(self):
        """Start the underlying server implementation."""
        # Using aiohttp for the HTTP server
        from aiohttp import web

        async def handle_request(request):
            if request.method == 'POST':
                try:
                    data = await request.json()
                    response = await self.request_handler.handle_request(data)
                    return web.json_response(response)
                except Exception as e:
                    logger.error(f"Error handling request: {str(e)}", exc_info=True)
                    return web.json_response({
                        "error": str(e),
                        "status": "error"
                    })
            else:
                return web.json_response({
                    "error": "Only POST requests are supported",
                    "status": "error"
                })

        app = web.Application()
        app.router.add_post('/', handle_request)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        self.runner = runner  # Keep reference to prevent garbage collection

    async def register_with_registry(self):
        """Register this server with the MCP service registry."""
        try:
            from registry.registry_client import ServiceInfo

            service_info = ServiceInfo(
                id=f"sql-server-{self.host.replace('.', '-')}-{self.port}",
                host=self.host,
                port=self.port,
                type="mcp_sql",
                metadata={
                    "name": "sql-service",
                    "description": "SQL generation and execution service for database queries",
                    "capabilities": [
                        {
                            "name": "generate_sql",
                            "description": "Generate SQL query based on user request and schema",
                            "parameters": {
                                "user_request": {"type": "string", "required": True},
                                "schema_dump": {"type": "object", "required": True},
                                "attached_files": {"type": "array", "required": False},
                                "previous_sql_queries": {"type": "array", "required": False},
                                "table_to_db_mapping": {"type": "object", "required": False},
                                "table_to_real_db_mapping": {"type": "object", "required": False}
                            }
                        },
                        {
                            "name": "execute_sql",
                            "description": "Execute SQL query against the database",
                            "parameters": {
                                "sql_query": {"type": "string", "required": True},
                                "db_name": {"type": "string", "required": False},
                                "table_to_db_mapping": {"type": "object", "required": False}
                            }
                        },
                        {
                            "name": "get_schema",
                            "description": "Get database schema information",
                            "parameters": {
                                "db_name": {"type": "string", "required": False}
                            }
                        },
                        {
                            "name": "validate_sql",
                            "description": "Validate SQL query for safety and correctness",
                            "parameters": {
                                "sql_query": {"type": "string", "required": True},
                                "schema_dump": {"type": "object", "required": False}
                            }
                        }
                    ]
                }
            )

            self.registry_client.register_service(service_info, ttl=60)
            logger.info("Successfully registered SQL service with MCP registry")

        except Exception as e:
            logger.error(f"Error registering with MCP registry: {str(e)}", exc_info=True)
            raise

    async def stop(self):
        """Stop the SQL MCP server."""
        try:
            logger.info("Stopping SQL MCP Server...")

            # Unregister from the registry (optional for testing)
            try:
                self.registry_client.unregister_service(f"sql-server-{self.host.replace('.', '-')}-{self.port}")
            except Exception as reg_error:
                logger.warning(f"Registry unregistration failed (this is OK for testing): {reg_error}")

            # Stop the server
            if hasattr(self, 'runner'):
                await self.runner.cleanup()

            self.running = False
            logger.info("SQL MCP Server stopped")

        except Exception as e:
            logger.error(f"Error stopping SQL MCP Server: {str(e)}", exc_info=True)
            raise


async def main():
    """Main entry point for the SQL MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description='SQL MCP Server - Provides SQL generation and execution services to the MCP framework')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host address to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8092, help='Port to listen on (default: 8092)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080', help='URL of the MCP registry server')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    server = SQLMCPServer(host=args.host, port=args.port, registry_url=args.registry_url)

    try:
        await server.start()

        # Keep the server running
        while server.running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())