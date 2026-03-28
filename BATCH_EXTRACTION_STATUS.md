# PDF to Markdown Batch Extraction - Status & Operations Guide

**Last Updated:** 2026-03-19 06:45  
**Script:** `/root/qwen/ai_agent/batch_pdf_to_md.py`

---

## Current Status

| Metric | Value |
|--------|-------|
| **Completed** | 17 PDFs (15 original + 2 from Group 1) |
| **Remaining** | 98 PDFs |
| **Active Job** | `job_866dabdc2d59` - 1 PDF (`gost-34_35cf3ed7`) |
| **Configuration** | 1 PDF per job (resilient to interruptions) |

---

## Quick Commands

### Check Current Status
```bash
python3 -c "
import requests, os
DOC = '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents'
md = len([f for f in os.listdir(DOC) if f.endswith('.md')])
jobs = requests.get('http://localhost:5003/jobs').json().get('jobs', [])
proc = [j for j in jobs if j.get('status') == 'processing' and j.get('parameters', {}).get('phases') == ['extract']]
print(f'MD Files: {md} | Processing: {len(proc)}')
for j in proc:
    docs = j.get('parameters', {}).get('document_ids', [])
    print(f'  - {j.get(\"job_id\")[:20]}... ({len(docs)} PDFs)')
"
```

### Start/Resume Batch Script
```bash
source ai_agent_env/bin/activate
nohup python3 batch_pdf_to_md.py > /tmp/batch_conversion.log 2>&1 &
```

### Stop Batch Script
```bash
pkill -f batch_pdf_to_md.py
```

### Cancel a Stuck Job
```bash
curl -X POST http://localhost:5003/jobs/JOB_ID/cancel
```

### Check Remaining PDFs
```bash
python3 -c "
import os
DOC = '/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents'
done = {f[:-3] for f in os.listdir(DOC) if f.endswith('.md')}
todo = [f[:-4] for f in os.listdir(DOC) if f.endswith('.pdf') and f[:-4] not in done]
print(f'Remaining: {len(todo)}')
for t in todo[:10]: print(f'  - {t}')
"
```

---

## Known Issues

### 1. Jobs Get Stuck at "processing" with 0 Progress
**Symptom:** Job shows `status: processing`, `documents_processed: 0/1`, never completes

**Cause:** Background worker threads may not be processing jobs correctly

**Workaround:**
```bash
# Cancel stuck job
curl -X POST http://localhost:5003/jobs/JOB_ID/cancel

# Restart batch script (it will skip completed PDFs)
pkill -f batch_pdf_to_md.py
python3 batch_pdf_to_md.py
```

### 2. Script Doesn't Show Output in Log File
**Cause:** Python output buffering with nohup

**Fix:** Run with `-u` flag for unbuffered output:
```bash
nohup python3 -u batch_pdf_to_md.py > /tmp/batch_conversion.log 2>&1 &
```

---

## Script Behavior

### Resume Support
- Script automatically detects which PDFs already have `.md` files
- Skips completed PDFs on restart
- State saved to `batch_conversion_state.json`

### Job Configuration
- **1 PDF per job** (changed from 5 for better reliability)
- **LLM extraction only** (no PyMuPDF fallback)
- **5-minute polling interval** (saves API calls)
- **Max 1 concurrent job** (resilient to power outages)

### Expected Timing
- ~5-15 minutes per PDF (depends on LLM response)
- ~8-25 hours for all 98 remaining PDFs

---

## Monitoring Checklist

Every few hours, check:

- [ ] Script is running: `ps aux | grep batch_pdf_to_md`
- [ ] MD file count increasing: Should go from 17 → 115
- [ ] No stuck jobs: All processing jobs should complete within 20 min
- [ ] RAG service healthy: `curl http://localhost:5003/health`

---

## Troubleshooting

### All Jobs Stuck
```bash
# 1. Check RAG service
curl http://localhost:5003/health

# 2. If unhealthy, restart RAG service
# (Coordinate with team - affects other services)

# 3. Cancel all stuck jobs
curl -X POST http://localhost:5003/jobs/JOB_ID/cancel  # For each stuck job

# 4. Restart batch script
python3 batch_pdf_to_md.py
```

### Script Crashed
```bash
# Just restart - it will resume automatically
python3 batch_pdf_to_md.py
```

### Need to Change Concurrency
Edit `batch_pdf_to_md.py`:
```python
MAX_CONCURRENT_JOBS = 1  # Change to 2-4 for faster processing
```

---

## Files

| File | Purpose |
|------|---------|
| `batch_pdf_to_md.py` | Main orchestration script |
| `batch_conversion_state.json` | Resume state (completed groups) |
| `batch_conversion_summary.json` | Final summary (after completion) |
| `/tmp/batch_conversion.log` | Script output (if using nohup) |

---

## When Complete

Expected final state:
- **115 MD files** in document store
- **0 PDFs** without corresponding MD file
- Summary saved to `batch_conversion_summary.json`

To verify:
```bash
cd /root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents
echo "MD files: $(ls *.md | wc -l)"
echo "PDFs without MD: $(for p in *.pdf; do [ ! -f \"\${p%.pdf}.md\" ] && echo \$p; done | wc -l)"
```
