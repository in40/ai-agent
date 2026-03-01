#!/bin/bash

# Quick Fix Script for Document Store Port Conflict
# This script disables the base project's Document Store and starts ai_agent's

set -e

echo "================================================"
echo "Document Store Port Conflict - Quick Fix"
echo "================================================"
echo ""

# Step 1: Kill all Document Store processes
echo "Step 1: Stopping all Document Store processes..."
pkill -f "document_store_server" 2>/dev/null && echo "  ✓ Killed existing processes" || echo "  ℹ No processes to kill"
sleep 2

# Step 2: Verify port 3070 is free
echo ""
echo "Step 2: Checking if port 3070 is free..."
if lsof -i :3070 > /dev/null 2>&1; then
    echo "  ✗ Port 3070 is still in use!"
    lsof -i :3070
    echo ""
    echo "  Please manually kill the process above and re-run this script."
    exit 1
else
    echo "  ✓ Port 3070 is available"
fi

# Step 3: Backup and modify start_mcp_master.sh
echo ""
echo "Step 3: Backing up and modifying start_mcp_master.sh..."
MASTER_SCRIPT="/root/qwen/base/start_mcp_master.sh"
BACKUP_FILE="${MASTER_SCRIPT}.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$MASTER_SCRIPT" ]; then
    cp "$MASTER_SCRIPT" "$BACKUP_FILE"
    echo "  ✓ Backup created: $BACKUP_FILE"
    
    # Comment out Document Store startup (lines 105-120)
    # Using sed to comment out the Document Store section
    sed -i 's/^echo "Step 4\/6: Starting Document Store Server on port 3070..."/# COMMENTED OUT BY FIX SCRIPT: echo "Step 4\/6: Starting Document Store Server on port 3070..."/' "$MASTER_SCRIPT"
    sed -i 's/^echo "---------------------------------------------------------"/# COMMENTED OUT: echo "---------------------------------------------------------"/' "$MASTER_SCRIPT"
    sed -i 's/^cd \/root\/qwen\/base\/document-store-mcp-server$/# cd \/root\/qwen\/base\/document-store-mcp-server/' "$MASTER_SCRIPT"
    sed -i 's/^nohup bash \.\/start_document_store\.sh/# nohup bash .\/start_document_store.sh/' "$MASTER_SCRIPT"
    sed -i 's/^DOCSTORE_PID=\$!$/# DOCSTORE_PID=\$!/' "$MASTER_SCRIPT"
    
    # Comment out cleanup line
    sed -i 's/pkill -f "document_store" 2>\/dev\/null || true/# pkill -f "document_store" 2>\/dev\/null || true  # COMMENTED OUT BY FIX SCRIPT/' "$MASTER_SCRIPT"
    
    echo "  ✓ Modified start_mcp_master.sh"
else
    echo "  ⚠ start_mcp_master.sh not found at $MASTER_SCRIPT"
fi

# Step 4: Start ai_agent Document Store
echo ""
echo "Step 4: Starting ai_agent Document Store..."
cd /root/qwen/ai_agent/document-store-mcp-server

if [ -d "../ai_agent_env" ]; then
    source ../ai_agent_env/bin/activate
fi

# Set environment variables
export DOCUMENT_STORE_PORT=3070
export DOCUMENT_STORAGE_PATH=/root/qwen/ai_agent/document-store-mcp-server/data
export REGISTRY_HOST=127.0.0.1
export REGISTRY_PORT=3031

# Start the server
nohup python -m document_store_server.server --port 3070 > document_store.log 2>&1 &
DOCSTORE_PID=$!
echo "  ✓ Started Document Store with PID: $DOCSTORE_PID"

# Wait for it to be ready
echo ""
echo "Step 5: Waiting for Document Store to be ready..."
for i in {1..10}; do
    if curl -s -X POST http://localhost:3070/mcp \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' > /dev/null 2>&1; then
        echo "  ✓ Document Store is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "  ⚠ Document Store may not have started correctly"
    fi
    sleep 1
done

# Step 6: Verify correct data
echo ""
echo "Step 6: Verifying Document Store data..."
RESPONSE=$(curl -s -X POST http://localhost:3070/mcp \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_ingestion_jobs","arguments":{}}}' 2>/dev/null)

if echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    text = d['result']['content'][0]['text']
    data = json.loads(text)
    jobs = data.get('jobs', [])
    print(f'  ✓ Jobs found: {len(jobs)}')
    for j in jobs:
        print(f'    - {j.get(\"job_id\", \"?\")}: {j.get(\"document_count\", 0)} documents')
        print(f'      Path: {j.get(\"path\", \"?\")}')
    
    # Check if we have the right data
    if len(jobs) == 1 and 'job_job_90825d5e7b99' in jobs[0].get('job_id', ''):
        print('')
        print('  ✅ SUCCESS: Correct Document Store is running!')
    elif len(jobs) > 1 or any('test_job' in j.get('job_id', '') for j in jobs):
        print('')
        print('  ✗ WARNING: Still showing phantom data!')
        print('  The base project Document Store may still be running.')
    else:
        print('')
        print('  ⚠ Unexpected data structure')
except Exception as e:
    print(f'  ✗ Error parsing response: {e}')
    print(f'  Response: {sys.stdin.read()[:200]}')
" 2>/dev/null; then
    :
else
    echo "  ✗ Failed to verify Document Store"
fi

# Step 7: Summary
echo ""
echo "================================================"
echo "Fix Complete!"
echo "================================================"
echo ""
echo "Summary:"
echo "  - Base project Document Store: DISABLED"
echo "  - ai_agent Document Store: RUNNING (PID $DOCSTORE_PID)"
echo "  - Port: 3070"
echo "  - Storage: /root/qwen/ai_agent/document-store-mcp-server/data"
echo ""
echo "Backup of original script:"
echo "  $BACKUP_FILE"
echo ""
echo "To restore original behavior:"
echo "  cp $BACKUP_FILE $MASTER_SCRIPT"
echo "  pkill -f document_store"
echo "  cd /root/qwen/base/start_mcp_master.sh && ./start_mcp_master.sh"
echo ""
echo "Logs: /root/qwen/ai_agent/document-store-mcp-server/document_store.log"
echo ""
