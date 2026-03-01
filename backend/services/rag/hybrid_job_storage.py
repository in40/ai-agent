"""
Hybrid Job Storage Manager
Manages jobs in both Redis (fast, temporary) and PostgreSQL (permanent)
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from sqlalchemy import text

from backend.services.rag.job_queue import SmartIngestionJob, JobStatus, REDIS_AVAILABLE, redis_client

logger = logging.getLogger(__name__)

# Database imports
try:
    from database.utils.database import get_db_manager
    DB_AVAILABLE = True
    db_manager = get_db_manager()
except ImportError:
    logger.warning("Database module not available, using Redis only")
    DB_AVAILABLE = False
    db_manager = None


class HybridJobStorage:
    """Manages job storage in both Redis and PostgreSQL"""
    
    def __init__(self):
        self.redis_available = REDIS_AVAILABLE and redis_client
        self.db_available = DB_AVAILABLE and db_manager is not None
        logger.info(f"HybridJobStorage initialized: Redis={self.redis_available}, DB={self.db_available}")
    
    def save_job(self, job: SmartIngestionJob, save_to_db: bool = True):
        """
        Save job to both Redis (for active jobs) and PostgreSQL (for long-term storage)
        
        Args:
            job: Job object to save
            save_to_db: Whether to also save to PostgreSQL (default True)
        """
        job_dict = job.to_dict()
        
        # Always save to Redis if available (for fast access to active jobs)
        if self.redis_available:
            try:
                key = f"smart_ingestion_job:{job.job_id}"
                redis_client.setex(key, timedelta(hours=24), json.dumps(job_dict))
                
                # Update user job list
                user_key = f"smart_ingestion_user_jobs:{job.user_id}"
                redis_client.lrem(user_key, 0, job.job_id)
                redis_client.lpush(user_key, job.job_id)
                redis_client.expire(user_key, timedelta(hours=24))
                
                logger.debug(f"Saved job {job.job_id} to Redis")
            except Exception as e:
                logger.error(f"Failed to save job to Redis: {e}")
        
        # Save to PostgreSQL for long-term storage
        if save_to_db and self.db_available:
            try:
                self._save_job_to_db(job)
                logger.debug(f"Saved job {job.job_id} to PostgreSQL")
            except Exception as e:
                logger.error(f"Failed to save job to PostgreSQL: {e}")
    
    def _save_job_to_db(self, job: SmartIngestionJob):
        """Save job to PostgreSQL database"""
        if not db_manager:
            return
        
        try:
            with db_manager.engine.connect() as conn:
                # Check if job exists
                result = conn.execute(text("""
                    SELECT job_id FROM ingestion_jobs WHERE job_id = :job_id
                """), {'job_id': job.job_id})
                
                exists = result.fetchone() is not None
                
                if exists:
                    # Update existing job
                    conn.execute(text("""
                        UPDATE ingestion_jobs SET
                            status = :status,
                            updated_at = :updated_at,
                            progress = :progress,
                            current_stage = :current_stage,
                            documents_processed = :documents_processed,
                            chunks_generated = :chunks_generated,
                            result = :result,
                            error = :error,
                            completed_at = :completed_at
                        WHERE job_id = :job_id
                    """), {
                        'status': job.status,
                        'updated_at': datetime.utcnow().isoformat(),
                        'progress': job.progress,
                        'current_stage': job.current_stage,
                        'documents_processed': job.documents_processed,
                        'chunks_generated': job.chunks_generated,
                        'result': json.dumps(job.result) if job.result else None,
                        'error': job.error,
                        'completed_at': datetime.utcnow().isoformat() if job.status == JobStatus.COMPLETED.value else None,
                        'job_id': job.job_id
                    })
                else:
                    # Insert new job
                    conn.execute(text("""
                        INSERT INTO ingestion_jobs (
                            job_id, user_id, job_type, status, created_at, updated_at, expires_at,
                            ingestion_mode, processing_mode, chunking_strategy,
                            source_url, progress, current_stage,
                            documents_total, documents_processed, chunks_generated,
                            result, error
                        ) VALUES (
                            :job_id, :user_id, :job_type, :status, :created_at, :updated_at, :expires_at,
                            :ingestion_mode, :processing_mode, :chunking_strategy,
                            :source_url, :progress, :current_stage,
                            :documents_total, :documents_processed, :chunks_generated,
                            :result, :error
                        )
                    """), {
                        'job_id': job.job_id,
                        'user_id': job.user_id,
                        'job_type': job.job_type,
                        'status': job.status,
                        'created_at': job.created_at,
                        'updated_at': datetime.utcnow().isoformat(),
                        'expires_at': job.expires_at,
                        'ingestion_mode': job.ingestion_mode,
                        'processing_mode': job.processing_mode,
                        'chunking_strategy': job.chunking_strategy,
                        'source_url': job.source_url,
                        'progress': job.progress,
                        'current_stage': job.current_stage,
                        'documents_total': job.documents_total,
                        'documents_processed': job.documents_processed,
                        'chunks_generated': job.chunks_generated,
                        'result': json.dumps(job.result) if job.result else None,
                        'error': job.error
                    })
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save job to database: {e}")
    
    def get_job(self, job_id: str, from_redis_only: bool = False) -> Optional[SmartIngestionJob]:
        """
        Get job by ID
        
        Tries Redis first (fast), then falls back to PostgreSQL
        
        Args:
            job_id: Job ID to retrieve
            from_redis_only: If True, only check Redis (for active jobs)
        
        Returns:
            Job object or None if not found
        """
        # Try Redis first
        if self.redis_available:
            try:
                key = f"smart_ingestion_job:{job_id}"
                job_json = redis_client.get(key)
                if job_json:
                    job_data = json.loads(job_json)
                    return SmartIngestionJob.from_dict(job_data)
            except Exception as e:
                logger.error(f"Failed to get job from Redis: {e}")
        
        # If not in Redis or redis_only=False, try PostgreSQL
        if not from_redis_only and self.db_available:
            return self._get_job_from_db(job_id)
        
        return None
    
    def _get_job_from_db(self, job_id: str) -> Optional[SmartIngestionJob]:
        """Get job from PostgreSQL database"""
        if not db_manager:
            return None
        
        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM ingestion_jobs WHERE job_id = :job_id
                """), {'job_id': job_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                # Convert database row to SmartIngestionJob
                job_data = {
                    'job_id': row[0],
                    'user_id': row[1],
                    'job_type': row[2],
                    'status': row[3],
                    'created_at': row[4].isoformat() if row[4] else None,
                    'updated_at': row[5].isoformat() if row[5] else None,
                    'expires_at': row[6].isoformat() if row[6] else None,
                    'ingestion_mode': row[7],
                    'processing_mode': row[8],
                    'chunking_strategy': row[9],
                    'source_url': row[11],
                    'progress': row[13],
                    'current_stage': row[14],
                    'documents_total': row[15],
                    'documents_processed': row[16],
                    'chunks_generated': row[17],
                    'result': row[19],
                    'error': row[20],
                    'parameters': {}  # Default empty parameters
                }
                
                return SmartIngestionJob.from_dict(job_data)
                
        except Exception as e:
            logger.error(f"Failed to get job from database: {e}")
            return None
    
    def get_user_jobs(self, user_id: str, limit: int = 50, include_historical: bool = True) -> List[SmartIngestionJob]:
        """
        Get all jobs for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of jobs to return
            include_historical: If True, include old jobs from PostgreSQL
        
        Returns:
            List of Job objects
        """
        jobs = []
        job_ids_seen = set()
        
        # Get active jobs from Redis
        if self.redis_available:
            try:
                user_key = f"smart_ingestion_user_jobs:{user_id}"
                job_ids = redis_client.lrange(user_key, 0, limit - 1)
                
                for job_id in job_ids:
                    job = self.get_job(job_id, from_redis_only=True)
                    if job:
                        jobs.append(job)
                        job_ids_seen.add(job_id)
            except Exception as e:
                logger.error(f"Failed to get user jobs from Redis: {e}")
        
        # Get historical jobs from PostgreSQL
        if include_historical and self.db_available and len(jobs) < limit:
            try:
                historical_jobs = self._get_user_jobs_from_db(
                    user_id, 
                    limit - len(jobs),
                    exclude_job_ids=job_ids_seen
                )
                jobs.extend(historical_jobs)
            except Exception as e:
                logger.error(f"Failed to get historical jobs from database: {e}")
        
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return jobs[:limit]
    
    def _get_user_jobs_from_db(self, user_id: str, limit: int, exclude_job_ids: set = None) -> List[SmartIngestionJob]:
        """Get user jobs from PostgreSQL"""
        if not db_manager:
            return []
        
        try:
            with db_manager.engine.connect() as conn:
                if exclude_job_ids:
                    placeholders = ','.join([f':job_id_{i}' for i in range(len(exclude_job_ids))])
                    params = {'user_id': user_id, 'limit': limit}
                    for i, job_id in enumerate(exclude_job_ids):
                        params[f'job_id_{i}'] = job_id
                    
                    query = f"""
                        SELECT * FROM ingestion_jobs 
                        WHERE user_id = :user_id AND job_id NOT IN ({placeholders})
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text("""
                        SELECT * FROM ingestion_jobs 
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """), {'user_id': user_id, 'limit': limit})
                
                rows = result.fetchall()
                jobs = []
                for row in rows:
                    job_data = {
                        'job_id': row[0],
                        'user_id': row[1],
                        'job_type': row[2],
                        'status': row[3],
                        'created_at': row[4].isoformat() if row[4] else None,
                        'updated_at': row[5].isoformat() if row[5] else None,
                        'expires_at': row[6].isoformat() if row[6] else None,
                        'ingestion_mode': row[7],
                        'processing_mode': row[8],
                        'chunking_strategy': row[9],
                        'source_url': row[11],
                        'progress': row[13],
                        'current_stage': row[14],
                        'documents_total': row[15],
                        'documents_processed': row[16],
                        'chunks_generated': row[17],
                        'result': row[19],
                        'error': row[20],
                        'parameters': {}
                    }
                    jobs.append(SmartIngestionJob.from_dict(job_data))
                
                return jobs
                
        except Exception as e:
            logger.error(f"Failed to get user jobs from database: {e}")
            return []
    
    def get_all_jobs(self, limit: int = 100, include_historical: bool = True) -> List[SmartIngestionJob]:
        """
        Get all jobs (admin view)
        
        Args:
            limit: Maximum number of jobs
            include_historical: Include old jobs from PostgreSQL
        
        Returns:
            List of Job objects
        """
        jobs = []
        
        # Get from Redis
        if self.redis_available:
            try:
                job_keys = redis_client.keys("smart_ingestion_job:*")
                for key in job_keys[:limit]:
                    job_json = redis_client.get(key)
                    if job_json:
                        job_data = json.loads(job_json)
                        jobs.append(SmartIngestionJob.from_dict(job_data))
            except Exception as e:
                logger.error(f"Failed to get all jobs from Redis: {e}")
        
        # Get from PostgreSQL
        if include_historical and self.db_available:
            try:
                with db_manager.engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT * FROM ingestion_jobs
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """), {'limit': limit - len(jobs)})
                    
                    rows = result.fetchall()
                    for row in rows:
                        job_data = {
                            'job_id': row[0],
                            'user_id': row[1],
                            'job_type': row[2],
                            'status': row[3],
                            'created_at': row[4].isoformat() if row[4] else None,
                            'updated_at': row[5].isoformat() if row[5] else None,
                            'expires_at': row[6].isoformat() if row[6] else None,
                            'ingestion_mode': row[7],
                            'processing_mode': row[8],
                            'chunking_strategy': row[9],
                            'source_url': row[11],
                            'progress': row[13],
                            'current_stage': row[14],
                            'documents_total': row[15],
                            'documents_processed': row[16],
                            'chunks_generated': row[17],
                            'result': row[19],
                            'error': row[20],
                            'parameters': {}
                        }
                        jobs.append(SmartIngestionJob.from_dict(job_data))
            except Exception as e:
                logger.error(f"Failed to get all jobs from database: {e}")
        
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]


# Global instance
hybrid_storage = HybridJobStorage()
