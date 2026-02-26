#!/bin/bash
# Script to add Document Store MCP Server to start_all_services.sh

STARTUP_FILE="/root/qwen/ai_agent/start_all_services.sh"

# Find the line number after "Wait for Download server to start"
LINE_NUM=$(grep -n "Wait for Download server to start" "$STARTUP_FILE" | cut -d: -f1)
LINE_NUM=$((LINE_NUM + 2))

# Create the Document Store startup code
DOCUMENT_STORE_CODE='
# Start Document Store MCP Server (port 3070)
echo -e "${YELLOW}Starting Document Store MCP Server on port 3070...${NC}"
nohup bash -c "source '"'"'$PROJECT_ROOT/ai_agent_env/bin/activate'"'"' && cd '"'"'$PROJECT_ROOT/document-store-mcp-server'"'"' && python -m document_store_server.server --port 3070" > document_store_mcp_server.log 2>&1 &
DOCUMENT_STORE_PID=$!
echo -e "${GREEN}Document Store MCP Server started with PID $DOCUMENT_STORE_PID${NC}"

# Wait for Document Store to start
sleep 2

# Test Document Store
if curl -s -f -m 10 "http://localhost:3070/mcp" -H "Content-Type: application/json" -d '"'"'{"jsonrpc":"2.0","method":"tools/list","id":1}'"'"' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Document Store MCP Server is responding${NC}"
else
    echo -e "${YELLOW}⚠ Document Store MCP Server may still be starting up${NC}"
fi
'

# Insert the code
sed -i "${LINE_NUM}i\\$DOCUMENT_STORE_CODE" "$STARTUP_FILE"

# Add Document Store to the service list
sed -i '/echo "Download MCP Server: http:\/\/localhost:8093"/a echo "Document Store MCP:  http://localhost:3070"' "$STARTUP_FILE"

# Add DOCUMENT_STORE_PID to the PIDs file section
sed -i '/DOWNLOAD_PID=$DOWNLOAD_PID/a DOCUMENT_STORE_PID=$DOCUMENT_STORE_PID' "$STARTUP_FILE"

# Add DOCUMENT_STORE_PID to the cleanup function
sed -i '/for pid_var in.*DOWNLOAD_PID;/s/DOWNLOAD_PID;/DOWNLOAD_PID DOCUMENT_STORE_PID;/' "$STARTUP_FILE"

echo "✅ Document Store MCP Server added to start_all_services.sh"
echo "📝 Changes:"
echo "   - Added startup code (port 3070)"
echo "   - Added to service list display"
echo "   - Added to PID tracking"
echo "   - Added to cleanup function"
