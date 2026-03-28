#!/usr/bin/env python3
"""
Batch PDF to Markdown Conversion Script (with smart recovery and monitoring)

Orchestrates LLM-based PDF extraction for documents in document store.
Enhanced with:
- Auto-recovery for stuck jobs (via /jobs/check-workers and /jobs/<id>/recover)
- Heartbeat monitoring to detect active LLM processing
- Smart polling intervals (30s when active, configurable wait between jobs)
- Max concurrent jobs with automatic capacity management
- Resume support from state file

Architecture:
- Creates jobs via /api/rag/phased/from-docstore
- Monitors via /jobs/<job_id>
- Detects stuck jobs via /jobs/check-workers
- Recovers stuck jobs via /jobs/<job_id>/recover
"""
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set

# Configuration
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://localhost:5003')
POLL_INTERVAL_ACTIVE = 30  # 30 seconds when jobs are running
POLL_INTERVAL_IDLE = 300  # 5 minutes when waiting for capacity
MAX_CONCURRENT_JOBS = int(os.getenv('MAX_CONCURRENT_JOBS', '2'))
USER_ID = "web_user"

# Job timeout configuration
JOB_HEARTBEAT_TIMEOUT = int(os.getenv('JOB_HEARTBEAT_TIMEOUT', '300'))  # 5 minutes without heartbeat = stuck (but only checked after 2x this time)
JOB_MAX_AGE = int(os.getenv('JOB_MAX_AGE', '7200'))  # 2 hours max job age

# Document store path
DOC_STORE_PATH = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents"

# State file for resume support
STATE_FILE = "/root/qwen/ai_agent/batch_conversion_state.json"


def get_completed_pdfs() -> set:
    """Get list of PDFs that already have .md files"""
    completed = set()
    if os.path.exists(DOC_STORE_PATH):
        for f in os.listdir(DOC_STORE_PATH):
            if f.endswith('.md'):
                base = f[:-3]  # Remove .md
                # Check if corresponding PDF exists
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
                base = f[:-4]  # Remove .pdf
                if base not in completed:
                    all_pdfs.append(base)
    
    # Sort for consistent ordering
    all_pdfs.sort()
    return all_pdfs


def load_state() -> Dict:
    """Load conversion state from file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'completed_groups': [], 'failed_groups': [], 'next_group': 0}


def save_state(state: Dict):
    """Save conversion state to file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchOrchestrator:
    def __init__(self):
        self.active_jobs: Dict[str, Dict] = {}  # job_id -> {group_num, start_time, pdfs}
        self.completed_jobs: List[Dict] = []
        self.failed_jobs: List[Dict] = []
        self.next_group_idx = 0
        self.state = load_state()
        
    def create_job(self, group_num: int, pdf_ids: List[str]) -> Optional[str]:
        """Create a new extraction job for a group of PDFs"""
        url = f"{RAG_SERVICE_URL}/api/rag/phased/from-docstore"
        
        payload = {
            "document_ids": pdf_ids,
            "phases": ["extract"],  # Only extraction, no chunking/vector/graph
            "user_id": USER_ID,
            "extraction_config": {
                "method": "llm",  # LLM only, no fallback
                "page_range": "all"
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                job_id = result.get('job_id')
                print(f"  ✓ Created job {job_id[:20]}... for Group {group_num} ({len(pdf_ids)} PDFs)")
                return job_id
            else:
                print(f"  ✗ Failed to create job for Group {group_num}: HTTP {response.status_code}")
                print(f"    Response: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"  ✗ Error creating job for Group {group_num}: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Optional[str]:
        """Check the status of a job"""
        url = f"{RAG_SERVICE_URL}/jobs/{job_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                job_data = response.json()
                return job_data.get('status')
            else:
                return None
        except Exception as e:
            print(f"  Warning: Could not check status for {job_id}: {e}")
            return None
    
    def start_next_job(self, remaining_pdfs: List[str]) -> bool:
        """Start next job with 1 PDF (for reliability)"""
        if not remaining_pdfs:
            return False
        
        # Take 1 PDF per job for better reliability and progress tracking
        batch_size = 1
        pdf_batch = remaining_pdfs[:batch_size]
        group_num = self.next_group_idx + 1
        
        job_id = self.create_job(group_num, pdf_batch)
        
        if job_id:
            self.active_jobs[job_id] = {
                'group_num': group_num,
                'pdfs': pdf_batch,
                'start_time': datetime.now()
            }
            self.next_group_idx += 1
            return True
        return False
    
    def poll_active_jobs(self) -> bool:
        """
        Poll all active jobs and update their status.
        Returns True if any job completed or failed.
        """
        changes = False
        completed_job_ids = []
        
        for job_id, job_info in list(self.active_jobs.items()):
            status = self.check_job_status(job_id)
            
            if status in [JobStatus.COMPLETED, "completed", "done"]:
                elapsed = datetime.now() - job_info['start_time']
                print(f"  ✓ Group {job_info['group_num']} COMPLETED ({elapsed.seconds // 60} min)")
                self.completed_jobs.append({
                    'job_id': job_id,
                    'group_num': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'elapsed_seconds': elapsed.total_seconds()
                })
                # Save state
                self.state['completed_groups'].append({
                    'group': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'job_id': job_id
                })
                save_state(self.state)
                completed_job_ids.append(job_id)
                changes = True
                
            elif status in [JobStatus.FAILED, "failed", "error"]:
                elapsed = datetime.now() - job_info['start_time']
                print(f"  ✗ Group {job_info['group_num']} FAILED ({elapsed.seconds // 60} min)")
                self.failed_jobs.append({
                    'job_id': job_id,
                    'group_num': job_info['group_num'],
                    'pdfs': job_info['pdfs']
                })
                self.state['failed_groups'].append({
                    'group': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'job_id': job_id
                })
                save_state(self.state)
                completed_job_ids.append(job_id)
                changes = True
        
        # Remove completed/failed jobs from active
        for job_id in completed_job_ids:
            del self.active_jobs[job_id]
        
        return changes

    def check_worker_health(self) -> Dict:
        """
        Check worker health via /jobs/check-workers endpoint.
        Returns dict with active_workers and orphaned_jobs.
        """
        url = f"{RAG_SERVICE_URL}/jobs/check-workers"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {'active_workers': 0, 'workers': [], 'orphaned_jobs': [], 'orphaned_count': 0}
        except Exception as e:
            print(f"  Warning: Could not check worker health: {e}")
            return {'active_workers': 0, 'workers': [], 'orphaned_jobs': [], 'orphaned_count': 0}

    def recover_stuck_job(self, job_id: str) -> bool:
        """
        Recover a stuck job via /jobs/<job_id>/recover endpoint.
        Returns True if recovery was successful.
        """
        url = f"{RAG_SERVICE_URL}/jobs/{job_id}/recover"
        try:
            response = requests.post(url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ Recovered stuck job {job_id[:20]}... (was {result.get('previous_stage', 'unknown')})")
                return True
            else:
                print(f"  ✗ Failed to recover job {job_id[:20]}...: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ Error recovering job {job_id[:20]}...: {e}")
            return False

    def is_job_stuck(self, job_id: str, job_info: Dict) -> tuple:
        """
        Check if a job is stuck based on:
        1. Job age exceeds JOB_MAX_AGE
        2. No heartbeat update for JOB_HEARTBEAT_TIMEOUT (but only after job has run for 2x timeout)
        3. Job is in 'processing' status but no progress
        
        Returns: (is_stuck, reason)
        """
        now = datetime.now()
        elapsed = now - job_info['start_time']
        elapsed_seconds = elapsed.total_seconds()
        
        # Check job age
        if elapsed_seconds > JOB_MAX_AGE:
            return True, f"Job age ({elapsed_seconds // 60} min) exceeds max ({JOB_MAX_AGE // 60} min)"
        
        # Only check heartbeat if job has been running for at least 2x the timeout
        # This prevents false positives when LLM is working on a large PDF
        min_age_for_heartbeat_check = JOB_HEARTBEAT_TIMEOUT * 2
        if elapsed_seconds < min_age_for_heartbeat_check:
            # Job hasn't run long enough to be considered stuck based on heartbeat
            return False, None
        
        # Check heartbeat
        last_heartbeat = job_info.get('last_heartbeat', job_info['start_time'])
        heartbeat_age = (now - last_heartbeat).total_seconds()
        if heartbeat_age > JOB_HEARTBEAT_TIMEOUT:
            return True, f"No heartbeat for {heartbeat_age // 60} min (timeout: {JOB_HEARTBEAT_TIMEOUT // 60} min)"
        
        return False, None

    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get detailed job info including heartbeat"""
        url = f"{RAG_SERVICE_URL}/jobs/{job_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"  Warning: Could not get details for {job_id}: {e}")
            return None

    def poll_active_jobs(self) -> bool:
        """
        Poll all active jobs and update their status.
        Enhanced with:
        - Heartbeat monitoring
        - Auto-recovery for stuck jobs
        - Check for .md file completion (faster than API status update)
        """
        changes = False
        completed_job_ids = []
        
        for job_id, job_info in list(self.active_jobs.items()):
            # First check if .md file was created (fastest completion detection)
            pdf_base = job_info['pdfs'][0] if job_info['pdfs'] else None
            if pdf_base:
                md_file = os.path.join(DOC_STORE_PATH, f"{pdf_base}.md")
                if os.path.exists(md_file):
                    elapsed = datetime.now() - job_info['start_time']
                    print(f"  ✓ Group {job_info['group_num']} COMPLETED ({elapsed.seconds // 60} min) - .md file detected")
                    self.completed_jobs.append({
                        'job_id': job_id,
                        'group_num': job_info['group_num'],
                        'pdfs': job_info['pdfs'],
                        'elapsed_seconds': elapsed.total_seconds()
                    })
                    # Save state
                    self.state['completed_groups'].append({
                        'group': job_info['group_num'],
                        'pdfs': job_info['pdfs'],
                        'job_id': job_id
                    })
                    save_state(self.state)
                    completed_job_ids.append(job_id)
                    changes = True
                    continue
            
            # Get detailed job info for heartbeat
            job_details = self.get_job_details(job_id)
            
            # Update heartbeat from job parameters
            if job_details and 'parameters' in job_details:
                heartbeat = job_details['parameters'].get('heartbeat', {})
                if heartbeat:
                    try:
                        hb_time = datetime.fromisoformat(heartbeat.get('timestamp', '').replace('Z', '+00:00'))
                        job_info['last_heartbeat'] = hb_time.replace(tzinfo=None)
                        job_info['heartbeat_phase'] = heartbeat.get('phase', 'unknown')
                        job_info['heartbeat_action'] = heartbeat.get('action', 'unknown')
                    except:
                        pass
            
            # Check if job is stuck (no heartbeat progress)
            # NOTE: We don't use orphaned detection via /jobs/check-workers because
            # worker_metadata is process-specific and doesn't work with Gunicorn workers
            is_stuck, reason = self.is_job_stuck(job_id, job_info)
            if is_stuck:
                print(f"  ⚠ Job {job_id[:20]}... appears stuck: {reason}")
                # Recover the job
                if self.recover_stuck_job(job_id):
                    print(f"  → Removing from active jobs, will restart")
                    completed_job_ids.append(job_id)
                    changes = True
                    continue
            
            # Check job status
            status = job_details.get('status') if job_details else None
            
            if status in [JobStatus.COMPLETED, "completed", "done"]:
                elapsed = datetime.now() - job_info['start_time']
                print(f"  ✓ Group {job_info['group_num']} COMPLETED ({elapsed.seconds // 60} min)")
                self.completed_jobs.append({
                    'job_id': job_id,
                    'group_num': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'elapsed_seconds': elapsed.total_seconds()
                })
                # Save state
                self.state['completed_groups'].append({
                    'group': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'job_id': job_id
                })
                save_state(self.state)
                completed_job_ids.append(job_id)
                changes = True

            elif status in [JobStatus.FAILED, "failed", "error"]:
                elapsed = datetime.now() - job_info['start_time']
                print(f"  ✗ Group {job_info['group_num']} FAILED ({elapsed.seconds // 60} min)")
                self.failed_jobs.append({
                    'job_id': job_id,
                    'group_num': job_info['group_num'],
                    'pdfs': job_info['pdfs']
                })
                self.state['failed_groups'].append({
                    'group': job_info['group_num'],
                    'pdfs': job_info['pdfs'],
                    'job_id': job_id
                })
                save_state(self.state)
                completed_job_ids.append(job_id)
                changes = True
            
            elif status == JobStatus.PROCESSING:
                # Show heartbeat status for active jobs
                if 'heartbeat_action' in job_info:
                    print(f"  → Group {job_info['group_num']}: {job_info['heartbeat_phase']}/{job_info['heartbeat_action']}")
                else:
                    # No heartbeat yet, show job age
                    elapsed = (datetime.now() - job_info['start_time']).total_seconds()
                    print(f"  → Group {job_info['group_num']}: processing for {elapsed:.0f}s")

        # Remove completed/failed/recovered jobs from active
        for job_id in completed_job_ids:
            del self.active_jobs[job_id]

        return changes
    
    def run(self):
        """Main orchestration loop with smart polling intervals"""
        # Get remaining PDFs
        remaining_pdfs = get_remaining_pdfs()
        total_remaining = len(remaining_pdfs)

        if total_remaining == 0:
            print("=" * 70)
            print("All PDFs already converted! Nothing to do.")
            print("=" * 70)
            return True

        print("=" * 70)
        print("PDF to Markdown Batch Conversion (Smart Recovery)")
        print("=" * 70)
        print(f"PDFs remaining: {total_remaining}")
        print(f"Max concurrent jobs: {MAX_CONCURRENT_JOBS}")
        print(f"Poll interval (active): {POLL_INTERVAL_ACTIVE}s")
        print(f"Poll interval (idle): {POLL_INTERVAL_IDLE}s")
        print(f"Job timeout: {JOB_HEARTBEAT_TIMEOUT // 60} min")
        print(f"RAG Service: {RAG_SERVICE_URL}")
        print("=" * 70)
        print()

        start_time = datetime.now()

        # Start first job
        print("Starting first job...")
        self.start_next_job(remaining_pdfs[self.next_group_idx:])
        print()

        # Main loop
        iteration = 0
        while self.active_jobs or (self.next_group_idx < total_remaining):
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Refresh remaining PDFs list (in case files were created externally)
            if iteration % 20 == 0:  # Every 20 iterations
                remaining_pdfs = get_remaining_pdfs()

            # Poll jobs
            print(f"[{timestamp}] Polling (iteration {iteration})...")
            print(f"  Active: {len(self.active_jobs)} | Completed: {len(self.completed_jobs)} | Failed: {len(self.failed_jobs)}")
            print(f"  Remaining PDFs: {total_remaining - self.next_group_idx}")

            has_changes = self.poll_active_jobs()

            # Start new job if capacity available
            if len(self.active_jobs) < MAX_CONCURRENT_JOBS:
                remaining = get_remaining_pdfs()
                if self.next_group_idx < len(remaining):
                    print("  Starting next job...")
                    self.start_next_job(remaining[self.next_group_idx:])

            # Check if we're done
            if not self.active_jobs and self.next_group_idx >= len(get_remaining_pdfs()):
                break

            # Smart polling: wait less when jobs are active, more when idle
            if self.active_jobs:
                wait_time = POLL_INTERVAL_ACTIVE
                status = "ACTIVE"
            else:
                wait_time = POLL_INTERVAL_IDLE
                status = "IDLE"
            
            print(f"  Status: {status} | Waiting {wait_time}s...")
            print()
            time.sleep(wait_time)

        # Final summary
        elapsed = datetime.now() - start_time
        print()
        print("=" * 70)
        print("BATCH CONVERSION COMPLETE")
        print("=" * 70)
        print(f"Total time: {elapsed.seconds // 60} minutes")
        print(f"Completed: {len(self.completed_jobs)} groups")
        print(f"Failed: {len(self.failed_jobs)} groups")
        print()

        if self.completed_jobs:
            print("Completed Jobs:")
            for job in self.completed_jobs:
                print(f"  ✓ Group {job['group_num']}: {job['job_id'][:20]}... ({len(job['pdfs'])} PDFs)")

        if self.failed_jobs:
            print()
            print("Failed Jobs:")
            for job in self.failed_jobs:
                print(f"  ✗ Group {job['group_num']}: {job['job_id'][:20]}... ({len(job['pdfs'])} PDFs)")

        print("=" * 70)

        # Save summary to file
        summary = {
            'completed_at': datetime.now().isoformat(),
            'total_time_seconds': elapsed.total_seconds(),
            'completed': self.completed_jobs,
            'failed': self.failed_jobs,
            'total_groups': self.next_group_idx
        }

        summary_file = "/root/qwen/ai_agent/batch_conversion_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"Summary saved to: {summary_file}")

        return len(self.failed_jobs) == 0


if __name__ == "__main__":
    orchestrator = BatchOrchestrator()
    success = orchestrator.run()
    sys.exit(0 if success else 1)
