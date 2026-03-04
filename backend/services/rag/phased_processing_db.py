"""
Phased Document Processing - Database Manager

Handles all database operations for the phased processing pipeline.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import text

from backend.services.rag.phased_processing_models import (
    DocumentProcessing, PhaseStatus, DocumentStatus,
    Chunk, Entity, PhaseExecutionLog, JobPhaseProgress
)

logger = logging.getLogger(__name__)

try:
    from database.utils.database import get_db_manager
    DB_AVAILABLE = True
    db_manager = get_db_manager()
except ImportError:
    logger.warning("Database module not available")
    DB_AVAILABLE = False
    db_manager = None


class PhasedProcessingDB:
    """Database operations for phased document processing"""
    
    def __init__(self):
        self.db_available = DB_AVAILABLE and db_manager is not None
    
    # ========================================================================
    # DOCUMENT PROCESSING OPERATIONS
    # ========================================================================
    
    def create_document(self, doc: DocumentProcessing) -> bool:
        """Create a new document processing record"""
        if not self.db_available:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO document_processing (
                        doc_id, job_id, user_id, original_filename, display_name,
                        file_path, file_size, content_type, source_url, source_website,
                        phase_upload, phase_extract, phase_chunk, phase_vector, phase_graph,
                        current_phase, overall_status
                    ) VALUES (
                        :doc_id, :job_id, :user_id, :original_filename, :display_name,
                        :file_path, :file_size, :content_type, :source_url, :source_website,
                        :phase_upload, :phase_extract, :phase_chunk, :phase_vector, :phase_graph,
                        :current_phase, :overall_status
                    )
                """), {
                    'doc_id': doc.doc_id,
                    'job_id': doc.job_id,
                    'user_id': doc.user_id,
                    'original_filename': doc.original_filename,
                    'display_name': doc.display_name,
                    'file_path': doc.file_path,
                    'file_size': doc.file_size,
                    'content_type': doc.content_type,
                    'source_url': doc.source_url,
                    'source_website': doc.source_website,
                    'phase_upload': doc.phase_upload.value,
                    'phase_extract': doc.phase_extract.value,
                    'phase_chunk': doc.phase_chunk.value,
                    'phase_vector': doc.phase_vector.value,
                    'phase_graph': doc.phase_graph.value,
                    'current_phase': doc.current_phase,
                    'overall_status': doc.overall_status.value,
                })
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[DocumentProcessing]:
        """Get document by ID"""
        if not self.db_available:
            return None
        
        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM document_processing WHERE doc_id = :doc_id
                """), {'doc_id': doc_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                return self._row_to_document(row)
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None
    
    def get_documents_by_job(self, job_id: str, status_filter: Optional[str] = None) -> List[DocumentProcessing]:
        """Get all documents for a job, optionally filtered by status"""
        if not self.db_available:
            return []
        
        try:
            with db_manager.engine.connect() as conn:
                if status_filter:
                    result = conn.execute(text("""
                        SELECT * FROM document_processing 
                        WHERE job_id = :job_id AND overall_status = :status
                        ORDER BY created_at
                    """), {'job_id': job_id, 'status': status_filter})
                else:
                    result = conn.execute(text("""
                        SELECT * FROM document_processing 
                        WHERE job_id = :job_id
                        ORDER BY created_at
                    """), {'job_id': job_id})
                
                return [self._row_to_document(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get documents by job: {e}")
            return []
    
    def get_documents_ready_for_phase(self, job_id: str, phase: str) -> List[DocumentProcessing]:
        """Get documents that are ready to be processed in specified phase"""
        if not self.db_available:
            return []

        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM document_processing
                    WHERE job_id = :job_id
                    AND overall_status IN ('PENDING', 'PROCESSING')
                    AND CASE
                        WHEN :phase = 'extract' THEN phase_upload = 'COMPLETED' AND phase_extract IN ('PENDING', 'FAILED')
                        WHEN :phase = 'chunk' THEN (phase_extract = 'COMPLETED' OR phase_extract = 'SKIPPED') AND phase_chunk IN ('PENDING', 'FAILED')
                        WHEN :phase = 'vector' THEN (phase_chunk = 'COMPLETED' OR phase_chunk = 'SKIPPED') AND phase_vector IN ('PENDING', 'FAILED')
                        WHEN :phase = 'graph' THEN (phase_chunk = 'COMPLETED' OR phase_chunk = 'SKIPPED') AND phase_graph IN ('PENDING', 'FAILED')
                        ELSE FALSE
                    END
                    ORDER BY created_at
                """), {'job_id': job_id, 'phase': phase})

                return [self._row_to_document(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get documents ready for phase: {e}")
            return []
    
    def update_document_phase_status(
        self, 
        doc_id: str, 
        phase: str, 
        status: PhaseStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update the status of a specific phase"""
        if not self.db_available:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                # Update phase status
                phase_column = f"phase_{phase}"
                update_data = {
                    'doc_id': doc_id,
                    'status': status.value,
                }
                
                # Add timestamp for this phase if completed
                if status == PhaseStatus.COMPLETED:
                    update_data['timestamp'] = datetime.utcnow().isoformat()
                    # Map phase name to correct column name
                    timestamp_columns = {
                        'upload': 'uploaded_at',
                        'extract': 'extracted_at',
                        'chunk': 'chunked_at',
                        'vector': 'indexed_at',
                        'graph': 'graph_built_at'
                    }
                    timestamp_column = timestamp_columns.get(phase, f'{phase}_at')
                    timestamp_update = f", {timestamp_column} = :timestamp"
                else:
                    timestamp_update = ""
                
                # Add error message if failed
                error_update = ""
                if status == PhaseStatus.FAILED and error_message:
                    update_data['error'] = error_message
                    update_data['error_phase'] = phase
                    error_update = ", last_error = :error, last_error_phase = :error_phase"
                
                query = f"""
                    UPDATE document_processing 
                    SET {phase_column} = :status{timestamp_update}{error_update},
                        updated_at = NOW()
                    WHERE doc_id = :doc_id
                """
                
                conn.execute(text(query), update_data)
                
                # Update overall status
                if status == PhaseStatus.FAILED:
                    conn.execute(text("""
                        UPDATE document_processing
                        SET overall_status = 'FAILED', updated_at = NOW()
                        WHERE doc_id = :doc_id
                    """), {'doc_id': doc_id})
                elif status == PhaseStatus.COMPLETED:
                    # Check if all phases completed OR skipped
                    result = conn.execute(text("""
                        SELECT phase_upload, phase_extract, phase_chunk, phase_vector, phase_graph
                        FROM document_processing WHERE doc_id = :doc_id
                    """), {'doc_id': doc_id})
                    row = result.fetchone()
                    if row:
                        # A phase is "done" if it's COMPLETED or SKIPPED
                        all_done = all(
                            p in ('COMPLETED', 'SKIPPED') 
                            for p in [row.phase_upload, row.phase_extract,
                                      row.phase_chunk, row.phase_vector,
                                      row.phase_graph]
                        )
                        if all_done:
                            conn.execute(text("""
                                UPDATE document_processing
                                SET overall_status = 'COMPLETED', updated_at = NOW()
                                WHERE doc_id = :doc_id
                            """), {'doc_id': doc_id})

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update document phase status: {e}")
            return False
    
    def update_document_metadata(self, doc_id: str, metadata: Dict[str, Any]) -> bool:
        """Update document metadata (chunk count, entity count, etc.)"""
        if not self.db_available:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                updates = []
                params = {'doc_id': doc_id}
                
                for key, value in metadata.items():
                    if key in ['chunk_count', 'entity_count', 'relationship_count', 
                               'extraction_attempts', 'page_count', 'extracted_char_count',
                               'encoding_issues_fixed', 'vector_chunk_count']:
                        updates.append(f"{key} = :{key}")
                        params[key] = value
                    elif key in ['extraction_method', 'chunking_strategy', 'chunking_model',
                                 'vector_collection', 'embedding_model', 'graph_model']:
                        updates.append(f"{key} = :{key}")
                        params[key] = value
                
                if updates:
                    query = f"""
                        UPDATE document_processing 
                        SET {', '.join(updates)}, updated_at = NOW()
                        WHERE doc_id = :doc_id
                    """
                    conn.execute(text(query), params)
                    conn.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            return False
    
    def log_phase_execution(self, log_entry: PhaseExecutionLog) -> bool:
        """Log a phase execution"""
        if not self.db_available:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO phase_execution_log (
                        execution_id, job_id, doc_id, phase, action, status,
                        error_message, processing_time_ms, items_processed,
                        config_snapshot, metadata
                    ) VALUES (
                        :execution_id, :job_id, :doc_id, :phase, :action, :status,
                        :error_message, :processing_time_ms, :items_processed,
                        :config_snapshot, :metadata
                    )
                """), {
                    'execution_id': log_entry.execution_id,
                    'job_id': log_entry.job_id,
                    'doc_id': log_entry.doc_id,
                    'phase': log_entry.phase,
                    'action': log_entry.action,
                    'status': log_entry.status,
                    'error_message': log_entry.error_message,
                    'processing_time_ms': log_entry.processing_time_ms,
                    'items_processed': log_entry.items_processed,
                    'config_snapshot': log_entry.config_snapshot,
                    'metadata': log_entry.metadata,
                })
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to log phase execution: {e}")
            return False
    
    def get_job_phase_progress(self, job_id: str) -> Optional[JobPhaseProgress]:
        """Get phase progress summary for a job"""
        if not self.db_available:
            return None
        
        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM v_job_phase_progress WHERE job_id = :job_id
                """), {'job_id': job_id})
                
                row = result.fetchone()
                if not row:
                    return None
                
                return JobPhaseProgress(
                    job_id=row.job_id,
                    documents_total=row.documents_total,
                    upload_completed=row.upload_completed,
                    upload_failed=row.upload_failed,
                    upload_pending=row.upload_pending,
                    extract_completed=row.extract_completed,
                    extract_failed=row.extract_failed,
                    extract_pending=row.extract_pending,
                    chunk_completed=row.chunk_completed,
                    chunk_failed=row.chunk_failed,
                    chunk_pending=row.chunk_pending,
                    vector_completed=row.vector_completed,
                    vector_failed=row.vector_failed,
                    vector_pending=row.vector_pending,
                    graph_completed=row.graph_completed,
                    graph_failed=row.graph_failed,
                    graph_pending=row.graph_pending,
                    fully_completed=row.fully_completed,
                    fully_failed=row.fully_failed,
                    in_progress=row.in_progress,
                )
        except Exception as e:
            logger.error(f"Failed to get job phase progress: {e}")
            return None
    
    # ========================================================================
    # CHUNK OPERATIONS
    # ========================================================================
    
    def save_chunks(self, chunks: List[Chunk]) -> bool:
        """Save multiple chunks to cache"""
        if not self.db_available or not chunks:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                for chunk in chunks:
                    conn.execute(text("""
                        INSERT INTO chunks_cache (
                            doc_id, chunk_id, chunk_index, content, content_length,
                            section, title, chunk_type, token_count, start_char, end_char,
                            contains_formula, contains_table, entity_hints,
                            version, version_label, is_active
                        ) VALUES (
                            :doc_id, :chunk_id, :chunk_index, :content, :content_length,
                            :section, :title, :chunk_type, :token_count, :start_char, :end_char,
                            :contains_formula, :contains_table, :entity_hints,
                            :version, :version_label, :is_active
                        )
                        ON CONFLICT (doc_id, chunk_id, version) DO UPDATE SET
                            content = EXCLUDED.content,
                            content_length = EXCLUDED.content_length,
                            section = EXCLUDED.section,
                            title = EXCLUDED.title,
                            entity_hints = EXCLUDED.entity_hints,
                            is_active = EXCLUDED.is_active
                    """), {
                        'doc_id': chunk.doc_id,
                        'chunk_id': chunk.chunk_id,
                        'chunk_index': chunk.chunk_index,
                        'content': chunk.content,
                        'content_length': chunk.content_length,
                        'section': chunk.section,
                        'title': chunk.title,
                        'chunk_type': chunk.chunk_type,
                        'token_count': chunk.token_count,
                        'start_char': chunk.start_char,
                        'end_char': chunk.end_char,
                        'contains_formula': chunk.contains_formula,
                        'contains_table': chunk.contains_table,
                        'entity_hints': chunk.entity_hints,
                        'version': chunk.version,
                        'version_label': chunk.version_label,
                        'is_active': chunk.is_active,
                    })
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save chunks: {e}")
            return False
    
    def get_chunks_for_document(self, doc_id: str, version: str = 'v1') -> List[Chunk]:
        """Get all chunks for a document"""
        if not self.db_available:
            return []
        
        try:
            with db_manager.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM chunks_cache 
                    WHERE doc_id = :doc_id AND version = :version AND is_active = TRUE
                    ORDER BY chunk_index
                """), {'doc_id': doc_id, 'version': version})
                
                return [self._row_to_chunk(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get chunks: {e}")
            return []
    
    def deactivate_chunks(self, doc_id: str, version: str = 'v1') -> bool:
        """Deactivate chunks (for re-processing)"""
        if not self.db_available:
            return False
        
        try:
            with db_manager.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE chunks_cache 
                    SET is_active = FALSE 
                    WHERE doc_id = :doc_id AND version = :version
                """), {'doc_id': doc_id, 'version': version})
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to deactivate chunks: {e}")
            return False
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _row_to_document(self, row) -> DocumentProcessing:
        """Convert database row to DocumentProcessing object"""
        return DocumentProcessing(
            doc_id=row.doc_id,
            job_id=row.job_id,
            user_id=row.user_id,
            original_filename=row.original_filename,
            display_name=row.display_name,
            file_path=row.file_path,
            file_size=row.file_size,
            content_type=row.content_type,
            source_url=row.source_url,
            source_website=row.source_website,
            phase_upload=PhaseStatus(row.phase_upload),
            phase_extract=PhaseStatus(row.phase_extract),
            phase_chunk=PhaseStatus(row.phase_chunk),
            phase_vector=PhaseStatus(row.phase_vector),
            phase_graph=PhaseStatus(row.phase_graph),
            current_phase=row.current_phase,
            overall_status=DocumentStatus(row.overall_status),
            extraction_method=row.extraction_method,
            extraction_attempts=row.extraction_attempts,
            page_count=row.page_count,
            extracted_char_count=row.extracted_char_count,
            chunk_count=row.chunk_count,
            chunking_strategy=row.chunking_strategy,
            vector_collection=row.vector_collection,
            entity_count=row.entity_count,
            last_error=row.last_error,
            last_error_phase=row.last_error_phase,
            retry_count=row.retry_count,
            uploaded_at=row.uploaded_at,
            extracted_at=row.extracted_at,
            chunked_at=row.chunked_at,
            indexed_at=row.indexed_at,
            graph_built_at=row.graph_built_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    
    def _row_to_chunk(self, row) -> Chunk:
        """Convert database row to Chunk object"""
        return Chunk(
            doc_id=row.doc_id,
            chunk_id=row.chunk_id,
            chunk_index=row.chunk_index,
            content=row.content,
            content_length=row.content_length,
            section=row.section,
            title=row.title,
            chunk_type=row.chunk_type,
            token_count=row.token_count,
            start_char=row.start_char,
            end_char=row.end_char,
            contains_formula=row.contains_formula,
            contains_table=row.contains_table,
            entity_hints=row.entity_hints or [],
            version=row.version,
            version_label=row.version_label,
            is_active=row.is_active,
            vector_id=row.vector_id,
            vector_collection=row.vector_collection,
            created_at=row.created_at,
        )


# Global instance
phased_db = PhasedProcessingDB()
