#!/bin/bash

# Script to start all MCP services (Registry, SQL, RAG, etc.)

echo "Starting MCP Services..."
echo ""

cd /root/qwen_test/ai_agent

# Create a log file for the services
LOG_FILE="/tmp/mcp_services.log"
echo "Starting MCP services at $(date)" > "$LOG_FILE"

# Start the MCP service registry
echo "Starting MCP Service Registry on port 8080..."
python -m registry.registry_server --host 127.0.0.1 --port 8080 >>"$LOG_FILE" 2>&1 &
REGISTRY_PID=$!

# Give the registry a moment to start
sleep 2

# Start the SQL MCP server
echo "Starting SQL MCP Server on port 8092..."
python -m sql_mcp_server.sql_mcp_server --host 127.0.0.1 --port 8092 --registry-url http://127.0.0.1:8080 >>"$LOG_FILE" 2>&1 &
SQL_PID=$!

# Start the RAG MCP server
echo "Starting RAG MCP Server on port 8091..."
python -m rag_component.rag_mcp_server --host 127.0.0.1 --port 8091 --registry-url http://127.0.0.1:8080 >>"$LOG_FILE" 2>&1 &
RAG_PID=$!

# Give the services a moment to start up
sleep 3

# Check if the services started successfully
if kill -0 $REGISTRY_PID 2>/dev/null; then
    echo "MCP Service Registry (PID $REGISTRY_PID) started successfully"
else
    echo "Warning: MCP Service Registry may not have started correctly. Check $LOG_FILE"
fi

if kill -0 $SQL_PID 2>/dev/null; then
    echo "SQL MCP Server (PID $SQL_PID) started successfully"
else
    echo "Warning: SQL MCP Server may not have started correctly. Check $LOG_FILE"
fi

if kill -0 $RAG_PID 2>/dev/null; then
    echo "RAG MCP Server (PID $RAG_PID) started successfully"
else
    echo "Warning: RAG MCP Server may not have started correctly. Check $LOG_FILE"
fi

echo ""
echo "All MCP services started!"
echo "Registry: http://127.0.0.1:8080"
echo "SQL Server: http://127.0.0.1:8092"
echo "RAG Server: http://127.0.0.1:8091"
echo ""
echo "Log file: $LOG_FILE"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for all background processes
wait $REGISTRY_PID $SQL_PID $RAG_PID