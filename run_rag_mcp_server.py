#!/usr/bin/env python3
"""
Script to run the RAG MCP Server with environment properly loaded
"""

import os
import sys
import asyncio
from dotenv import dotenv_values

# Load environment variables from .env file
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

# Now run the RAG MCP Server main function
from rag_component.rag_mcp_server import main

if __name__ == "__main__":
    # Parse command line arguments manually since we're not using the original main
    import argparse
    
    parser = argparse.ArgumentParser(description='RAG MCP Server - Provides RAG services to the MCP framework')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8091, help='Port to listen on (default: 8091)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080', help='URL of the MCP registry server')
    
    args = parser.parse_args()
    
    # Override the default values with our specific ones
    os.environ['RAG_MCP_HOST'] = args.host
    os.environ['RAG_MCP_PORT'] = str(args.port)
    os.environ['RAG_MCP_REGISTRY_URL'] = args.registry_url
    
    # Run the main function
    asyncio.run(main())