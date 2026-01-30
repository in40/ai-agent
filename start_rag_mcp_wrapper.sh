#!/bin/bash
# Wrapper script to start RAG MCP Server with proper environment

# Activate the virtual environment
source /root/qwen/ai_agent/ai_agent_env/bin/activate

# Source the environment variables properly
set -a
source /root/qwen/ai_agent/.env
set +a

# Start the RAG MCP Server
exec python -m rag_component.rag_mcp_server --host 0.0.0.0 --port 8091 --registry-url http://192.168.51.216:8080