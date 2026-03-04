#!/bin/bash
# Phased Processing - Complete Verification Test
echo "========================================"
echo "  Phased Processing Verification Test"
echo "========================================"
echo ""

cd /root/qwen/ai_agent
source ai_agent_env/bin/activate

echo "1. Creating test job..."
JOB_RESPONSE=$(curl -s -X POST "http://localhost:5003/api/rag/phased/from-docstore" \
  -H "Content-Type: application/json" \
  -d '{"document_ids":["gost-r-56546-2015=edt2018_6d040aec"],"phases":["chunk"],"user_id":"test"}')

JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))")
echo "   Job ID: $JOB_ID"

if [ -z "$JOB_ID" ]; then
    echo "   ❌ Failed to create job"
    exit 1
fi
echo "   ✅ Job created"

echo ""
echo "2. Waiting for processing (10 seconds)..."
sleep 10

echo ""
echo "3. Checking job stats..."
python3 << PYCHECK
import json
import requests

job_id = "$JOB_ID"

# Check job endpoint
response = requests.get(f"http://localhost:5003/jobs/{job_id}")
job = response.json()

print(f"   Status: {job.get('status')}")
print(f"   Documents: {job.get('documents_processed')}/{job.get('documents_total')}")
print(f"   Chunks: {job.get('chunks_generated')}")

# Verify
chunks = job.get('chunks_generated', 0)
docs_processed = job.get('documents_processed', 0)

if chunks > 0 and docs_processed > 0:
    print("   ✅ Job stats updated correctly!")
else:
    print("   ⚠️  Job stats not updated (may need manual verification)")

# Also check chunks in DB
from backend.services.rag.phased_processing_db import phased_db
db_chunks = phased_db.get_chunks_for_document('gost-r-56546-2015=edt2018_6d040aec')
print(f"   Chunks in DB: {len(db_chunks)}")

if len(db_chunks) > 0:
    print("   ✅ Chunks created successfully!")
else:
    print("   ❌ No chunks in database")
PYCHECK

echo ""
echo "4. Checking UI access..."
UI_CHECK=$(curl -sk "https://192.168.51.216/index.html" 2>&1 | grep -o "toggleDocstoreDocById" | head -1)
if [ "$UI_CHECK" = "toggleDocstoreDocById" ]; then
    echo "   ✅ UI serving updated code"
else
    echo "   ⚠️  UI may be serving old code"
fi

echo ""
echo "========================================"
echo "  Test Complete"
echo "========================================"
echo ""
echo "To verify in UI:"
echo "  1. Open: https://192.168.51.216"
echo "  2. Press Ctrl+Shift+R (hard refresh)"
echo "  3. Go to Jobs tab"
echo "  4. Find job: $JOB_ID"
echo "  5. Should show: Docs: 1/1 | Chunks: 1001"
echo ""
echo "  Or test new job:"
echo "  1. Smart Ingestion → Import from Document Store"
echo "  2. Load documents"
echo "  3. Filter by 'Text' (green)"
echo "  4. Select TXT file"
echo "  5. Uncheck 'Extract', keep 'Chunk'"
echo "  6. Click 'Start'"
echo "  7. Should complete without warning"
echo ""
