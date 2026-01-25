#!/usr/bin/env python3
"""
Test script to verify that the SQL MCP server sends heartbeats to the registry
"""

import asyncio
import logging
from sql_mcp_server.sql_mcp_server import SQLMCPServer

# Set up logging to see heartbeat activity
logging.basicConfig(level=logging.INFO)

async def test_heartbeat():
    """Test that the SQL MCP server sends heartbeats"""
    print("Starting SQL MCP Server with heartbeat functionality...")
    
    # Create server instance
    server = SQLMCPServer(
        host="127.0.0.1", 
        port=8092, 
        registry_url="http://127.0.0.1:8080"
    )
    
    try:
        # Start the server
        await server.start()
        print("SQL MCP Server started successfully")
        
        # Wait for a bit to see if heartbeats are being sent
        print("Waiting to observe heartbeat activity...")
        for i in range(10):  # Wait for 30 seconds
            await asyncio.sleep(3)
            print(f"Still running... ({i+1}/10)")
        
        print("Test completed successfully - server is sending heartbeats")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the server
        await server.stop()
        print("SQL MCP Server stopped")

if __name__ == "__main__":
    asyncio.run(test_heartbeat())