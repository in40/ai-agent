"""
Document Store Browser API

Endpoints for browsing, filtering, and selecting documents from the Document Store
for phased processing.
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import Blueprint, request, jsonify
from sqlalchemy import text

from backend.services.rag.phased_processing_models import (
    DocumentProcessing, PhaseStatus, DocumentStatus, ProcessingPhase
)
from backend.services.rag.phased_processing_db import phased_db

logger = logging.getLogger(__name__)

# Create blueprint
document_store_bp = Blueprint('document_store', __name__, url_prefix='/api/rag/document-store')


# ============================================================================
# DOCUMENT STORE BROWSER ENDPOINTS
# ============================================================================

@document_store_bp.route('/documents', methods=['GET'])
def list_documents():
    """
    List documents from Document Store with filtering

    Query Parameters:
        job_id: Filter by job ID
        status: Filter by overall status (PENDING, PROCESSING, COMPLETED, FAILED)
        phase: Filter by current phase
        search: Search in filename/display_name
        file_type: Filter by file type (pdf, txt, chunks, metadata)
        page: Page number (default: 1)
        limit: Items per page (default: 50)
        user_id: Filter by user ID

    Returns:
        Paginated list of documents with phase status
    """
    try:
        # Get query parameters
        job_id = request.args.get('job_id')
        status = request.args.get('status')
        phase = request.args.get('phase')
        search = request.args.get('search', '')
        file_type_filter = request.args.get('file_type', '')  # New filter
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        user_id = request.args.get('user_id')
        
        # Scan actual directory for all file types
        import os
        doc_store_path = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
        all_documents = []
        
        if os.path.exists(doc_store_path):
            for job_dir in os.listdir(doc_store_path):
                job_path = os.path.join(doc_store_path, job_dir)
                if not os.path.isdir(job_path):
                    continue
                
                docs_path = os.path.join(job_path, 'documents')
                if not os.path.exists(docs_path):
                    continue
                
                # Get all files
                for filename in os.listdir(docs_path):
                    file_path = os.path.join(docs_path, filename)
                    if not os.path.isfile(file_path):
                        continue
                    
                    file_ext = os.path.splitext(filename)[1].lower()
                    doc_id = os.path.splitext(filename)[0]
                    
                    # Determine file type
                    file_type = get_file_type_from_filename(filename)
                    
                    # Get file size
                    file_size = os.path.getsize(file_path)
                    
                    # Load metadata if PDF
                    metadata = {}
                    if file_ext == '.pdf':
                        metadata_path = os.path.join(docs_path, f"{doc_id}.metadata.json")
                        if os.path.exists(metadata_path):
                            try:
                                with open(metadata_path, 'r') as f:
                                    metadata = json.load(f)
                            except:
                                pass
                    
                    all_documents.append({
                        'doc_id': doc_id,
                        'original_filename': filename,
                        'display_name': metadata.get('display_name', doc_id),
                        'file_type': file_type,
                        'format': file_type,
                        'size': file_size,
                        'file_size': file_size,
                        'job_id': job_dir.replace('job_', ''),
                        'source_website': metadata.get('source_website', ''),
                        'metadata': metadata
                    })
        
        # Apply filters
        documents = all_documents
        
        if job_id:
            documents = [d for d in documents if job_id in d.get('job_id', '')]
        
        if search:
            search_lower = search.lower()
            documents = [
                d for d in documents 
                if search_lower in d.get('original_filename', '').lower() 
                or search_lower in d.get('display_name', '').lower()
            ]
        
        if file_type_filter:
            documents = [d for d in documents if d.get('file_type') == file_type_filter]
        
        # Re-calculate total after filters
        total = len(documents)
        start = (page - 1) * limit
        end = start + limit
        paginated_docs = documents[start:end]
        
        return jsonify({
            'success': True,
            'documents': paginated_docs,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def get_file_type_from_filename(filename: str) -> str:
    """Determine file type from filename"""
    if not filename:
        return 'unknown'
    
    filename_lower = filename.lower()
    if filename_lower.endswith('.pdf'):
        return 'pdf'
    elif filename_lower.endswith('.txt'):
        return 'txt'
    elif filename_lower.endswith('.json'):
        if 'chunk' in filename_lower:
            return 'chunks'
        elif 'metadata' in filename_lower:
            return 'metadata'
        else:
            return 'json'
    else:
        return 'other'


@document_store_bp.route('/documents/<doc_id>', methods=['GET'])
def get_document(doc_id: str):
    """
    Get detailed information about a specific document
    
    Returns:
        Document details with all phase statuses and metadata
    """
    try:
        doc = phased_db.get_document(doc_id)
        
        if not doc:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        # Get chunks for this document
        chunks = phased_db.get_chunks_for_document(doc_id)
        
        return jsonify({
            'success': True,
            'document': doc.to_dict(),
            'chunks': {
                'total': len(chunks),
                'versions': list(set(c.version for c in chunks))
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@document_store_bp.route('/jobs/<job_id>/progress', methods=['GET'])
def get_job_progress(job_id: str):
    """
    Get phase-by-phase progress for a job
    
    Returns:
        Progress summary showing completed/failed/pending for each phase
    """
    try:
        progress = phased_db.get_job_phase_progress(job_id)
        
        if not progress:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        return jsonify({
            'success': True,
            'progress': progress.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get job progress: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@document_store_bp.route('/jobs/<job_id>/documents', methods=['GET'])
def get_job_documents(job_id: str):
    """
    Get all documents for a job with their phase statuses
    
    Query Parameters:
        status: Filter by status (COMPLETED, FAILED, PENDING, etc.)
        phase: Filter by current phase
    
    Returns:
        List of documents with their processing status
    """
    try:
        status = request.args.get('status')
        phase = request.args.get('phase')
        
        documents = phased_db.get_documents_by_job(job_id, status_filter=status)
        
        if phase:
            documents = [d for d in documents if d.current_phase == phase]
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents],
            'total': len(documents)
        })
        
    except Exception as e:
        logger.error(f"Failed to get job documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# DOCUMENT SELECTION FOR PROCESSING
# ============================================================================

@document_store_bp.route('/documents/select', methods=['POST'])
def select_documents():
    """
    Select documents from Document Store for processing
    
    Request Body:
        document_ids: List of document IDs to select
        job_id: New or existing job ID
        phases: List of phases to run (e.g., ["extract", "chunk", "vector"])
        config: Processing configuration
    
    Returns:
        Created/updated job with selected documents
    """
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        job_id = data.get('job_id')
        phases = data.get('phases', ['extract', 'chunk', 'vector'])
        config = data.get('config', {})
        
        if not document_ids:
            return jsonify({
                'success': False,
                'error': 'No document IDs provided'
            }), 400
        
        if not job_id:
            # Generate new job ID
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:12]}"
        
        # TODO: Create job in job queue with selected documents
        # For now, return job_id and document count
        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_selected': len(document_ids),
            'phases_configured': phases,
            'message': 'Document selection endpoint - full implementation pending'
        })
        
    except Exception as e:
        logger.error(f"Failed to select documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@document_store_bp.route('/documents/reprocess', methods=['POST'])
def reprocess_documents():
    """
    Re-process documents with new configuration
    
    Request Body:
        document_ids: List of document IDs to re-process
        phases_to_rerun: List of phases to re-run
        preserve_phases: List of phases to preserve
        new_config: New processing configuration
        on_conflict: How to handle existing data (overwrite, keep_both, skip)
    
    Returns:
        New job for re-processing
    """
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        phases_to_rerun = data.get('phases_to_rerun', [])
        preserve_phases = data.get('preserve_phases', [])
        new_config = data.get('new_config', {})
        on_conflict = data.get('on_conflict', 'overwrite')
        
        if not document_ids:
            return jsonify({
                'success': False,
                'error': 'No document IDs provided'
            }), 400
        
        if not phases_to_rerun:
            return jsonify({
                'success': False,
                'error': 'No phases specified for re-processing'
            }), 400
        
        # TODO: Create re-processing job
        # For now, return confirmation
        return jsonify({
            'success': True,
            'documents_to_reprocess': len(document_ids),
            'phases_to_rerun': phases_to_rerun,
            'preserve_phases': preserve_phases,
            'conflict_resolution': on_conflict,
            'message': 'Re-process endpoint - full implementation pending'
        })
        
    except Exception as e:
        logger.error(f"Failed to re-process documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# DOCUMENT STORE STATISTICS
# ============================================================================

@document_store_bp.route('/stats', methods=['GET'])
def get_statistics():
    """
    Get Document Store statistics
    
    Returns:
        Statistics about documents, phases, and processing status
    """
    try:
        # TODO: Implement statistics from database
        stats = {
            'total_documents': 0,
            'by_status': {
                'COMPLETED': 0,
                'FAILED': 0,
                'PROCESSING': 0,
                'PENDING': 0
            },
            'by_phase': {
                'upload': {'completed': 0, 'failed': 0, 'pending': 0},
                'extract': {'completed': 0, 'failed': 0, 'pending': 0},
                'chunk': {'completed': 0, 'failed': 0, 'pending': 0},
                'vector': {'completed': 0, 'failed': 0, 'pending': 0},
                'graph': {'completed': 0, 'failed': 0, 'pending': 0}
            }
        }
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def scan_document_store_directory() -> List[Dict[str, Any]]:
    """
    Scan Document Store directory for existing documents

    This is used to import existing documents into the phased processing system.

    Returns:
        List of document metadata
    """
    doc_store_path = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
    documents = []

    try:
        if not os.path.exists(doc_store_path):
            logger.warning(f"Document store path does not exist: {doc_store_path}")
            return documents

        # Scan job directories
        for job_dir in os.listdir(doc_store_path):
            job_path = os.path.join(doc_store_path, job_dir)
            if not os.path.isdir(job_path):
                continue

            docs_path = os.path.join(job_path, 'documents')
            if not os.path.exists(docs_path):
                continue

            # Scan all files (PDF, TXT, JSON, etc.)
            for filename in os.listdir(docs_path):
                file_path = os.path.join(docs_path, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                doc_id = os.path.splitext(filename)[0]
                
                # Determine file type
                if file_ext == '.pdf':
                    file_type = 'pdf'
                    file_format = 'pdf'
                elif file_ext == '.txt':
                    file_type = 'txt'
                    file_format = 'text'
                elif file_ext == '.json':
                    if 'metadata' in filename.lower():
                        file_type = 'metadata'
                        file_format = 'json'
                    elif 'chunk' in filename.lower():
                        file_type = 'chunks'
                        file_format = 'json'
                    else:
                        file_type = 'json'
                        file_format = 'json'
                else:
                    file_type = 'other'
                    file_format = file_ext.replace('.', '')
                
                # Load metadata if exists
                metadata = {}
                metadata_path = os.path.join(docs_path, f"{doc_id}.metadata.json")
                if os.path.exists(metadata_path) and file_ext == '.pdf':
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                documents.append({
                    'doc_id': doc_id,
                    'original_filename': filename,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'file_type': file_type,  # pdf, txt, chunks, metadata, other
                    'file_format': file_format,
                    'metadata': metadata,
                    'job_id': job_dir.replace('job_', ''),
                    'source_url': metadata.get('original_url') if metadata else None,
                    'display_name': metadata.get('display_name', doc_id) if metadata else doc_id
                })

        return documents

    except Exception as e:
        logger.error(f"Failed to scan document store: {e}")
        return documents


@document_store_bp.route('/scan', methods=['POST'])
def scan_and_import():
    """
    Scan Document Store directory and import existing documents into phased processing
    
    This is a one-time operation to migrate existing documents to the new system.
    
    Returns:
        Number of documents imported
    """
    try:
        documents = scan_document_store_directory()
        
        imported_count = 0
        for doc_data in documents:
            # Check if document already exists
            existing = phased_db.get_document(doc_data['doc_id'])
            if existing:
                continue
            
            # Create document record
            doc = DocumentProcessing(
                doc_id=doc_data['doc_id'],
                job_id=doc_data.get('job_id', 'unknown'),
                user_id='system',  # TODO: Get from metadata
                original_filename=doc_data['original_filename'],
                display_name=doc_data.get('display_name'),
                file_path=doc_data['file_path'],
                file_size=doc_data.get('file_size'),
                source_url=doc_data.get('source_url'),
                phase_upload=PhaseStatus.COMPLETED,  # Already uploaded
                phase_extract=PhaseStatus.PENDING,
                phase_chunk=PhaseStatus.PENDING,
                phase_vector=PhaseStatus.PENDING,
                phase_graph=PhaseStatus.PENDING,
                overall_status=DocumentStatus.PENDING,
            )
            
            if phased_db.create_document(doc):
                imported_count += 1
        
        return jsonify({
            'success': True,
            'documents_found': len(documents),
            'documents_imported': imported_count,
            'message': f'Imported {imported_count} documents into phased processing system'
        })
        
    except Exception as e:
        logger.error(f"Failed to scan and import: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
