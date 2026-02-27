#!/bin/bash

# Simple startup script for the standard MCP server with default settings
# Usage: ./start_mcp_default.sh

echo "Starting MCP Server with default settings..."

# Start with Streamable HTTP transport on port 3030 (this is already correct)
python -m mcp_std_server.server --transport streamable-http --port 3030