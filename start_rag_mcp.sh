#!/bin/bash
# Script to start RAG MCP server with proper environment
cd /root/qwen/ai_agent
source .env
export RAG_SIMILARITY_THRESHOLD=0.6
python -m rag_component.rag_mcp_server --host 0.0.0.0 --port 8091 --registry-url http://192.168.51.216:8080 &