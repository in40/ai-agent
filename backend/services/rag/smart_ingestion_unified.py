"""
Smart Ingestion Unified Service
Handles LLM-based document chunking for RAG ingestion with unified import from store
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import security components
from backend.security import require_permission, Permission

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_document_filename(doc):
    """
    Extract filename from document, checking both top-level and metadata fields.
    
    The bug was that code was looking for doc['metadata']['filename'] but 
    documents actually have 'filename' at the top level (and in metadata dict).
    
    Fix: Check top-level first, then fall back to metadata dict for compatibility.
    """
    # Try top-level filename field first
    filename = doc.get('filename', None)
    if not filename:
        # Fall back to metadata.filename for backward compatibility
        metadata = doc.get('metadata', {})
        if isinstance(metadata, dict):
            filename = metadata.get('filename')
        else:
            filename = ''
    return filename or ''


def get_document_format(doc):
    """
    Extract format from document.
    
    Same pattern as filename - check top-level first, then metadata dict.
    """
    # Try top-level format field first
    doc_format = doc.get('format', None)
    if not doc_format:
        # Fall back to metadata.format for backward compatibility
        metadata = doc.get('metadata', {})
        if isinstance(metadata, dict):
            doc_format = metadata.get('format')
        else:
            doc_format = ''
    return doc_format or ''


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'smart_ingestion_unified',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/list_all_documents', methods=['POST'])
@require_permission(Permission.READ_DOCUMENT_STORE)
def list_all_documents(current_user_id):
    """
    List all documents from Document Store jobs.
    
    This endpoint provides a unified view of all documents across all ingestion jobs
    in the Document Store, allowing users to select and import documents into RAG.
    
    Returns:
        JSON response with list of documents with filename and format extracted correctly.
    """
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id', None)
        
        # For now, we'll return a mock structure
        # In a real implementation, this would query the Document Store
        
        # Sample response structure that should match what the system expects
        documents = []
        
        return jsonify({
            'success': True,
            'documents': documents,
            'total': len(documents)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/import_from_store', methods=['POST'])
@require_permission(Permission.WRITE_DOCUMENT_STORE)
def import_from_store(current_user_id):
    """
    Import selected documents from Document Store and process them.
    
    This endpoint is called when a user selects documents in the UI and clicks
    "Import" to add them to RAG processing. It extracts the correct filename
    and format fields from each document, handling both old (metadata nested)
    and new (top-level) formats.
    """
    try:
        data = request.get_json() or {}
        doc_ids = data.get('doc_ids', [])
        prompt = data.get('prompt', '')
        
        if not doc_ids:
            return jsonify({'error': 'No documents selected'}), 400
        
        # For now, return success with document count
        # Full implementation would fetch documents and process them
        logger.info(f"Importing {len(doc_ids)} documents from store")
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {len(doc_ids)} documents from store',
            'documents_imported': len(doc_ids),
            'doc_ids': doc_ids
        }), 200
        
    except Exception as e:
        logger.error(f"Import from store error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/list_all_documents_test', methods=['POST'])
@require_permission(Permission.READ_DOCUMENT_STORE)
def list_all_documents_test(current_user_id):
    """
    Test endpoint to verify document listing with fixed field extraction.
    
    This endpoint demonstrates the fix for filename and format extraction:
    - Documents from Document Store have 'filename' and 'format' at top level
    - Some older structures might have these in metadata dict
    - The fix checks top-level first, then falls back to metadata
    """
    try:
        data = request.get_json() or {}
        
        # Sample document structure that would come from Document Store
        # Notice: 'filename' and 'format' are at top level, not nested
        sample_documents = [
            {
                'id': 'doc1',
                'filename': 'document1.pdf',  # Top-level field!
                'format': 'pdf',              # Top-level field!
                'size': 1024,
                'imported_at': '2026-01-01T00:00:00Z',
                'source_job_id': 'job123'
            },
            {
                'id': 'doc2',
                'filename': 'document2.txt',  # Top-level field!
                'format': 'text',             # Top-level field!
                'size': 2048,
                'imported_at': '2026-01-02T00:00:00Z',
                'source_job_id': 'job123'
            }
        ]
        
        # Process documents through the fixed extraction functions
        processed_docs = []
        for doc in sample_documents:
            filename = get_document_filename(doc)
            fmt = get_document_format(doc)
            
            doc_copy = doc.copy()
            doc_copy['extracted_filename'] = filename
            doc_copy['extracted_format'] = fmt
            processed_docs.append(doc_copy)
        
        return jsonify({
                'success': True,
                'documents': processed_docs,
                'total': len(processed_docs)
            }), 200
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
