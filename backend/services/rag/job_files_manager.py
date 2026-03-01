"""
Job Files Manager
Tracks individual files processed within ingestion jobs
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import text

logger = logging.getLogger(__name__)

try:
    from database.utils.database import get_db_manager
    DB_AVAILABLE = True
except ImportError:
    logger.warning("Database module not available")
    DB_AVAILABLE = False
    get_db_manager = None


def save_job_file(
    job_id: str,
    filename: str,
    file_format: str,
    file_size: int = 0,
    file_path: str = None,
    status: str = 'pending',
    extraction_method: str = None,
    extraction_time: float = None,
    text_length: int = None,
    cyrillic_ratio: float = None,
    encoding_was_fixed: bool = False,
    chunks_created: int = 0,
    error_message: str = None
) -> Optional[int]:
    """
    Save a processed file to the database
    
    Returns:
        file_id if successful, None otherwise
    """
    if not DB_AVAILABLE:
        return None
    
    db_manager = get_db_manager()
    if not db_manager:
        return None
    
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO ingestion_job_files (
                    job_id, original_filename, stored_filename, file_path,
                    file_size_bytes, file_format, status,
                    extraction_method, extraction_time_seconds, text_length,
                    cyrillic_ratio, encoding_was_fixed, chunks_created,
                    error_message
                ) VALUES (
                    :job_id, :filename, :stored_filename, :file_path,
                    :file_size, :format, :status,
                    :extraction_method, :extraction_time, :text_length,
                    :cyrillic_ratio, :encoding_fixed, :chunks_created,
                    :error_message
                )
                RETURNING id
            """), {
                'job_id': job_id,
                'filename': filename,
                'stored_filename': os.path.basename(file_path) if file_path else None,
                'file_path': file_path,
                'file_size': file_size,
                'format': file_format,
                'status': status,
                'extraction_method': extraction_method,
                'extraction_time': extraction_time,
                'text_length': text_length,
                'cyrillic_ratio': cyrillic_ratio,
                'encoding_fixed': encoding_was_fixed,
                'chunks_created': chunks_created,
                'error_message': error_message
            })
            
            file_id = result.fetchone()[0]
            conn.commit()
            logger.debug(f"Saved job file {filename} for job {job_id} with ID {file_id}")
            return file_id
            
    except Exception as e:
        logger.error(f"Failed to save job file: {e}")
        return None


def update_job_file(
    file_id: int,
    status: str = None,
    extraction_method: str = None,
    extraction_time: float = None,
    text_length: int = None,
    cyrillic_ratio: float = None,
    encoding_was_fixed: bool = None,
    chunks_created: int = None,
    chunks_ingested: bool = None,
    error_message: str = None
) -> bool:
    """
    Update a job file's processing status
    
    Returns:
        True if successful, False otherwise
    """
    if not DB_AVAILABLE:
        return False
    
    db_manager = get_db_manager()
    if not db_manager:
        return False
    
    try:
        # Build dynamic update query
        updates = []
        values = {}
        
        if status is not None:
            updates.append("status = :status")
            values['status'] = status
            values['processing_completed_at'] = datetime.utcnow()
        if extraction_method is not None:
            updates.append("extraction_method = :extraction_method")
            values['extraction_method'] = extraction_method
        if extraction_time is not None:
            updates.append("extraction_time_seconds = :extraction_time")
            values['extraction_time'] = extraction_time
        if text_length is not None:
            updates.append("text_length = :text_length")
            values['text_length'] = text_length
        if cyrillic_ratio is not None:
            updates.append("cyrillic_ratio = :cyrillic_ratio")
            values['cyrillic_ratio'] = cyrillic_ratio
        if encoding_was_fixed is not None:
            updates.append("encoding_was_fixed = :encoding_fixed")
            values['encoding_fixed'] = encoding_was_fixed
        if chunks_created is not None:
            updates.append("chunks_created = :chunks_created")
            values['chunks_created'] = chunks_created
        if chunks_ingested is not None:
            updates.append("chunks_ingested = :chunks_ingested")
            values['chunks_ingested'] = chunks_ingested
        if error_message is not None:
            updates.append("error_message = :error_message")
            values['error_message'] = error_message
        
        if not updates:
            return True  # Nothing to update
        
        values['file_id'] = file_id
        
        with db_manager.engine.connect() as conn:
            conn.execute(text(f"""
                UPDATE ingestion_job_files
                SET {', '.join(updates)}
                WHERE id = :file_id
            """), values)
            conn.commit()
            logger.debug(f"Updated job file {file_id}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to update job file: {e}")
        return False


def get_job_files(job_id: str) -> List[Dict[str, Any]]:
    """
    Get all files for a job
    
    Returns:
        List of file dictionaries
    """
    if not DB_AVAILABLE:
        return []
    
    db_manager = get_db_manager()
    if not db_manager:
        return []
    
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    id, job_id, original_filename, file_format, file_size_bytes,
                    status, extraction_method, extraction_time_seconds,
                    text_length, cyrillic_ratio, encoding_was_fixed,
                    chunks_created, error_message, processing_completed_at
                FROM ingestion_job_files
                WHERE job_id = :job_id
                ORDER BY id
            """), {'job_id': job_id})
            
            files = []
            for row in result.fetchall():
                files.append({
                    'id': row[0],
                    'job_id': row[1],
                    'filename': row[2],
                    'format': row[3],
                    'size_bytes': row[4],
                    'status': row[5],
                    'extraction_method': row[6],
                    'extraction_time': float(row[7]) if row[7] else None,
                    'text_length': row[8],
                    'cyrillic_ratio': float(row[9]) if row[9] else None,
                    'encoding_fixed': row[10],
                    'chunks_created': row[11],
                    'error': row[12],
                    'completed_at': row[13].isoformat() if row[13] else None
                })
            
            return files
            
    except Exception as e:
        logger.error(f"Failed to get job files: {e}")
        return []


def save_job_activity(
    job_id: str,
    activity_type: str,
    old_value: str = None,
    new_value: str = None,
    details: Dict = None,
    user_id: str = None,
    system_note: str = None
) -> Optional[int]:
    """
    Log job activity for audit trail
    
    Returns:
        activity_id if successful, None otherwise
    """
    if not DB_AVAILABLE:
        return None
    
    db_manager = get_db_manager()
    if not db_manager:
        return None
    
    try:
        with db_manager.engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO ingestion_job_activity (
                    job_id, activity_type, old_value, new_value,
                    details, user_id, system_note
                ) VALUES (
                    :job_id, :activity_type, :old_value, :new_value,
                    :details, :user_id, :system_note
                )
                RETURNING id
            """), {
                'job_id': job_id,
                'activity_type': activity_type,
                'old_value': old_value,
                'new_value': new_value,
                'details': json.dumps(details) if details else None,
                'user_id': user_id,
                'system_note': system_note
            })
            
            activity_id = result.fetchone()[0]
            conn.commit()
            return activity_id
            
    except Exception as e:
        logger.error(f"Failed to save job activity: {e}")
        return None
