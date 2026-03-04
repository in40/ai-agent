"""
Background Job Queue for Smart Ingestion
Manages asynchronous processing of web pages and large document sets
"""
import os
import json
import uuid
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from flask import Flask, Blueprint, request, jsonify
from flask_cors import CORS
import redis

logger = logging.getLogger(__name__)

# Redis connection for job queue
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))

try:
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Connected to Redis for job queue")
except Exception as e:
    logger.warning(f"Redis not available, using in-memory storage: {e}")
    REDIS_AVAILABLE = False
    redis_client = None


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SmartIngestionJob:
    job_id: str
    user_id: str
    job_type: str  # 'web_page', 'file_upload', 'docstore', 'webpage_scan'
    status: str
    created_at: str
    updated_at: str
    expires_at: str
    parameters: Dict[str, Any]
    progress: int  # 0-100
    current_stage: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    documents_total: int
    documents_processed: int
    chunks_generated: int
    # Configuration tracking fields (optional for backward compatibility)
    ingestion_mode: str = 'files'  # 'files', 'webpage', 'docstore'
    processing_mode: str = 'vector_db'  # 'download_only', 'vector_db', 'hybrid'
    chunking_strategy: str = 'smart_chunking'  # 'smart_chunking', 'naive_chunking', 'section_based'
    source_url: Optional[str] = None  # For web page mode
    document_urls: Optional[List[str]] = None  # List of document URLs to process

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        # Only pass fields that are part of the dataclass
        # This handles cases where extra fields were added to Redis data
        valid_fields = {
            'job_id', 'user_id', 'job_type', 'status', 'created_at',
            'updated_at', 'expires_at', 'parameters', 'progress',
            'current_stage', 'result', 'error', 'documents_total',
            'documents_processed', 'chunks_generated', 'ingestion_mode',
            'processing_mode', 'chunking_strategy', 'source_url', 'document_urls'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class JobQueue:
    """Manages background job queue with Redis or in-memory fallback"""
    
    def __init__(self):
        self.jobs: Dict[str, SmartIngestionJob] = {}
        self.lock = threading.Lock()
        self.workers: Dict[str, threading.Thread] = {}
        
    def create_job(self, user_id: str, job_type: str, parameters: Dict[str, Any], 
                   ingestion_mode: str = 'files', processing_mode: str = 'vector_db',
                   chunking_strategy: str = 'smart_chunking', source_url: Optional[str] = None,
                   document_urls: Optional[List[str]] = None) -> SmartIngestionJob:
        """Create a new job"""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()

        job = SmartIngestionJob(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING.value,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            parameters=parameters,
            progress=0,
            current_stage="queued",
            result=None,
            error=None,
            documents_total=parameters.get('total_documents', 0),
            documents_processed=0,
            chunks_generated=0,
            ingestion_mode=ingestion_mode,
            processing_mode=processing_mode,
            chunking_strategy=chunking_strategy,
            source_url=source_url,
            document_urls=document_urls
        )
        
        # Store job
        if REDIS_AVAILABLE and redis_client:
            key = f"smart_ingestion_job:{job_id}"
            redis_client.setex(key, timedelta(hours=24), json.dumps(job.to_dict()))
            # Add to user's job list
            user_key = f"smart_ingestion_user_jobs:{user_id}"
            redis_client.lpush(user_key, job_id)
            redis_client.expire(user_key, timedelta(hours=24))
        else:
            with self.lock:
                self.jobs[job_id] = job
        
        logger.info(f"Created job {job_id} for user {user_id}")
        return job
    
    def get_job(self, job_id: str) -> Optional[SmartIngestionJob]:
        """Get job by ID"""
        if REDIS_AVAILABLE and redis_client:
            key = f"smart_ingestion_job:{job_id}"
            data = redis_client.get(key)
            if data:
                return SmartIngestionJob.from_dict(json.loads(data))
            return None
        else:
            with self.lock:
                return self.jobs.get(job_id)
    
    def update_job(self, job: SmartIngestionJob):
        """Update job status (Redis + PostgreSQL for long-term storage)"""
        job.updated_at = datetime.utcnow().isoformat()

        # Update in Redis
        if REDIS_AVAILABLE and redis_client:
            key = f"smart_ingestion_job:{job.job_id}"
            redis_client.setex(key, timedelta(hours=24), json.dumps(job.to_dict()))
        else:
            with self.lock:
                self.jobs[job.job_id] = job
        
        # Also save to PostgreSQL for long-term storage
        try:
            from .hybrid_job_storage import hybrid_storage
            hybrid_storage.save_job(job, save_to_db=True)
        except ImportError:
            logger.debug("Hybrid storage not available, using Redis only")
    
    def get_user_jobs(self, user_id: str, limit: int = 20) -> List[SmartIngestionJob]:
        """Get all jobs for a user"""
        if REDIS_AVAILABLE and redis_client:
            user_key = f"smart_ingestion_user_jobs:{user_id}"
            job_ids = redis_client.lrange(user_key, 0, limit - 1)
            jobs = []
            for job_id in job_ids:
                job = self.get_job(job_id)
                if job:
                    jobs.append(job)
            return jobs
        else:
            with self.lock:
                user_jobs = [j for j in self.jobs.values() if j.user_id == user_id]
                user_jobs.sort(key=lambda x: x.created_at, reverse=True)
                return user_jobs[:limit]

    def get_all_jobs(self, limit: int = 100) -> List[SmartIngestionJob]:
        """Get all jobs (for admin/import purposes)"""
        jobs = []
        
        if REDIS_AVAILABLE and redis_client:
            # Get all job keys
            job_keys = redis_client.keys("smart_ingestion_job:*")
            for key in job_keys[:limit]:
                job_id = key.decode('utf-8').replace("smart_ingestion_job:", "") if isinstance(key, bytes) else key.replace("smart_ingestion_job:", "")
                # Jobs are stored as JSON strings
                job_json = redis_client.get(key)
                if job_json:
                    try:
                        job_data = json.loads(job_json)
                        job = SmartIngestionJob.from_dict(job_data)
                        jobs.append(job)
                    except Exception as e:
                        logger.warning(f"Failed to parse job {job_id}: {e}")
        else:
            # Fallback to in-memory storage
            with self.lock:
                jobs = list(self.jobs.values())
        
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]

    def list_jobs(self, limit: int = 100) -> List[Dict]:
        """List all jobs as dictionaries"""
        jobs = self.get_all_jobs(limit)
        return [job.to_dict() for job in jobs]

    def start_worker(self, job_id: str, process_func):
        """Start background worker for a job"""
        logger.info(f"[JobQueue] Starting worker for job {job_id}")
        
        def worker():
            logger.info(f"[JobQueue] Worker thread started for job {job_id}")
            try:
                job = self.get_job(job_id)
                logger.info(f"[JobQueue] Retrieved job {job_id}: status={job.status if job else 'None'}")
                
                if not job or job.status != JobStatus.PENDING.value:
                    logger.warning(f"[JobQueue] Job {job_id} not in PENDING status, skipping")
                    return

                # Update status to processing
                job.status = JobStatus.PROCESSING.value
                job.current_stage = "initializing"
                self.update_job(job)
                logger.info(f"[JobQueue] Job {job_id} status updated to PROCESSING")

                # Execute processing function
                result = process_func(job)
                logger.info(f"[JobQueue] Job {job_id} processing completed")

                # Update job status - preserve any data fields updated by process_func
                # Get current job state from Redis (may have been updated by process_func)
                current_job = self.get_job(job_id)
                if current_job:
                    # Only update status fields, preserve data fields
                    current_job.status = JobStatus.COMPLETED.value
                    current_job.progress = 100
                    current_job.current_stage = "completed"
                    if result:  # Only set result if it's not None/empty
                        current_job.result = result
                    self.update_job(current_job)
                logger.info(f"[JobQueue] Job {job_id} marked as COMPLETED")

                logger.info(f"Job {job_id} completed successfully")

            except Exception as e:
                logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
                job = self.get_job(job_id)
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error = str(e)
                    self.update_job(job)
        
        thread = threading.Thread(target=worker, daemon=True, name=f"job-worker-{job_id}")
        thread.start()
        logger.info(f"[JobQueue] Worker thread for job {job_id} started successfully (thread={thread.name})")
        self.workers[job_id] = thread
        return thread


# Global job queue instance
job_queue = JobQueue()


# Flask blueprint for job management API
jobs_bp = Blueprint('jobs', __name__)
CORS_ENABLED = True


@jobs_bp.route('/jobs', methods=['POST'])
def create_job():
    """Create a new background job"""
    try:
        data = request.get_json()

        user_id = data.get('user_id', 'anonymous')
        job_type = data.get('job_type', 'web_page')
        parameters = data.get('parameters', {})

        if not parameters:
            return jsonify({'error': 'Parameters are required'}), 400

        job = job_queue.create_job(user_id, job_type, parameters)

        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'message': 'Job created successfully',
            'check_status_url': f'/jobs/{job.job_id}'
        }), 201

    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (with optional historical jobs from database)"""
    try:
        # Check if user wants historical jobs
        include_historical = request.args.get('historical', 'true').lower() == 'true'
        limit = request.args.get('limit', 100, type=int)
        
        # Use hybrid storage if available
        try:
            from .hybrid_job_storage import hybrid_storage
            jobs = hybrid_storage.get_all_jobs(limit=limit, include_historical=include_historical)
            return jsonify({'jobs': [job.to_dict() for job in jobs], 'count': len(jobs)}), 200
        except ImportError:
            # Fallback to Redis-only
            jobs = job_queue.list_jobs(limit=limit)
            return jsonify({'jobs': jobs, 'count': len(jobs)}), 200
            
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/jobs/user/<user_id>', methods=['GET'])
def get_user_jobs(user_id):
    """Get all jobs for a user (including historical from database)"""
    try:
        # Check if user wants historical jobs
        include_historical = request.args.get('historical', 'true').lower() == 'true'
        limit = request.args.get('limit', 50, type=int)
        
        # Use hybrid storage if available
        try:
            from .hybrid_job_storage import hybrid_storage
            jobs = hybrid_storage.get_user_jobs(
                user_id=user_id, 
                limit=limit, 
                include_historical=include_historical
            )
            return jsonify({'jobs': [job.to_dict() for job in jobs], 'count': len(jobs)}), 200
        except ImportError:
            # Fallback to Redis-only
            jobs = job_queue.get_user_jobs(user_id, limit)
            return jsonify({'jobs': [job.to_dict() for job in jobs], 'count': len(jobs)}), 200
            
    except Exception as e:
        logger.error(f"Error getting user jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress (including processed files if available)"""
    try:
        # Try to get from hybrid storage
        try:
            from .hybrid_job_storage import hybrid_storage
            job = hybrid_storage.get_job(job_id)
        except ImportError:
            job = job_queue.get_job(job_id)

        if not job:
            return jsonify({'error': 'Job not found'}), 404

        response_data = {
            'job_id': job.job_id,
            'job_type': job.job_type,
            'ingestion_mode': job.ingestion_mode,
            'processing_mode': job.processing_mode,
            'chunking_strategy': job.chunking_strategy,
            'source_url': job.source_url,
            'status': job.status,
            'progress': job.progress,
            'current_stage': job.current_stage,
            'created_at': job.created_at,
            'updated_at': job.updated_at,
            'documents_total': job.documents_total,
            'documents_processed': job.documents_processed,
            'chunks_generated': job.chunks_generated,
            'result': job.result,
            'error': job.error
        }

        # Try to get processed files from database
        try:
            from database.utils.database import get_db_connection
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            id, original_filename, file_format, file_size_bytes,
                            status, extraction_method, extraction_time_seconds,
                            text_length, cyrillic_ratio, encoding_was_fixed,
                            chunks_created, error_message
                        FROM ingestion_job_files
                        WHERE job_id = %s
                        ORDER BY id
                    """, (job_id,))
                    
                    files = []
                    for row in cur.fetchall():
                        files.append({
                            'id': row[0],
                            'filename': row[1],
                            'format': row[3],
                            'size_bytes': row[4],
                            'status': row[5],
                            'extraction_method': row[6],
                            'extraction_time': row[7],
                            'text_length': row[8],
                            'cyrillic_ratio': row[9],
                            'encoding_fixed': row[10],
                            'chunks_created': row[11],
                            'error': row[12]
                        })
                    
                    response_data['files'] = files
                    response_data['files_count'] = len(files)
        except Exception as e:
            logger.debug(f"Could not load job files: {e}")
            response_data['files'] = []
            response_data['files_count'] = 0

        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/jobs/<job_id>/cancel', methods=['POST'])
def cancel_job(job_id):
    """Cancel a pending or processing job"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        return jsonify({'error': 'Cannot cancel completed/failed job'}), 400
    
    job.status = JobStatus.CANCELLED.value
    job.current_stage = "cancelled"
    job_queue.update_job(job)
    
    return jsonify({'message': 'Job cancelled successfully'}), 200


@jobs_bp.route('/jobs/cleanup', methods=['POST'])
def cleanup_old_jobs():
    """
    Clean up old jobs from Redis (PostgreSQL keeps permanent record)
    
    Request JSON (optional):
    {
        "days_to_keep": 7,  // Keep jobs newer than this (default: 7 days)
        "dry_run": true     // Don't actually delete, just report (default: false)
    }
    
    Response:
    {
        "jobs_scanned": 100,
        "jobs_deleted": 25,
        "jobs_older_than": "2026-02-22"
    }
    """
    try:
        from datetime import datetime, timedelta
        
        data = request.get_json() or {}
        days_to_keep = data.get('days_to_keep', 7)
        dry_run = data.get('dry_run', False)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        jobs_scanned = 0
        jobs_deleted = 0
        
        if REDIS_AVAILABLE and redis_client:
            # Get all job keys
            job_keys = redis_client.keys("smart_ingestion_job:*")
            
            for key in job_keys:
                jobs_scanned += 1
                job_json = redis_client.get(key)
                
                if job_json:
                    try:
                        job_data = json.loads(job_json)
                        created_at = job_data.get('created_at', '')
                        
                        # Compare dates (ISO format strings can be compared lexicographically)
                        if created_at < cutoff_str:
                            if not dry_run:
                                redis_client.delete(key)
                            jobs_deleted += 1
                    except Exception as e:
                        logger.warning(f"Failed to parse job: {e}")
        
        return jsonify({
            'success': True,
            'jobs_scanned': jobs_scanned,
            'jobs_deleted': jobs_deleted,
            'cutoff_date': cutoff_str,
            'days_to_keep': days_to_keep,
            'dry_run': dry_run,
            'message': f"Would delete {jobs_deleted} jobs older than {cutoff_str}" if dry_run else f"Deleted {jobs_deleted} old jobs"
        }), 200
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@jobs_bp.route('/jobs/stats', methods=['GET'])
def get_jobs_stats():
    """
    Get job statistics
    
    Response:
    {
        "total_jobs": 100,
        "by_status": {"completed": 80, "failed": 10, ...},
        "by_type": {"file_upload": 60, "web_page": 40},
        "recent_jobs": [...],
        "oldest_job_date": "2026-01-01",
        "postgres_jobs": 500  // Total in PostgreSQL
    }
    """
    try:
        from sqlalchemy import text, func
        from database.utils.database import get_db_manager
        
        stats = {
            'total_jobs': 0,
            'by_status': {},
            'by_type': {},
            'recent_jobs': [],
            'oldest_job_date': None,
            'redis_jobs': 0,
            'postgres_jobs': 0
        }
        
        # Get Redis stats
        if REDIS_AVAILABLE and redis_client:
            job_keys = redis_client.keys("smart_ingestion_job:*")
            stats['redis_jobs'] = len(job_keys)
            
            for key in job_keys:
                job_json = redis_client.get(key)
                if job_json:
                    try:
                        job_data = json.loads(job_json)
                        status = job_data.get('status', 'unknown')
                        job_type = job_data.get('job_type', 'unknown')
                        created_at = job_data.get('created_at')
                        
                        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                        stats['by_type'][job_type] = stats['by_type'].get(job_type, 0) + 1
                        stats['total_jobs'] += 1
                        
                        if created_at:
                            if not stats['oldest_job_date'] or created_at < stats['oldest_job_date']:
                                stats['oldest_job_date'] = created_at
                        
                        # Add to recent jobs (last 10)
                        if len(stats['recent_jobs']) < 10:
                            stats['recent_jobs'].append({
                                'job_id': job_data.get('job_id'),
                                'status': status,
                                'created_at': created_at
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse job: {e}")
        
        # Get PostgreSQL stats
        db_manager = get_db_manager()
        if db_manager:
            try:
                with db_manager.engine.connect() as conn:
                    # Total jobs
                    result = conn.execute(text("SELECT COUNT(*) FROM ingestion_jobs"))
                    stats['postgres_jobs'] = result.fetchone()[0]
                    
                    # By status
                    result = conn.execute(text("""
                        SELECT status, COUNT(*) 
                        FROM ingestion_jobs 
                        GROUP BY status
                    """))
                    for row in result.fetchall():
                        stats['by_status'][row[0]] = stats['by_status'].get(row[0], 0) + row[1]
                    
                    # By type
                    result = conn.execute(text("""
                        SELECT job_type, COUNT(*) 
                        FROM ingestion_jobs 
                        GROUP BY job_type
                    """))
                    for row in result.fetchall():
                        stats['by_type'][row[0]] = stats['by_type'].get(row[0], 0) + row[1]
                    
                    # Oldest job
                    result = conn.execute(text("SELECT MIN(created_at) FROM ingestion_jobs"))
                    oldest = result.fetchone()[0]
                    if oldest and (not stats['oldest_job_date'] or str(oldest) < stats['oldest_job_date']):
                        stats['oldest_job_date'] = str(oldest)
            except Exception as e:
                logger.debug(f"Could not get PostgreSQL stats: {e}")
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting job stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('JOB_QUEUE_PORT', 5006))
    app.run(host='0.0.0.0', port=port, debug=False)


@jobs_bp.route('/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Resume a stuck job by resetting it to pending status for chunking"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status not in [JobStatus.PROCESSING.value, JobStatus.CANCELLED.value]:
        return jsonify({'error': 'Can only resume processing/cancelled jobs'}), 400
    
    # Reset job to pending for chunking
    job.status = JobStatus.PENDING.value
    job.current_stage = "queued_for_chunking"
    job.progress = 25  # Reset to post-download stage
    job.error = None
    
    # Add recovery metadata
    if 'recovery_history' not in job.parameters:
        job.parameters['recovery_history'] = []
    job.parameters['recovery_history'].append({
        'action': 'resume',
        'timestamp': job.updated_at
    })
    
    job_queue.update_job(job)
    
    logger.info(f"Job {job_id} resumed (reset to pending for chunking)")
    
    return jsonify({
        'message': 'Job resumed successfully',
        'job_id': job_id,
        'new_status': job.status,
        'new_stage': job.current_stage
    }), 200


@jobs_bp.route('/jobs/<job_id>/retry_chunking', methods=['POST'])
def retry_chunking(job_id):
    """Retry chunking for a job from a specific document"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    data = request.get_json() or {}
    from_document = data.get('from_document', 0)
    skip_download = data.get('skip_download', True)
    
    # Reset chunking progress
    job.chunks_generated = 0
    job.current_stage = "chunking"
    job.progress = 30
    job.error = None
    
    # Add retry metadata
    job.parameters['chunking_retry'] = {
        'from_document': from_document,
        'skip_download': skip_download,
        'retry_timestamp': job.updated_at
    }
    
    job_queue.update_job(job)
    
    logger.info(f"Job {job_id} chunking retry initiated from document {from_document}")
    
    return jsonify({
        'message': 'Chunking retry initiated',
        'job_id': job_id,
        'from_document': from_document,
        'skip_download': skip_download
    }), 200


@jobs_bp.route('/jobs/<job_id>/activate', methods=['POST'])
def activate_job(job_id):
    """Activate a pending job"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != JobStatus.PENDING.value:
        return jsonify({'error': 'Job is not in pending status'}), 400
    
    # Job is already pending, just log the activation
    logger.info(f"Job {job_id} activated (already in pending status)")
    
    return jsonify({
        'message': 'Job is ready for processing',
        'job_id': job_id,
        'status': job.status
    }), 200


@jobs_bp.route('/jobs/<job_id>/retry', methods=['POST'])
def retry_failed_job(job_id):
    """Retry a failed job from the beginning"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status not in [JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
        return jsonify({'error': 'Can only retry failed/cancelled jobs'}), 400
    
    # Reset job completely
    job.status = JobStatus.PENDING.value
    job.current_stage = "queued"
    job.progress = 0
    job.chunks_generated = 0
    job.documents_processed = 0
    job.error = None
    job.result = None
    
    # Add retry metadata
    if 'retry_history' not in job.parameters:
        job.parameters['retry_history'] = []
    job.parameters['retry_history'].append({
        'action': 'retry_failed_job',
        'timestamp': job.updated_at,
        'previous_status': job.status
    })
    
    job_queue.update_job(job)
    
    logger.info(f"Job {job_id} retry initiated (reset to pending)")
    
    return jsonify({
        'message': 'Job retry initiated',
        'job_id': job_id,
        'new_status': job.status
    }), 200


@jobs_bp.route('/jobs/<job_id>/delete', methods=['DELETE'])
def delete_job(job_id):
    """Permanently delete a job from the database"""
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    # Store job info for logging
    job_status = job.status
    job_type = job.job_type
    chunks_generated = job.chunks_generated
    
    # Delete from Redis
    job_key = f"smart_ingestion_job:{job_id}"
    if redis_client and REDIS_AVAILABLE:
        redis_client.delete(job_key)
        # Also remove from user's job list
        user_key = f"smart_ingestion_user_jobs:{job.user_id}"
        redis_client.lrem(user_key, 0, job_id)
    else:
        # Fallback to in-memory deletion
        if job_id in job_queue.jobs:
            del job_queue.jobs[job_id]
    
    logger.info(f"Job {job_id} permanently deleted (status: {job_status}, type: {job_type}, chunks: {chunks_generated})")
    
    return jsonify({
        'message': 'Job permanently deleted',
        'job_id': job_id,
        'deleted_status': job_status,
        'chunks_removed': chunks_generated
    }), 200


@jobs_bp.route('/jobs/<job_id>/restart', methods=['POST'])
def restart_job(job_id):
    """
    Restart a job (cancel current and create new with same parameters)
    
    This deletes the current job and creates a new one with identical parameters.
    Useful when a job is stuck or you want to reprocess with current settings.
    """
    old_job = job_queue.get_job(job_id)

    if not old_job:
        return jsonify({'error': 'Job not found'}), 404

    # Can only restart completed, failed, or cancelled jobs
    if old_job.status not in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
        return jsonify({'error': 'Can only restart completed/failed/cancelled jobs'}), 400

    # Create new job with same parameters
    try:
        new_job = job_queue.create_job(
            user_id=old_job.user_id,
            job_type=old_job.job_type,
            parameters=old_job.parameters,
            ingestion_mode=old_job.ingestion_mode,
            processing_mode=old_job.processing_mode,
            chunking_strategy=old_job.chunking_strategy,
            source_url=old_job.source_url,
            document_urls=old_job.document_urls
        )

        logger.info(f"Job {job_id} restarted as {new_job.job_id}")

        # Start processing the new job
        _start_job_processing(new_job)

        return jsonify({
            'message': 'Job restarted successfully',
            'old_job_id': job_id,
            'new_job_id': new_job.job_id,
            'new_status': new_job.status
        }), 202

    except Exception as e:
        logger.error(f"Failed to restart job {job_id}: {e}")
        return jsonify({'error': f'Failed to restart job: {str(e)}'}), 500


def _start_job_processing(job):
    """Helper function to start job processing based on job type"""
    from .smart_ingestion_enhanced import _process_documents_internal
    import os

    if job.job_type == 'file_upload':
        # Define the processing function for file upload jobs
        def process_files_background(job):
            local_dir = job.parameters.get('local_file_dir', '/root/qwen/ai_agent/downloads')
            if os.path.exists(local_dir):
                pdf_files = [f for f in os.listdir(local_dir) if f.endswith('.pdf')]
                doc_urls = [f"file://{os.path.join(local_dir, f)}" for f in pdf_files[:116]]
            else:
                doc_urls = job.parameters.get('document_urls', [])

            return _process_documents_internal(
                document_urls=doc_urls,
                prompt=job.parameters.get('prompt', ''),
                ingest_chunks_flag=job.parameters.get('ingest_chunks', True),
                job=job
            )

        job_queue.start_worker(job.job_id, process_files_background)

    elif job.job_type == 'webpage_scan':
        # Define the processing function for web page jobs
        def process_webpage_background(job):
            source_url = job.source_url
            return _process_documents_internal(
                document_urls=[source_url] if source_url else [],
                prompt=job.parameters.get('prompt', ''),
                ingest_chunks_flag=job.parameters.get('ingest_chunks', True),
                job=job
            )

        job_queue.start_worker(job.job_id, process_webpage_background)

    elif job.job_type == 'smart_ingest_docstore':
        # Import and use the docstore processing function
        from .app import _process_smart_ingest_docstore
        job_queue.start_worker(job.job_id, _process_smart_ingest_docstore)

    elif job.job_type == 'phased_processing':
        # Import and use the phased processing function
        from .phased_processing_api import process_phased_job_background
        job_queue.start_worker(job.job_id, process_phased_job_background)


@jobs_bp.route('/jobs/<job_id>/start_processing', methods=['POST'])
def start_processing(job_id):
    """Start processing for a pending job with local files"""
    import os
    from backend.services.rag.smart_ingestion_enhanced import _process_documents_internal
    
    job = job_queue.get_job(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != JobStatus.PENDING.value:
        return jsonify({'error': 'Can only start pending jobs'}), 400
    
    # Check if we have local files
    local_file_dir = job.parameters.get('local_file_dir')
    local_files = job.parameters.get('local_files', False)
    
    # Define the processing function for this job
    def process_job_background(job: SmartIngestionJob):
        """Background processing function for local files"""
        local_dir = job.parameters.get('local_file_dir', '/root/qwen/ai_agent/downloads')
        
        # Get list of PDF files from the directory
        if os.path.exists(local_dir):
            pdf_files = [f for f in os.listdir(local_dir) if f.endswith('.pdf')]
            # Create file:// URLs that the processor can handle
            doc_urls = [f"file://{os.path.join(local_dir, f)}" for f in pdf_files[:116]]
        else:
            doc_urls = job.parameters.get('document_urls', [])
        
        return _process_documents_internal(
            document_urls=doc_urls,
            prompt=job.parameters.get('prompt', ''),
            ingest_chunks_flag=job.parameters.get('ingest_chunks', True),
            job=job
        )
    
    # Start the worker
    job_queue.start_worker(job.job_id, process_job_background)
    
    logger.info(f"Job {job_id} processing started with local files")
    
    return jsonify({
        'message': 'Job processing started',
        'job_id': job_id,
        'status': 'processing',
        'local_files': local_files
    }), 200
