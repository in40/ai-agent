#!/usr/bin/env bash
# Parallel Smart Chunking Test - Uses separate processes with proper env isolation

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

# Create Python test script
cat > /tmp/test_chunking.py << 'PYEOF'
import sys, os, time, json
sys.path.insert(0, '/root/qwen/ai_agent')

model_name = os.environ.get('TEST_MODEL_NAME', 'unknown')
print(f"=== {model_name} ===")
print(f"MODEL: {os.environ.get('RESPONSE_LLM_MODEL')}")
print(f"HOST: {os.environ.get('RESPONSE_LLM_HOSTNAME')}")
print(f"PORT: {os.environ.get('RESPONSE_LLM_PORT')}")
print(f"API: {os.environ.get('RESPONSE_LLM_API_PATH')}")
print()

from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync

start = time.time()
success, chunks, error = chunk_document_with_llm_sync(
    file_path='/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/r-1323565.1_881b0329.md',
    prompt='', filename='r-1323565.1_881b0329.pdf', timeout=int(os.environ.get('TEST_TIMEOUT', '600'))
)
elapsed = (time.time() - start) / 60
with_content = sum(1 for c in chunks if c.get('content')) if chunks else 0

print(f"Result: success={success}, chunks={len(chunks)}, with_content={with_content}, time={elapsed:.1f}min")

result = {'model': model_name, 'success': success, 'chunks': len(chunks), 'with_content': with_content, 'elapsed': elapsed}
with open(os.environ.get('TEST_RESULT_FILE', '/tmp/result.json'), 'w') as f:
    json.dump(result, f, indent=2)
print(f"Saved: {os.environ.get('TEST_RESULT_FILE')}")
PYEOF

echo "Starting both models in separate processes..."
echo ""

# Start Mistral 119B test
(
    export RESPONSE_LLM_PROVIDER="LM Studio"
    export RESPONSE_LLM_MODEL="mistral-small-4-119b-2603"
    export RESPONSE_LLM_HOSTNAME="192.168.51.105"
    export RESPONSE_LLM_PORT="1234"
    export RESPONSE_LLM_API_PATH="/v1"
    export TEST_MODEL_NAME="Mistral 119B"
    export TEST_TIMEOUT="3600"
    export TEST_RESULT_FILE="/root/qwen/ai_agent/mistral_119b_result.json"
    
    python3 /tmp/test_chunking.py
) > /root/qwen/ai_agent/chunking_mistral_119b.log 2>&1 &
MISTRAL_PID=$!

# Start Qwen 0.8B test  
(
    export RESPONSE_LLM_PROVIDER="LM Studio"
    export RESPONSE_LLM_MODEL="qwen3.5-0.8b@bf16"
    export RESPONSE_LLM_HOSTNAME="asus-tus"
    export RESPONSE_LLM_PORT="1234"
    export RESPONSE_LLM_API_PATH="/v1/chat/completions"
    export TEST_MODEL_NAME="Qwen 0.8B"
    export TEST_TIMEOUT="600"
    export TEST_RESULT_FILE="/root/qwen/ai_agent/qwen_0.8b_result.json"
    
    python3 /tmp/test_chunking.py
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
    echo "--- Mistral 119B ---"
    tail -10 /root/qwen/ai_agent/chunking_mistral_119b.log 2>/dev/null
    echo ""
    echo "--- Qwen 0.8B ---"
    tail -10 /root/qwen/ai_agent/chunking_qwen_0.8b.log 2>/dev/null
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
