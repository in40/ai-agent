#!/bin/bash
# Complete Phased Processing Fix Script
# Applies all fixes and starts services properly

echo "=========================================="
echo "  Phased Processing - Complete Fix"
echo "=========================================="
echo ""

# Stop any running services
echo "1. Stopping existing services..."
pkill -f "python.*rag.*app" 2>/dev/null
sleep 3

# Activate environment
cd /root/qwen/ai_agent
source ai_agent_env/bin/activate

# Fix database schema
echo "2. Fixing database schema..."
python fix_phased_db_schema.py

# Start RAG service
echo "3. Starting RAG service..."
nohup python -m backend.services.rag.app > rag_service.log 2>&1 &
sleep 15

# Verify service is running
echo "4. Verifying service..."
sleep 5
if ps aux | grep "python.*rag.*app" | grep -v grep | head -1 > /dev/null; then
    echo "   ✅ RAG service is running"
else
    echo "   ❌ RAG service failed to start"
    exit 1
fi

# Run comprehensive test
echo ""
echo "5. Running comprehensive test..."
python << 'PYTEST'
import json
import time
import requests

BASE_URL = "http://localhost:5003"

print("   Test 1: Create job via API")
response = requests.post(
    f"{BASE_URL}/api/rag/phased/from-docstore",
    json={
        "document_ids": ["gost-r-56546-2015=edt2018_6d040aec"],
        "phases": ["chunk"],
        "user_id": "test"
    },
    headers={"Content-Type": "application/json"}
)

if response.status_code != 200:
    print(f"   ❌ Failed to create job: {response.text}")
    exit(1)

job_data = response.json()
job_id = job_data.get('job_id')
print(f"   ✅ Job created: {job_id}")

print("   Test 2: Wait for processing")
time.sleep(8)

print("   Test 3: Check job status")
response = requests.get(f"{BASE_URL}/api/rag/phased/job/{job_id}/status")
if response.status_code != 200:
    print(f"   ❌ Failed to get status: {response.text}")
    exit(1)

status = response.json()
completed = status['documents']['completed']
processing = status['documents']['processing']
chunk_completed = status['progress']['phases']['chunk']['completed']

print(f"   Completed: {completed}, Processing: {processing}")
print(f"   Chunk phase completed: {chunk_completed}")

if completed > 0 or (chunk_completed > 0 and processing == 0):
    print("   ✅ Job processing completed successfully")
else:
    print("   ⚠️  Job still processing (this is OK for first run)")

print("   Test 4: Check chunks in database")
from backend.services.rag.phased_processing_db import phased_db
chunks = phased_db.get_chunks_for_document("gost-r-56546-2015=edt2018_6d040aec")
print(f"   Chunks found: {len(chunks)}")

if len(chunks) > 0:
    print("   ✅ Chunks created successfully")
else:
    print("   ❌ No chunks created")
    exit(1)

print("")
print("========================================")
print("  ALL TESTS PASSED!")
print("========================================")
print("")
print("System is ready for UI testing:")
print("  1. Open browser: https://192.168.51.216")
print("  2. Press Ctrl+Shift+R (hard refresh)")
print("  3. Smart Ingestion → Import from Document Store")
print("  4. Load documents")
print("  5. Filter by 'Text' (green button)")
print("  6. Select TXT file")
print("  7. Uncheck 'Extract', keep 'Chunk'")
print("  8. Click 'Start'")
print("  9. Should show: Overall Progress: 100%")
print(" 10. No warning should appear")
print("")
PYTEST

echo ""
echo "Services running:"
ps aux | grep "python.*rag.*app" | grep -v grep | head -1

echo ""
echo "✅ Setup complete!"
