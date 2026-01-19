#!/usr/bin/env python3
"""
Test script to verify the SQL MCP server integration
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sql_mcp_server.sql_mcp_server import SQLMCPServer
from sql_mcp_server.client import SQLMCPClient


async def test_sql_mcp_server():
    """Test the SQL MCP server functionality."""
    print("Starting SQL MCP Server test...")

    # Create and start the server
    server = SQLMCPServer(host="127.0.0.1", port=8092, registry_url="http://127.0.0.1:8080")

    try:
        # Start the server in the background
        await server.start()
        print("SQL MCP Server started successfully")

        # Wait a moment for the server to fully initialize
        await asyncio.sleep(1)

        # Create a client to test the server
        client = SQLMCPClient(server_url="http://127.0.0.1:8092")

        # Test the get_schema functionality
        print("\nTesting get_schema...")
        schema_result = client.get_schema()
        print(f"Schema result: {schema_result}")

        # Test the validate_sql functionality with a simple query
        print("\nTesting validate_sql...")
        validation_result = client.validate_sql("SELECT * FROM users LIMIT 1;")
        print(f"Validation result: {validation_result}")

        # Test with a potentially unsafe query
        print("\nTesting validate_sql with potentially unsafe query...")
        unsafe_validation_result = client.validate_sql("DROP TABLE users;")
        print(f"Unsafe validation result: {unsafe_validation_result}")

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the server
        await server.stop()
        print("SQL MCP Server stopped")


if __name__ == "__main__":
    asyncio.run(test_sql_mcp_server())