#!/usr/bin/env bash
# Parallel Smart Chunking Test - Uses separate processes
# Each model runs in its own process with isolated environment

cd /root/qwen/ai_agent
source ai_agent_env/bin/activate

echo ""
echo "================================================================================"
echo "PARALLEL SMART CHUNKING TEST"
echo "================================================================================"
echo ""

# Verify document exists
TEST_DOC="/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md"
if [ ! -f "$TEST_DOC" ]; then
    echo "ERROR: Document not found: $TEST_DOC"
    exit 1
fi
echo "Document: $TEST_DOC"
echo ""

echo "Starting both models in separate processes..."
echo ""

# Start Mistral 119B test
(
    export RESPONSE_LLM_PROVIDER="LM Studio"
    export RESPONSE_LLM_MODEL="mistral-small-4-119b-2603"
    export RESPONSE_LLM_HOSTNAME="192.168.51.105"
    export RESPONSE_LLM_PORT="1234"
    export RESPONSE_LLM_API_PATH="/v1"
    
    echo "=== Mistral 119B Configuration ==="
    echo "Model: $RESPONSE_LLM_MODEL"
    echo "Host: $RESPONSE_LLM_HOSTNAME:$RESPONSE_LLM_PORT"
    echo "API: $RESPONSE_LLM_API_PATH"
    echo ""
    
    python3 -c "
import sys, os, time
sys.path.insert(0, '/root/qwen/ai_agent')
print(f'Python env MODEL: {os.environ.get(\"RESPONSE_LLM_MODEL\")}')
print(f'Python env HOST: {os.environ.get(\"RESPONSE_LLM_HOSTNAME\")}')
from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync
start = time.time()
success, chunks, error = chunk_document_with_llm_sync(
    file_path='/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md',
    prompt='', filename='r-1323565.1_881b0329.pdf', timeout=3600
)
elapsed = (time.time() - start) / 60
with_content = sum(1 for c in chunks if c.get('content')) if chunks else 0
print(f'Result: success={success}, chunks={len(chunks)}, with_content={with_content}, time={elapsed:.1f}min')
import json
with open('/root/qwen/ai_agent/mistral_119b_result.json', 'w') as f:
    json.dump({'success': success, 'chunks': len(chunks), 'with_content': with_content, 'elapsed': elapsed}, f)
"
) > /root/qwen/ai_agent/chunking_mistral_119b.log 2>&1 &
MISTRAL_PID=$!

# Start Qwen 0.8B test  
(
    export RESPONSE_LLM_PROVIDER="LM Studio"
    export RESPONSE_LLM_MODEL="qwen3.5-0.8b@bf16"
    export RESPONSE_LLM_HOSTNAME="asus-tus"
    export RESPONSE_LLM_PORT="1234"
    export RESPONSE_LLM_API_PATH="/v1/chat/completions"
    
    echo "=== Qwen 0.8B Configuration ==="
    echo "Model: $RESPONSE_LLM_MODEL"
    echo "Host: $RESPONSE_LLM_HOSTNAME:$RESPONSE_LLM_PORT"
    echo "API: $RESPONSE_LLM_API_PATH"
    echo ""
    
    python3 -c "
import sys, os, time
sys.path.insert(0, '/root/qwen/ai_agent')
print(f'Python env MODEL: {os.environ.get(\"RESPONSE_LLM_MODEL\")}')
print(f'Python env HOST: {os.environ.get(\"RESPONSE_LLM_HOSTNAME\")}')
from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync
start = time.time()
success, chunks, error = chunk_document_with_llm_sync(
    file_path='/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md',
    prompt='', filename='r-1323565.1_881b0329.pdf', timeout=600
)
elapsed = (time.time() - start) / 60
with_content = sum(1 for c in chunks if c.get('content')) if chunks else 0
print(f'Result: success={success}, chunks={len(chunks)}, with_content={with_content}, time={elapsed:.1f}min')
import json
with open('/root/qwen/ai_agent/qwen_0.8b_result.json', 'w') as f:
    json.dump({'success': success, 'chunks': len(chunks), 'with_content': with_content, 'elapsed': elapsed}, f)
"
) > /root/qwen/ai_agent/chunking_qwen_0.8b.log 2>&1 &
QWEN_PID=$!

echo "✓ Mistral 119B PID: $MISTRAL_PID (host: 192.168.51.105)"
echo "✓ Qwen 0.8B PID: $QWEN_PID (host: asus-tus)"
echo ""
echo "Monitoring progress..."
echo ""

# Monitor both logs
while kill -0 $MISTRAL_PID 2>/dev/null || kill -0 $QWEN_PID 2>/dev/null; do
    echo "=== $(date '+%H:%M:%S') ==="
    echo "--- Mistral 119B (last 5 lines) ---"
    tail -5 /root/qwen/ai_agent/chunking_mistral_119b.log 2>/dev/null || echo "Starting..."
    echo ""
    echo "--- Qwen 0.8B (last 5 lines) ---"
    tail -5 /root/qwen/ai_agent/chunking_qwen_0.8b.log 2>/dev/null || echo "Starting..."
    echo ""
    sleep 30
done

# Wait for both to complete
wait $MISTRAL_PID 2>/dev/null
wait $QWEN_PID 2>/dev/null

echo ""
echo "================================================================================"
echo "TESTS COMPLETED"
echo "================================================================================"
echo ""
echo "=== Results ==="
echo "Mistral 119B:"
cat /root/qwen/ai_agent/mistral_119b_result.json 2>/dev/null && echo "" || echo "No results"
echo ""
echo "Qwen 0.8B:"
cat /root/qwen/ai_agent/qwen_0.8b_result.json 2>/dev/null && echo "" || echo "No results"
echo ""
