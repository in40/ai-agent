# Job Submission & Monitoring Guide

## Overview

This guide explains how to use the batch extraction system for converting PDFs to markdown using LLM extraction.

---

## Quick Start

### 1. Start the Batch Conversion Script

```bash
source ai_agent_env/bin/activate
nohup python3 batch_pdf_to_md.py > /tmp/batch_conversion.log 2>&1 &
```

### 2. Monitor Script Activity

```bash
# Check if script is running
ps aux | grep batch_pdf_to_md.py

# View output log
tail -f /tmp/batch_conversion.log
```

### 3. Stop the Script

```bash
pkill -f batch_pdf_to_md.py
```

---

## Configuration

### Max Concurrent Jobs

The current setting is **2 concurrent jobs** (in `batch_pdf_to_md.py` line 18):

```python
MAX_CONCURRENT_JOBS = 2  # Change to 1 for reliability or higher for speed
```

> **Note:** Running 1 job at a time is recommended for power-outage resilience.

### Poll Interval

Jobs are polled every 5 minutes by default:

```python
POLL_INTERVAL_SECONDS = 300  # Change if needed
```

---

## Monitoring Commands

### Check Active Jobs

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

### View Job Status for Specific Job

```bash
curl http://localhost:5003/jobs/JOB_ID
```

### Check RAG Service Health

```bash
curl http://localhost:5003/health
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

## Troubleshooting

### Jobs Getting Stuck

If jobs show `status: processing` with 0 progress for >20 minutes:

```bash
# Cancel stuck job
curl -X POST http://localhost:5003/jobs/JOB_ID/cancel

# Restart script (will skip completed PDFs)
pkill -f batch_pdf_to_md.py
python3 batch_pdf_to_md.py
```

### All Jobs Stuck

```bash
# 1. Check RAG service health
curl http://localhost:5003/health

# 2. If unhealthy, restart RAG service

# 3. Cancel all stuck jobs
# Find jobs: python3 -c "import requests; print(requests.get('http://localhost:5003/jobs').json()['jobs'])"

# 4. Restart batch script
python3 batch_pdf_to_md.py
```

### Script Crashed

Simply restart:
```bash
python3 batch_pdf_to_md.py
```

The script automatically resumes from where it left off.

---

## Expected Progress

- **~5-15 minutes per PDF** (depends on LLM response time)
- **~8-25 hours** for all remaining PDFs
- Script output: `/tmp/batch_conversion.log`
- Final summary: `batch_conversion_summary.json`

---

## Files & State

| File | Purpose |
|------|---------|
| `batch_pdf_to_md.py` | Main script |
| `batch_conversion_state.json` | Resume state |
| `batch_conversion_summary.json` | Final results |
| `/tmp/batch_conversion.log` | Script output (when using nohup) |

---

## When Complete

Expected final state:
- **115 MD files** in document store
- **0 PDFs** without corresponding MD file

Verify:
```bash
cd /root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents
echo "MD files: $(ls *.md | wc -l)"
echo "PDFs without MD: \$(for p in *.pdf; do [ ! -f \"\${p%.pdf}.md\" ] && echo \$p; done | wc -l)"
```
