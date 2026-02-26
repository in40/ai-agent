#!/usr/bin/env python3
import re

# Read the file
with open('/root/qwen/ai_agent/start_all_services.sh', 'r') as f:
    content = f.read()

# Find the position after "Wait for Download server to start"
pattern = r'(sleep 3\n\n# Start Download MCP Server.*?sleep 3\n)'
match = re.search(pattern, content, re.DOTALL)

if match:
    insert_pos = match.end()
    
    document_store_code = '''
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

'''
    
    # Insert the code
    content = content[:insert_pos] + document_store_code + content[insert_pos:]
    
    # Write back
    with open('/root/qwen/ai_agent/start_all_services.sh', 'w') as f:
        f.write(content)
    
    print("✅ Document Store startup code inserted successfully")
else:
    print("❌ Could not find insertion point")
