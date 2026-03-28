#!/usr/bin/env python3
"""
Simple Batch PDF to Markdown Conversion

Processes PDFs one at a time, waiting for each to complete before starting the next.
This avoids the complexity of job queue management and works reliably with Gunicorn.
"""
import os
import sys
import time
import requests
from datetime import datetime
from typing import List, Optional

# Configuration
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://localhost:5003')
USER_ID = "web_user"
POLL_INTERVAL = 30  # seconds

# Document store path
DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"

# State file
STATE_FILE = "/root/qwen/ai_agent/batch_simple_state.json"


def get_completed_pdfs() -> set:
    """Get list of PDFs that already have .md files"""
    completed = set()
    if os.path.exists(DOC_STORE_PATH):
        for f in os.listdir(DOC_STORE_PATH):
            if f.endswith('.md'):
                base = f[:-3]
                if os.path.exists(os.path.join(DOC_STORE_PATH, base + '.pdf')):
                    completed.add(base)
    return completed


def get_remaining_pdfs() -> List[str]:
    """Get list of PDFs that don't have .md files yet"""
    completed = get_completed_pdfs()
    all_pdfs = []
    if os.path.exists(DOC_STORE_PATH):
        for f in os.listdir(DOC_STORE_PATH):
            if f.endswith('.pdf'):
                base = f[:-4]
                if base not in completed:
                    all_pdfs.append(base)
    all_pdfs.sort()
    return all_pdfs


def load_state() -> dict:
    """Load state from file"""
    if os.path.exists(STATE_FILE):
        import json
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'completed': [], 'failed': [], 'current': None}


def save_state(state: dict):
    """Save state to file"""
    import json
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_active_job_count() -> int:
    """Get count of actively processing jobs (not pending)"""
    url = f"{RAG_SERVICE_URL}/jobs"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            # Only count jobs that are actually processing (not pending)
            # Pending jobs are just records, not actively using resources
            processing = [j for j in jobs if j.get('status') == 'processing']
            return len(processing)
    except:
        pass
    return 0


def wait_for_no_active_jobs():
    """Wait until there are no active jobs in the system"""
    iteration = 0
    while True:
        active = get_active_job_count()
        if active == 0:
            return
        
        if iteration % 10 == 0:
            print(f"  → Waiting for {active} active jobs to complete...")
        iteration += 1
        time.sleep(POLL_INTERVAL)


def create_extraction_job(pdf_id: str) -> Optional[str]:
    """Create extraction job for a single PDF"""
    # First, wait for any existing jobs to complete
    print("  Checking for active jobs...")
    wait_for_no_active_jobs()
    print("  No active jobs - starting new extraction")
    
    url = f"{RAG_SERVICE_URL}/api/rag/phased/from-docstore"
    payload = {
        "document_ids": [pdf_id],
        "phases": ["extract"],
        "user_id": USER_ID,
        "extraction_config": {
            "method": "llm",
            "page_range": "all"
        }
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get('job_id')
        else:
            print(f"  ✗ Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None


def get_job_status(job_id: str) -> dict:
    """Get job status"""
    url = f"{RAG_SERVICE_URL}/jobs/{job_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {'status': 'unknown'}
    except:
        return {'status': 'error'}


def wait_for_job(job_id: str, pdf_id: str) -> bool:
    """Wait for job to complete, checking for .md file creation"""
    start_time = datetime.now()
    iteration = 0
    
    while True:
        iteration += 1
        
        # Check if .md file was created (fastest completion detection)
        md_file = os.path.join(DOC_STORE_PATH, f"{pdf_id}.md")
        if os.path.exists(md_file):
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  ✓ Completed! ({elapsed:.0f}s) - .md file created")
            return True
        
        # Check job status
        job = get_job_status(job_id)
        status = job.get('status', 'unknown')
        stage = job.get('current_stage', 'unknown')
        
        if status in ['completed', 'done']:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  ✓ Completed! ({elapsed:.0f}s)")
            return True
        elif status in ['failed', 'error', 'cancelled']:
            print(f"  ✗ Failed: {job.get('error', 'unknown error')}")
            return False
        
        # Show progress
        if iteration % 10 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  → Still processing... ({elapsed:.0f}s) - stage: {stage}")
        
        time.sleep(POLL_INTERVAL)


def main():
    """Main processing loop"""
    remaining = get_remaining_pdfs()
    total = len(remaining)
    
    if total == 0:
        print("=" * 60)
        print("All PDFs already converted!")
        print("=" * 60)
        return 0
    
    state = load_state()
    completed_count = len(state.get('completed', []))
    failed_count = len(state.get('failed', []))
    
    print("=" * 60)
    print("Simple Batch PDF to Markdown Conversion")
    print("=" * 60)
    print(f"PDFs remaining: {total}")
    print(f"Previously completed: {completed_count}")
    print(f"Previously failed: {failed_count}")
    print(f"Poll interval: {POLL_INTERVAL}s")
    print("=" * 60)
    print()
    
    start_time = datetime.now()
    success_count = 0
    fail_count = 0
    
    for i, pdf_id in enumerate(remaining):
        group_num = completed_count + fail_count + i + 1
        print(f"[{group_num}/{total + completed_count + failed_count}] Processing: {pdf_id}")
        
        # Create job
        print("  Creating extraction job...")
        job_id = create_extraction_job(pdf_id)
        
        if not job_id:
            print(f"  ✗ Failed to create job")
            state['failed'].append({'pdf': pdf_id, 'error': 'job creation failed'})
            save_state(state)
            fail_count += 1
            continue
        
        print(f"  Job ID: {job_id}")
        state['current'] = {'pdf': pdf_id, 'job_id': job_id}
        save_state(state)
        
        # Wait for completion
        success = wait_for_job(job_id, pdf_id)
        
        if success:
            state['completed'].append({'pdf': pdf_id, 'job_id': job_id})
            success_count += 1
        else:
            state['failed'].append({'pdf': pdf_id, 'job_id': job_id})
            fail_count += 1
        
        state['current'] = None
        save_state(state)
        print()
    
    # Summary
    elapsed = datetime.now() - start_time
    print("=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"Total time: {elapsed.total_seconds() / 60:.1f} minutes")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print("=" * 60)
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
