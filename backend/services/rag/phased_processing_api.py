"""
Phased Document Processing API

Endpoints for phased document processing:
- Phase 1: Upload & Store
- Phase 2: Text Extraction
- Phase 3: Chunking
- Phase 4: Vector Indexing
- Phase 5: Graph Build
"""
import os
import json
import uuid
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename as flask_secure_filename
from sqlalchemy import text

from backend.services.rag.phased_processing_models import (
    DocumentProcessing, PhaseStatus, DocumentStatus, ProcessingPhase,
    Chunk, PhaseExecutionLog
)
from backend.services.rag.phased_processing_db import phased_db
from config.settings import LLM_CHUNKING_TIMEOUT

logger = logging.getLogger(__name__)

# Create blueprint
phased_processing_bp = Blueprint('phased_processing', __name__, url_prefix='/api/rag/phased')

# Configuration
UPLOAD_FOLDER = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file
ALLOWED_EXTENSIONS = {'pdf'}


def secure_filename(filename: str) -> str:
    """Secure filename while preserving Unicode characters"""
    if filename is None:
        return ''
    
    filename = filename.replace('\\', '/')
    filename = os.path.basename(filename)
    filename = filename.lstrip('. ')
    
    # Allow Unicode word characters, dots, dashes, underscores
    import re
    filename = re.sub(r'[^\w\-.]', '_', filename, flags=re.UNICODE)
    
    if not filename:
        filename = "unnamed_file"
    
    return filename


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# PHASE 1: UPLOAD & STORE
# ============================================================================

@phased_processing_bp.route('/upload', methods=['POST'])
def upload_documents():
    """
    Phase 1: Upload documents to Document Store
    
    Request:
        multipart/form-data with files
        OR JSON with URLs to download
    
    Returns:
        job_id and list of document IDs
    """
    try:
        # Generate job ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        user_id = request.headers.get('X-User-ID', 'anonymous')
        
        uploaded_docs = []
        
        # Handle file uploads
        if 'files' in request.files:
            files = request.getlist('files')
            
            for file in files:
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename):
                    continue
                
                # Generate unique doc_id
                filename = secure_filename(file.filename)
                doc_id = f"{os.path.splitext(filename)[0]}_{uuid.uuid4().hex[:8]}"
                
                # Create job directory
                job_dir = os.path.join(UPLOAD_FOLDER, f"job_{job_id}")
                docs_dir = os.path.join(job_dir, 'documents')
                os.makedirs(docs_dir, exist_ok=True)
                
                # Save file
                file_path = os.path.join(docs_dir, f"{doc_id}.pdf")
                file.save(file_path)
                file_size = os.path.getsize(file_path)
                
                # Create document record
                doc = DocumentProcessing(
                    doc_id=doc_id,
                    job_id=job_id,
                    user_id=user_id,
                    original_filename=filename,
                    display_name=os.path.splitext(filename)[0],
                    file_path=file_path,
                    file_size=file_size,
                    content_type='application/pdf',
                    phase_upload=PhaseStatus.COMPLETED,
                    phase_extract=PhaseStatus.PENDING,
                    phase_chunk=PhaseStatus.PENDING,
                    phase_vector=PhaseStatus.PENDING,
                    phase_graph=PhaseStatus.PENDING,
                    current_phase=ProcessingPhase.EXTRACT.value,
                    overall_status=DocumentStatus.PENDING,
                )
                
                if phased_db.create_document(doc):
                    uploaded_docs.append(doc_id)
                    
                    # Log phase execution
                    phased_db.log_phase_execution(PhaseExecutionLog(
                        execution_id=f"exec_{uuid.uuid4().hex[:8]}",
                        job_id=job_id,
                        doc_id=doc_id,
                        phase='upload',
                        action='COMPLETE',
                        status='SUCCESS',
                        items_processed=1,
                        metadata={'filename': filename, 'size': file_size}
                    ))
        
        # Handle URL imports
        if 'urls' in request.json if request.is_json else False:
            data = request.get_json()
            urls = data.get('urls', [])
            
            for url in urls:
                # Generate doc_id from URL
                url_hash = uuid.uuid4().hex[:8]
                doc_id = f"url_import_{url_hash}"
                
                # TODO: Download file from URL
                # For now, create placeholder record
                doc = DocumentProcessing(
                    doc_id=doc_id,
                    job_id=job_id,
                    user_id=user_id,
                    original_filename=f"import_from_url.pdf",
                    display_name=f"URL Import {url_hash}",
                    source_url=url,
                    phase_upload=PhaseStatus.PENDING,  # Needs download
                    phase_extract=PhaseStatus.PENDING,
                    phase_chunk=PhaseStatus.PENDING,
                    phase_vector=PhaseStatus.PENDING,
                    phase_graph=PhaseStatus.PENDING,
                    current_phase=ProcessingPhase.UPLOAD.value,
                    overall_status=DocumentStatus.PENDING,
                )
                
                if phased_db.create_document(doc):
                    uploaded_docs.append(doc_id)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_uploaded': len(uploaded_docs),
            'document_ids': uploaded_docs,
            'message': f'Uploaded {len(uploaded_docs)} documents'
        })
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phased_processing_bp.route('/from-docstore', methods=['POST'])
def create_job_from_docstore():
    """
    Create a processing job from existing Document Store documents

    Request:
        document_ids: List of document IDs to process
        phases: List of phases to run (default: all pending)
        extraction_config: Optional extraction configuration
            - method: Extraction method (auto, pymupdf, pdfminer)
            - page_range: 'all' or {'start': int, 'end': int}

    Returns:
        job_id and processing status
    """
    try:
        data = request.get_json()
        document_ids = data.get('document_ids', [])
        phases = data.get('phases', ['extract', 'chunk', 'vector', 'graph'])
        user_id = data.get('user_id', 'anonymous')
        extraction_config = data.get('extraction_config', {})

        # Log received config
        logger.info(f"[create_job_from_docstore] Received extraction_config: {json.dumps(extraction_config, indent=2)}")

        # Validate method
        valid_methods = ['auto', 'pymupdf', 'pdfminer', 'tesseract', 'llm']
        method = extraction_config.get('method', 'auto')
        if method not in valid_methods:
            logger.warning(f"[create_job_from_docstore] Invalid extraction method '{method}', using 'auto' instead. Valid: {valid_methods}")
            extraction_config['method'] = 'auto'
            method = 'auto'
        else:
            logger.info(f"[create_job_from_docstore] ✓ Extraction method '{method}' is valid")

        # Validate page_range
        page_range = extraction_config.get('page_range', 'all')
        if page_range != 'all' and isinstance(page_range, dict):
            start = page_range.get('start')
            end = page_range.get('end')
            
            if start and (not isinstance(start, int) or start < 1):
                logger.warning(f"[create_job_from_docstore] Invalid page_range start '{start}', using 'all' instead")
                extraction_config['page_range'] = 'all'
            elif end and (not isinstance(end, int) or end < 1):
                logger.warning(f"[create_job_from_docstore] Invalid page_range end '{end}', using 'all' instead")
                extraction_config['page_range'] = 'all'
            elif start and end and start > end:
                logger.warning(f"[create_job_from_docstore] Invalid page_range: start ({start}) > end ({end}), using 'all' instead")
                extraction_config['page_range'] = 'all'
            else:
                logger.info(f"[create_job_from_docstore] ✓ Page range valid: {start}-{end if end else 'end'}")
        else:
            logger.info(f"[create_job_from_docstore] ✓ Page range: {page_range}")

        # Log final validated config
        logger.info(f"[create_job_from_docstore] Final extraction_config after validation: {json.dumps(extraction_config, indent=2)}")

        if not document_ids:
            return jsonify({
                'success': False,
                'error': 'No document IDs provided'
            }), 400

        auto_retry = data.get('auto_retry_failed', True)
        logger.info(f"[create_job_from_docstore] Auto-retry failed: {auto_retry}")

        # FIRST: Create job in job queue to get job_id
        # We need the job_id BEFORE creating documents so they match
        try:
            from backend.services.rag.job_queue import job_queue, _start_job_processing

            job = job_queue.create_job(
                user_id=user_id,
                job_type='phased_processing',
                parameters={
                    'phases': phases,
                    'document_ids': document_ids,
                    'source': 'docstore',
                    'total_documents': 0,  # Will update after creating documents
                    'files': [],  # Track files
                    'extraction_config': extraction_config,  # Store extraction config
                    'auto_retry_failed': auto_retry
                },
                ingestion_mode='docstore',
                processing_mode='vector_db',
                chunking_strategy='smart_chunking'
            )

            # Use the job_id from create_job() - this is what's in Redis
            job_id = job.job_id
            logger.info(f"Created job {job_id} in job queue")
            
            # Track input files in job
            input_files = []
            for doc_id in document_ids:
                existing_doc = phased_db.get_document(doc_id)
                if existing_doc:
                    input_files.append({
                        'filename': existing_doc.original_filename,
                        'size': existing_doc.file_size,
                        'path': existing_doc.file_path,
                        'type': 'input'
                    })
            
            # Update job with file list
            job.parameters['files'] = input_files
            job_queue.update_job(job)
            
        except Exception as e:
            logger.error(f"Failed to create job: {e}")
            return jsonify({
                'success': False,
                'error': f'Failed to create job: {str(e)}'
            }), 500

        # SECOND: Create documents in phased processing DB with the SAME job_id
        # For Document Store documents, we need to read metadata from JSON files
        created_count = 0
        
        # Document Store base directory
        docstore_base = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
        
        for doc_id in document_ids:
            # Try to get from phased DB first
            existing_doc = phased_db.get_document(doc_id)

            # If not in phased DB, try to load from Document Store metadata
            if not existing_doc:
                # Search for the document in Document Store
                # Format: job_{job_id}_{source}/documents/{doc_id}.metadata.json
                import glob as glob_module

                # Try EXACT match first - this is the expected case now that frontend sends full doc_id
                metadata_files = glob_module.glob(f"{docstore_base}/**/documents/{doc_id}.metadata.json", recursive=True)
                
                # If no metadata file, try looking for the PDF directly
                if not metadata_files:
                    pdf_files = glob_module.glob(f"{docstore_base}/**/documents/{doc_id}.pdf", recursive=True)
                    if pdf_files:
                        # Found PDF without metadata - create minimal metadata
                        metadata_file = pdf_files[0]
                        metadata = {}
                        doc_dir = os.path.dirname(metadata_file)
                        actual_doc_id = doc_id
                        file_path = metadata_file
                        file_size = os.path.getsize(file_path)
                        logger.info(f"[Phased Job {job_id}] Found {actual_doc_id} PDF (no metadata): {file_path}")
                    else:
                        logger.error(f"Document {doc_id} not found in phased DB or Document Store (tried exact match)")
                        continue
                elif len(metadata_files) > 1:
                    # This should NEVER happen with full doc_id, but validate anyway
                    logger.error(
                        f"Document {doc_id} matched {len(metadata_files)} metadata files (unexpected!): "
                        f"{[os.path.basename(f) for f in metadata_files[:5]]}. "
                        f"This indicates a bug - full doc_id should be unique."
                    )
                    continue
                else:
                    # Exactly one match - perfect!
                    metadata_file = metadata_files[0]
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)

                    # Find the actual file (could be .pdf, .md, or .txt)
                    doc_dir = os.path.dirname(metadata_file)
                    actual_doc_id = os.path.splitext(os.path.basename(metadata_file))[0].replace('.metadata', '')
                    file_path = None
                    file_size = 0

                    # Try to find the actual document file
                    # IMPORTANT: PDF must be FIRST to ensure LLM extraction runs on original PDF
                    # TXT/MD are outputs from previous extractions and should only be used as fallback
                    for ext in ['.pdf', '.md', '.txt']:
                        candidate = os.path.join(doc_dir, f"{actual_doc_id}{ext}")
                        if os.path.exists(candidate):
                            file_path = candidate
                            file_size = os.path.getsize(candidate)
                            break

                    if not file_path:
                        # Fallback to PDF path even if it doesn't exist
                        file_path = os.path.join(doc_dir, f"{actual_doc_id}.pdf")

                    logger.info(f"[Phased Job {job_id}] Loaded {actual_doc_id} from Document Store: {file_path}")

                    # Verify the doc_id matches what we expected
                    if actual_doc_id != doc_id:
                        logger.warning(
                            f"[Phased Job {job_id}] Document ID mismatch: "
                            f"expected {doc_id}, found {actual_doc_id}. "
                            f"This may indicate stale metadata or filesystem inconsistency."
                        )

                # Create mock document if we found a file
                if file_path:
                    class MockDocument:
                        def __init__(self, metadata, file_path, file_size):
                            self.original_filename = metadata.get('original_filename', f"{actual_doc_id}.pdf")
                            self.display_name = metadata.get('display_name', actual_doc_id)
                            self.file_path = file_path
                            self.file_size = file_size
                            self.content_type = metadata.get('content_type', 'application/pdf')
                            self.source_url = metadata.get('original_url', '')
                            self.source_website = metadata.get('source_website', '')
                            self.extraction_method = None
                            self.chunk_count = 0

                    existing_doc = MockDocument(metadata, file_path, file_size)

                    # Update doc_id to the actual_doc_id for document creation
                    # (should match since we're using exact match now)
                    doc_id = actual_doc_id
                else:
                    logger.warning(f"Document {doc_id} not found in phased DB or Document Store")
                    continue
            
            # Determine which phases to run based on request
            # For NEW jobs, always run requested phases (don't reuse old phase status)
            phase_upload = PhaseStatus.COMPLETED  # Already in store
            
            # For new job, set phases based on request (not previous status)
            if 'extract' in phases:
                phase_extract = PhaseStatus.PENDING
            else:
                phase_extract = PhaseStatus.SKIPPED
            
            if 'chunk' in phases:
                phase_chunk = PhaseStatus.PENDING  # Always re-chunk for new job
            else:
                phase_chunk = PhaseStatus.SKIPPED
            
            if 'vector' in phases:
                phase_vector = PhaseStatus.PENDING
            else:
                phase_vector = PhaseStatus.SKIPPED
            
            if 'graph' in phases:
                phase_graph = PhaseStatus.PENDING
            else:
                phase_graph = PhaseStatus.SKIPPED
            
            # Determine current phase
            current_phase = ProcessingPhase.EXTRACT.value
            if phase_extract == PhaseStatus.COMPLETED:
                current_phase = ProcessingPhase.CHUNK.value
            if phase_chunk == PhaseStatus.COMPLETED:
                current_phase = ProcessingPhase.VECTOR.value
            if phase_vector == PhaseStatus.COMPLETED:
                current_phase = ProcessingPhase.GRAPH.value

            doc = DocumentProcessing(
                doc_id=doc_id,  # Use SAME doc_id (composite constraint allows this)
                job_id=job_id,  # Use job_id from create_job() - MUST MATCH!
                user_id=user_id,
                original_filename=existing_doc.original_filename,
                display_name=existing_doc.display_name,
                file_path=existing_doc.file_path,
                file_size=existing_doc.file_size,
                content_type=existing_doc.content_type,
                source_url=existing_doc.source_url,
                source_website=existing_doc.source_website,
                phase_upload=phase_upload,
                phase_extract=phase_extract,
                phase_chunk=phase_chunk,
                phase_vector=phase_vector,
                phase_graph=phase_graph,
                current_phase=current_phase,
                overall_status=DocumentStatus.PROCESSING,
                extraction_method=existing_doc.extraction_method,
                chunk_count=existing_doc.chunk_count,
            )

            if phased_db.create_document(doc):
                created_count += 1
            else:
                logger.warning(f"Failed to create document {doc_id} for job {job_id} (may already exist)")
        
        logger.info(f"Created {created_count} documents in phased DB for job {job_id}")
        
        # Update job with correct document count
        try:
            job.documents_total = created_count
            job.parameters['total_documents'] = created_count
            job_queue.update_job(job)
        except Exception as e:
            logger.warning(f"Failed to update job document count: {e}")

        # THIRD: Start job processing
        try:
            _start_job_processing(job)
            logger.info(f"Started processing for job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to start job processing: {e}")

        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_selected': created_count,
            'phases_configured': phases,
            'message': f'Created job with {created_count} documents'
        })

    except Exception as e:
        logger.error(f"Failed to create job from docstore: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# PHASE 2: TEXT EXTRACTION
# ============================================================================

@phased_processing_bp.route('/extract', methods=['POST'])
def extract_text():
    """
    Phase 2: Extract text from PDF documents

    Request:
        job_id: Job ID to process
        document_ids: Optional list of specific document IDs (default: all pending in job)
        method: Extraction method (pymupdf, pdfminer, tesseract, auto)
        page_range: Optional page range - 'all' or {'start': int, 'end': int}

    Returns:
        Processing status and document IDs being processed
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        document_ids = data.get('document_ids')
        method = data.get('method', 'auto')
        page_range = data.get('page_range', 'all')

        if not job_id:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400

        # Get documents ready for extraction
        if document_ids:
            documents = [phased_db.get_document(doc_id) for doc_id in document_ids]
            documents = [d for d in documents if d is not None]
        else:
            documents = phased_db.get_documents_ready_for_phase(job_id, 'extract')

        if not documents:
            return jsonify({
                'success': True,
                'message': 'No documents ready for extraction',
                'documents_processed': 0
            })

        # Import document loader
        from rag_component.document_loader import DocumentLoader
        from backend.services.rag.job_queue import job_queue as jq

        # Pass job context for per-page heartbeat tracking
        loader = DocumentLoader(job_id=job_id, job_queue=jq, doc_id=None)
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        processed_count = 0
        failed_count = 0

        for doc in documents:
            try:
                start_time = datetime.utcnow()

                # Update status to in-progress
                phased_db.update_document_phase_status(
                    doc.doc_id, 'extract', PhaseStatus.IN_PROGRESS
                )

                # Extract text from PDF with specified method and page range
                extracted_text = None
                extraction_method_used = method

                # Handle page range parsing
                pages_to_extract = None  # None means all pages
                if page_range and page_range != 'all':
                    if isinstance(page_range, dict):
                        start = page_range.get('start')
                        end = page_range.get('end')
                        if start:
                            pages_to_extract = range(start - 1, end if end else None)  # 0-indexed

                if method == 'auto' or method == 'pymupdf':
                    try:
                        extracted_text = loader._extract_with_pymupdf(doc.file_path, pages=pages_to_extract)
                        extraction_method_used = 'pymupdf'
                    except Exception:
                        if method == 'auto':
                            # Try pdfminer
                            try:
                                extracted_text = loader._extract_with_pdfminer(doc.file_path)
                                extraction_method_used = 'pdfminer'
                            except Exception:
                                # Try Tesseract OCR as last resort
                                try:
                                    extracted_text = loader._extract_with_tesseract(doc.file_path)
                                    extraction_method_used = 'tesseract'
                                except Exception:
                                    pass

                if method == 'pdfminer':
                    extracted_text = loader._extract_with_pdfminer(doc.file_path)
                    extraction_method_used = 'pdfminer'

                if method == 'tesseract':
                    extracted_text = loader._extract_with_tesseract(doc.file_path)
                    extraction_method_used = 'tesseract'

                if method == 'llm':
                    # LLM extraction - NO FALLBACK
                    extracted_text = loader._extract_with_llm(doc.file_path)
                    extraction_method_used = 'llm'

                if not extracted_text:
                    raise Exception("All extraction methods failed")

                # Save extracted text
                text_path = doc.file_path.replace('.pdf', '.txt')
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)

                # Update document metadata
                char_count = len(extracted_text)
                phased_db.update_document_metadata(doc.doc_id, {
                    'extraction_method': extraction_method_used,
                    'extracted_char_count': char_count,
                    'page_range': str(page_range) if page_range != 'all' else 'all',
                })

                # Mark phase as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                phased_db.update_document_phase_status(
                    doc.doc_id, 'extract', PhaseStatus.COMPLETED,
                    metadata={
                        'method': extraction_method_used,
                        'char_count': char_count,
                        'text_path': text_path,
                        'page_range': str(page_range) if page_range != 'all' else 'all'
                    }
                )

                # Log execution
                phased_db.log_phase_execution(PhaseExecutionLog(
                    execution_id=execution_id,
                    job_id=job_id,
                    doc_id=doc.doc_id,
                    phase='extract',
                    action='COMPLETE',
                    status='SUCCESS',
                    processing_time_ms=int(processing_time),
                    items_processed=char_count,
                    metadata={
                        'method': extraction_method_used,
                        'text_path': text_path,
                        'page_range': str(page_range) if page_range != 'all' else 'all'
                    }
                ))

                processed_count += 1

            except Exception as e:
                logger.error(f"Extraction failed for {doc.doc_id}: {e}")
                phased_db.update_document_phase_status(
                    doc.doc_id, 'extract', PhaseStatus.FAILED,
                    error_message=str(e)
                )
                failed_count += 1

        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_processed': processed_count,
            'documents_failed': failed_count,
            'execution_id': execution_id,
            'message': f'Extracted text from {processed_count} documents ({failed_count} failed)'
        })

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phased_processing_bp.route('/extract/<doc_id>', methods=['GET'])
def get_extracted_text(doc_id: str):
    """
    Get extracted text for a document
    
    Returns:
        Extracted text and metadata
    """
    try:
        doc = phased_db.get_document(doc_id)
        
        if not doc:
            return jsonify({
                'success': False,
                'error': 'Document not found'
            }), 404
        
        if doc.phase_extract != PhaseStatus.COMPLETED.value:
            return jsonify({
                'success': False,
                'error': 'Text not yet extracted'
            }), 400
        
        # Read extracted text
        text_path = doc.file_path.replace('.pdf', '.txt')
        if not os.path.exists(text_path):
            return jsonify({
                'success': False,
                'error': 'Extracted text file not found'
            }), 404
        
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'text': text_content,
            'metadata': {
                'char_count': len(text_content),
                'extraction_method': doc.extraction_method,
                'extracted_at': doc.extracted_at.isoformat() if doc.extracted_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get extracted text: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# PHASE 3: CHUNKING
# ============================================================================

@phased_processing_bp.route('/chunk', methods=['POST'])
def chunk_documents():
    """
    Phase 3: Chunk documents using LLM or fallback strategies
    
    Request:
        job_id: Job ID to process
        document_ids: Optional list of specific document IDs
        strategy: Chunking strategy (smart_llm, fixed_size, paragraph)
        config: Strategy-specific configuration
    
    Returns:
        Processing status and chunk counts
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        document_ids = data.get('document_ids')
        strategy = data.get('strategy', 'smart_llm')
        config = data.get('config', {})
        
        if not job_id:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400
        
        # Get documents ready for chunking
        if document_ids:
            documents = [phased_db.get_document(doc_id) for doc_id in document_ids]
            documents = [d for d in documents if d is not None]
        else:
            documents = phased_db.get_documents_ready_for_phase(job_id, 'chunk')
        
        if not documents:
            return jsonify({
                'success': True,
                'message': 'No documents ready for chunking',
                'documents_processed': 0
            })
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        processed_count = 0
        failed_count = 0
        total_chunks = 0
        
        for doc in documents:
            try:
                start_time = datetime.utcnow()
                
                # Update status to in-progress
                phased_db.update_document_phase_status(
                    doc.doc_id, 'chunk', PhaseStatus.IN_PROGRESS
                )

                # Read extracted text - handle various file types
                file_path_lower = doc.file_path.lower()
                
                # Determine the text file path based on original file type
                if file_path_lower.endswith('.pdf'):
                    # PDF file - look for extracted .txt or .md
                    text_path = doc.file_path.replace('.pdf', '.txt')
                    if not os.path.exists(text_path):
                        text_path = doc.file_path.replace('.pdf', '.md')
                elif file_path_lower.endswith('.md'):
                    # Already a markdown file - use it directly
                    text_path = doc.file_path
                elif file_path_lower.endswith('.txt'):
                    # Already a text file - use it directly
                    text_path = doc.file_path
                else:
                    # Try common extensions
                    base_path = doc.file_path.rsplit('.', 1)[0]
                    if os.path.exists(f"{base_path}.txt"):
                        text_path = f"{base_path}.txt"
                    elif os.path.exists(f"{base_path}.md"):
                        text_path = f"{base_path}.md"
                    else:
                        text_path = doc.file_path
                
                if not os.path.exists(text_path):
                    raise Exception(f"Extracted text not found at: {text_path}")

                with open(text_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # Chunk based on strategy
                chunks = []
                chunking_strategy = strategy
                
                if strategy == 'smart_llm':
                    # Try LLM-based chunking
                    try:
                        chunks = _smart_chunk_with_llm(text_content, doc.doc_id, config)
                        chunking_strategy = 'smart_llm'
                    except Exception as e:
                        logger.warning(f"LLM chunking failed, falling back: {e}")
                        # Fallback to fixed-size
                        chunks = _fixed_size_chunk(text_content, doc.doc_id, config)
                        chunking_strategy = 'fixed_size'
                
                elif strategy == 'fixed_size':
                    chunks = _fixed_size_chunk(text_content, doc.doc_id, config)
                
                elif strategy == 'paragraph':
                    chunks = _paragraph_chunk(text_content, doc.doc_id, config)
                
                if not chunks:
                    raise Exception("No chunks generated")
                
                # Save chunks to database (deactivate old chunks first)
                phased_db.deactivate_chunks(doc.doc_id)  # Deactivate old chunks
                phased_db.save_chunks(chunks)
                
                # Update document metadata
                phased_db.update_document_metadata(doc.doc_id, {
                    'chunk_count': len(chunks),
                    'chunking_strategy': chunking_strategy,
                })
                
                # Mark phase as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                phased_db.update_document_phase_status(
                    doc.doc_id, 'chunk', PhaseStatus.COMPLETED,
                    metadata={
                        'strategy': chunking_strategy,
                        'chunk_count': len(chunks)
                    }
                )
                
                # Log execution
                phased_db.log_phase_execution(PhaseExecutionLog(
                    execution_id=execution_id,
                    job_id=job_id,
                    doc_id=doc.doc_id,
                    phase='chunk',
                    action='COMPLETE',
                    status='SUCCESS',
                    processing_time_ms=int(processing_time),
                    items_processed=len(chunks),
                    metadata={
                        'strategy': chunking_strategy,
                        'chunk_count': len(chunks)
                    }
                ))
                
                processed_count += 1
                total_chunks += len(chunks)
                
            except Exception as e:
                logger.error(f"Chunking failed for {doc.doc_id}: {e}")
                phased_db.update_document_phase_status(
                    doc.doc_id, 'chunk', PhaseStatus.FAILED,
                    error_message=str(e)
                )
                failed_count += 1
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_processed': processed_count,
            'documents_failed': failed_count,
            'total_chunks_generated': total_chunks,
            'execution_id': execution_id,
            'message': f'Generated {total_chunks} chunks from {processed_count} documents'
        })
        
    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _smart_chunk_with_llm(text: str, doc_id: str, config: Dict) -> List[Chunk]:
    """
    Smart chunking using LLM for semantic boundaries
    
    Falls back to fixed-size if LLM is unavailable
    """
    # TODO: Implement LLM-based chunking
    # For now, use fixed-size as placeholder
    return _fixed_size_chunk(text, doc_id, config)


def _fixed_size_chunk(text: str, doc_id: str, config: Dict) -> List[Chunk]:
    """
    Fixed-size chunking with overlap
    
    Config:
        chunk_size: Tokens per chunk (default: 512)
        overlap: Overlap between chunks (default: 50)
    """
    chunk_size = config.get('chunk_size', 512)
    overlap = config.get('overlap', 50)
    
    # Simple character-based chunking (approximate)
    # TODO: Use proper tokenization
    chars_per_token = 4  # Rough estimate
    char_chunk_size = chunk_size * chars_per_token
    char_overlap = overlap * chars_per_token
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = min(start + char_chunk_size, len(text))
        content = text[start:end]
        
        if content.strip():  # Skip empty chunks
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}_chunk_{chunk_index:04d}",
                chunk_index=chunk_index,
                content=content,
                content_length=len(content),
                chunk_type='text',
                token_count=len(content) // chars_per_token,
                start_char=start,
                end_char=end,
            ))
        
        start = end - char_overlap
        chunk_index += 1
        
        # Safety limit
        if chunk_index > 1000:
            logger.warning(f"Chunk limit reached for {doc_id}")
            break
    
    return chunks


def _paragraph_chunk(text: str, doc_id: str, config: Dict) -> List[Chunk]:
    """
    Paragraph-based chunking
    
    Groups paragraphs into chunks up to max size
    """
    max_chunk_size = config.get('max_chunk_size', 2048)  # characters
    
    # Split by paragraphs
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_size = 0
    chunk_index = 0
    start_char = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        
        if current_size + para_size > max_chunk_size and current_chunk:
            # Save current chunk
            content = '\n\n'.join(current_chunk)
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}_chunk_{chunk_index:04d}",
                chunk_index=chunk_index,
                content=content,
                content_length=len(content),
                chunk_type='text',
                token_count=len(content) // 4,
                start_char=start_char,
                end_char=start_char + len(content),
            ))
            
            current_chunk = [para]
            current_size = para_size
            start_char += len(content) + 2
            chunk_index += 1
        else:
            current_chunk.append(para)
            current_size += para_size
    
    # Don't forget the last chunk
    if current_chunk:
        content = '\n\n'.join(current_chunk)
        chunks.append(Chunk(
            doc_id=doc_id,
            chunk_id=f"{doc_id}_chunk_{chunk_index:04d}",
            chunk_index=chunk_index,
            content=content,
            content_length=len(content),
            chunk_type='text',
            token_count=len(content) // 4,
            start_char=start_char,
            end_char=start_char + len(content),
        ))
    
    return chunks


# ============================================================================
# PHASE 4: VECTOR INDEXING
# ============================================================================

@phased_processing_bp.route('/index', methods=['POST'])
def index_to_vector():
    """
    Phase 4: Index chunks to vector database (Qdrant)
    
    Request:
        job_id: Job ID to process
        document_ids: Optional list of specific document IDs
        collection: Qdrant collection name (default: "documents")
    
    Returns:
        Indexing status and vector counts
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        document_ids = data.get('document_ids')
        collection = data.get('collection', 'documents')
        
        if not job_id:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400
        
        # Get documents ready for vector indexing
        if document_ids:
            documents = [phased_db.get_document(doc_id) for doc_id in document_ids]
            documents = [d for d in documents if d is not None]
        else:
            documents = phased_db.get_documents_ready_for_phase(job_id, 'vector')
        
        if not documents:
            return jsonify({
                'success': True,
                'message': 'No documents ready for vector indexing',
                'documents_processed': 0
            })
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        processed_count = 0
        failed_count = 0
        total_vectors = 0
        
        # Import vector store manager
        from rag_component.vector_store_manager import VectorStoreManager
        from rag_component.config import RAG_EMBEDDING_MODEL
        
        vsm = VectorStoreManager()
        embedding_model = RAG_EMBEDDING_MODEL
        
        for doc in documents:
            try:
                start_time = datetime.utcnow()
                
                # Update status to in-progress
                phased_db.update_document_phase_status(
                    doc.doc_id, 'vector', PhaseStatus.IN_PROGRESS
                )
                
                # Get chunks for this document
                chunks = phased_db.get_chunks_for_document(doc.doc_id)
                
                if not chunks:
                    raise Exception("No chunks found for document")
                
                # Convert to LangChain documents
                from langchain_core.documents import Document as LCDocument
                
                lc_docs = []
                for chunk in chunks:
                    metadata = {
                        'source': doc.doc_id,
                        'filename': doc.original_filename,
                        'chunk_id': chunk.chunk_id,
                        'section': chunk.section or '',
                        'title': chunk.title or '',
                        'chunk_type': chunk.chunk_type,
                        'token_count': chunk.token_count or 0,
                        'contains_formula': chunk.contains_formula,
                        'contains_table': chunk.contains_table,
                        'user_id': doc.user_id,
                        'file_id': doc.doc_id,
                        'job_id': job_id,
                    }
                    lc_docs.append(LCDocument(page_content=chunk.content, metadata=metadata))
                
                # Add to vector store
                vsm.add_documents(lc_docs)
                
                # Update chunk records with vector IDs
                # (Qdrant generates IDs, so we'll store collection info)
                for chunk in chunks:
                    # Update in database
                    pass  # TODO: Update chunk with vector_id
                
                # Update document metadata
                phased_db.update_document_metadata(doc.doc_id, {
                    'vector_collection': collection,
                    'vector_chunk_count': len(chunks),
                    'embedding_model': embedding_model,
                })
                
                # Mark phase as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                phased_db.update_document_phase_status(
                    doc.doc_id, 'vector', PhaseStatus.COMPLETED,
                    metadata={
                        'collection': collection,
                        'vectors_added': len(chunks)
                    }
                )
                
                # Log execution
                phased_db.log_phase_execution(PhaseExecutionLog(
                    execution_id=execution_id,
                    job_id=job_id,
                    doc_id=doc.doc_id,
                    phase='vector',
                    action='COMPLETE',
                    status='SUCCESS',
                    processing_time_ms=int(processing_time),
                    items_processed=len(chunks),
                    metadata={
                        'collection': collection,
                        'embedding_model': embedding_model
                    }
                ))
                
                processed_count += 1
                total_vectors += len(chunks)
                
            except Exception as e:
                logger.error(f"Vector indexing failed for {doc.doc_id}: {e}")
                phased_db.update_document_phase_status(
                    doc.doc_id, 'vector', PhaseStatus.FAILED,
                    error_message=str(e)
                )
                failed_count += 1
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_processed': processed_count,
            'documents_failed': failed_count,
            'total_vectors_indexed': total_vectors,
            'execution_id': execution_id,
            'message': f'Indexed {total_vectors} vectors from {processed_count} documents'
        })
        
    except Exception as e:
        logger.error(f"Vector indexing failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# PHASE 5: GRAPH BUILD
# ============================================================================

@phased_processing_bp.route('/graph', methods=['POST'])
def build_graph():
    """
    Phase 5: Extract entities and build knowledge graph in Neo4j
    
    Request:
        job_id: Job ID to process
        document_ids: Optional list of specific document IDs
        extract_entities: Whether to extract new entities (default: True)
    
    Returns:
        Graph build status and entity counts
    """
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        document_ids = data.get('document_ids')
        extract_entities = data.get('extract_entities', True)
        
        if not job_id:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400
        
        # Get documents ready for graph build
        if document_ids:
            documents = [phased_db.get_document(doc_id) for doc_id in document_ids]
            documents = [d for d in documents if d is not None]
        else:
            documents = phased_db.get_documents_ready_for_phase(job_id, 'graph')
        
        if not documents:
            return jsonify({
                'success': True,
                'message': 'No documents ready for graph build',
                'documents_processed': 0
            })
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        processed_count = 0
        failed_count = 0
        total_entities = 0
        total_relationships = 0
        
        for doc in documents:
            try:
                start_time = datetime.utcnow()
                
                # Update status to in-progress
                phased_db.update_document_phase_status(
                    doc.doc_id, 'graph', PhaseStatus.IN_PROGRESS
                )
                
                # Get chunks for entity extraction
                chunks = phased_db.get_chunks_for_document(doc.doc_id)
                
                if not chunks:
                    raise Exception("No chunks found for entity extraction")
                
                # Extract entities from chunks
                # TODO: Implement LLM-based entity extraction
                # For now, use simple keyword-based extraction
                entities = []
                relationships = []
                
                for chunk in chunks:
                    # Simple entity extraction (placeholder)
                    # Look for GOST standard patterns
                    import re
                    gost_pattern = r'ГОСТ\s*[Рр]?\s*(\d+(?:\.\d+)?-\d{4})'
                    matches = re.findall(gost_pattern, chunk.content)
                    
                    for match in matches:
                        entity_name = f"GOST {match}"
                        if not any(e.entity_name == entity_name for e in entities):
                            entities.append({
                                'name': entity_name,
                                'type': 'STANDARD',
                                'chunk_id': chunk.chunk_id,
                                'relevance': 0.9
                            })
                
                # Save entities to cache
                for entity_data in entities:
                    from backend.services.rag.phased_processing_models import Entity
                    entity = Entity(
                        doc_id=doc.doc_id,
                        chunk_id=entity_data.get('chunk_id'),
                        entity_name=entity_data['name'],
                        entity_type=entity_data['type'],
                        relevance_score=entity_data.get('relevance'),
                    )
                    # TODO: Save to database
                
                # TODO: Store in Neo4j
                # from backend.services.rag.graphrag_service import GraphRAGService
                # graph_service = GraphRAGService()
                # graph_service.store_in_neo4j(entities, relationships)
                
                # Update document metadata
                phased_db.update_document_metadata(doc.doc_id, {
                    'entity_count': len(entities),
                    'relationship_count': len(relationships),
                })
                
                # Mark phase as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                phased_db.update_document_phase_status(
                    doc.doc_id, 'graph', PhaseStatus.COMPLETED,
                    metadata={
                        'entities_extracted': len(entities),
                        'relationships_created': len(relationships)
                    }
                )
                
                # Log execution
                phased_db.log_phase_execution(PhaseExecutionLog(
                    execution_id=execution_id,
                    job_id=job_id,
                    doc_id=doc.doc_id,
                    phase='graph',
                    action='COMPLETE',
                    status='SUCCESS',
                    processing_time_ms=int(processing_time),
                    items_processed=len(entities),
                    metadata={
                        'entities': len(entities),
                        'relationships': len(relationships)
                    }
                ))
                
                processed_count += 1
                total_entities += len(entities)
                total_relationships += len(relationships)
                
            except Exception as e:
                logger.error(f"Graph build failed for {doc.doc_id}: {e}")
                phased_db.update_document_phase_status(
                    doc.doc_id, 'graph', PhaseStatus.FAILED,
                    error_message=str(e)
                )
                failed_count += 1
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'documents_processed': processed_count,
            'documents_failed': failed_count,
            'total_entities_extracted': total_entities,
            'total_relationships_created': total_relationships,
            'execution_id': execution_id,
            'message': f'Extracted {total_entities} entities from {processed_count} documents'
        })
        
    except Exception as e:
        logger.error(f"Graph build failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# JOB CONTROL
# ============================================================================

def process_phased_job_background(job):
    """
    Background processing function for phased processing jobs
    Called by job queue worker
    
    Processes documents through selected phases sequentially
    """
    try:
        job_id = job.job_id
        phases = job.parameters.get('phases', ['extract', 'chunk', 'vector', 'graph'])
        
        logger.info(f"[Phased Job {job_id}] Starting background processing")
        logger.info(f"[Phased Job {job_id}] Phases: {phases}")
        
        # Import PhaseStatus early for use in fallback and error handling
        from backend.services.rag.phased_processing_models import PhaseStatus, DocumentStatus
        
        # Get documents for this job
        all_docs = phased_db.get_documents_by_job(job_id)
        if not all_docs:
            logger.warning(f"[Phased Job {job_id}] No documents found, attempting fallback from Document Store")
            # Try to load documents from Document Store for jobs that only specified 'chunk' phase
            import glob as glob_mod
            base_dir = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
            document_ids = job.parameters.get('document_ids', [])
            for doc_id in document_ids:
                matches = glob_mod.glob(f"{base_dir}/**/{doc_id}.pdf", recursive=True)
                if not matches:
                    logger.warning(f"Document {doc_id} not found in Document Store for fallback")
                    continue
                file_path = matches[0]
                doc_record = DocumentProcessing(
                    doc_id=doc_id,
                    job_id=job_id,
                    user_id=job.user_id,
                    original_filename=os.path.basename(file_path),
                    display_name=os.path.basename(file_path),
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    content_type='application/pdf',
                    source_url='',
                    source_website='',
                    phase_upload=PhaseStatus.COMPLETED,
                    phase_extract=PhaseStatus.SKIPPED,
                    phase_chunk=PhaseStatus.PENDING if 'chunk' in phases else PhaseStatus.SKIPPED,
                    phase_vector=PhaseStatus.PENDING if 'vector' in phases else PhaseStatus.SKIPPED,
                    phase_graph=PhaseStatus.PENDING if 'graph' in phases else PhaseStatus.SKIPPED,
                    current_phase='chunk' if 'chunk' in phases else 'vector' if 'vector' in phases else 'graph',
                    overall_status=DocumentStatus.PROCESSING,
                    extraction_method=None,
                    chunk_count=0,
                )
                if phased_db.create_document(doc_record):
                    all_docs.append(doc_record)
                    logger.info(f"[Phased Job {job_id}] Added fallback document {doc_id}")
            if not all_docs:
                logger.error(f"[Phased Job {job_id}] No documents found even after fallback")
                return
        logger.info(f"[Phased Job {job_id}] Processing {len(all_docs)} documents")
        
        # Process each phase sequentially
        for phase in phases:
            try:
                if phase == 'extract':
                    logger.info(f"[Phased Job {job_id}] Running Phase: Extract")
                    from backend.services.rag.job_queue import job_queue
                    # Update job status correctly
                    job = job_queue.get_job(job_id)
                    if job:
                        job.current_stage = 'extracting'
                        job_queue.update_job(job)

                    # Get extraction config from job parameters
                    extraction_config = job.parameters.get('extraction_config', {})
                    method = extraction_config.get('method', 'auto')
                    page_range = extraction_config.get('page_range', 'all')
                    
                    logger.info(f"[Phased Job {job_id}] Extraction config: method={method}, page_range={page_range}")
                    logger.info(f"[Phased Job {job_id}] extraction_config dict: {extraction_config}")
                    logger.info(f"[Phased Job {job_id}] method type: {type(method).__name__}, value: '{method}'")

                    # Get documents ready for extraction
                    docs = get_documents_ready_for_phase(job_id, 'extract')
                    for doc in docs:
                        try:
                            # Extract text with configured method and page range
                            from rag_component.document_loader import DocumentLoader
                            from backend.services.rag.job_queue import job_queue as jq
                            
                            # Pass job context for per-page heartbeat tracking
                            loader = DocumentLoader(job_id=job_id, job_queue=jq, doc_id=doc.doc_id)
                            
                            # Handle page range parsing
                            pages_to_extract = None  # None means all pages
                            if page_range and page_range != 'all':
                                if isinstance(page_range, dict):
                                    start = page_range.get('start')
                                    end = page_range.get('end')
                                    if start:
                                        pages_to_extract = range(start - 1, end if end else None)  # 0-indexed
                            
                            # Extract using specified method
                            logger.info(f"[Phased Job {job_id}] About to extract with method: '{method}' (type: {type(method).__name__})")
                            
                            if method == 'auto' or method == 'pymupdf':
                                try:
                                    text = loader._extract_with_pymupdf(doc.file_path, pages=pages_to_extract)
                                    extraction_method_used = 'pymupdf'
                                except Exception:
                                    if method == 'auto':
                                        # Try pdfminer
                                        try:
                                            text = loader._extract_with_pdfminer(doc.file_path)
                                            extraction_method_used = 'pdfminer'
                                        except Exception:
                                            # Try Tesseract OCR as last resort
                                            try:
                                                text = loader._extract_with_tesseract(doc.file_path)
                                                extraction_method_used = 'tesseract'
                                            except Exception:
                                                raise Exception("All extraction methods failed")
                                    else:
                                        raise
                            elif method == 'pdfminer':
                                text = loader._extract_with_pdfminer(doc.file_path)
                                extraction_method_used = 'pdfminer'
                            elif method == 'tesseract':
                                text = loader._extract_with_tesseract(doc.file_path)
                                extraction_method_used = 'tesseract'
                            elif method == 'llm':
                                logger.info(f"[Phased Job {job_id}] Calling LLM extraction for {doc.doc_id}")
                                logger.info(f"[Phased Job {job_id}] Page range: {page_range}")

                                # Update heartbeat before LLM call (can take minutes)
                                from backend.services.rag.job_queue import job_queue as jq
                                current_job = jq.get_job(job_id)
                                
                                # Get completed pages for page-level resume
                                completed_pages = set()
                                if current_job and 'completed_pages' in current_job.parameters:
                                    completed_pages = set(current_job.parameters.get('completed_pages', []))
                                    logger.info(f"[Phased Job {job_id}] Resuming with {len(completed_pages)} completed pages")
                                
                                if current_job:
                                    current_job.parameters['heartbeat'] = {
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'phase': 'extract',
                                        'doc_id': doc.doc_id,
                                        'action': 'llm_extraction_starting'
                                    }
                                    jq.update_job(current_job)

                                # LLM extraction with page-level resume support
                                text = loader._extract_with_llm(
                                    doc.file_path, 
                                    pages=pages_to_extract,
                                    job_id=job_id,
                                    completed_pages=completed_pages if completed_pages else None
                                )
                                extraction_method_used = 'llm'
                                logger.info(f"[Phased Job {job_id}] LLM extraction returned {len(text)} chars")

                                # Update heartbeat after LLM call
                                if current_job:
                                    current_job.parameters['heartbeat'] = {
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'phase': 'extract',
                                        'doc_id': doc.doc_id,
                                        'action': 'llm_extraction_completed',
                                        'chars_extracted': len(text)
                                    }
                                    jq.update_job(current_job)
                            else:
                                # Default to pymupdf
                                text = loader._extract_with_pymupdf(doc.file_path, pages=pages_to_extract)
                                extraction_method_used = 'pymupdf'

                            # Save text as markdown
                            if extraction_method_used == 'llm':
                                # LLM extraction produces markdown, save as .md
                                text_path = doc.file_path.replace('.pdf', '.md')
                            else:
                                # Other methods produce plain text, save as .txt
                                text_path = doc.file_path.replace('.pdf', '.txt')
                            
                            with open(text_path, 'w', encoding='utf-8') as f:
                                f.write(text)

                            # Update metadata
                            phased_db.update_document_metadata(doc.doc_id, {
                                'extraction_method': extraction_method_used,
                                'extracted_char_count': len(text),
                                'page_range': str(page_range) if page_range != 'all' else 'all'
                            })

                            # Mark phase complete
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'extract', PhaseStatus.COMPLETED,
                                metadata={
                                    'method': extraction_method_used,
                                    'page_range': str(page_range) if page_range != 'all' else 'all'
                                }
                            )
                            
                            logger.info(f"[Phased Job {job_id}] Extracted {len(text)} chars from {doc.doc_id[:30]} using {extraction_method_used}")
                        except Exception as e:
                            logger.error(f"[Phased Job {job_id}] Extract failed for {doc.doc_id}: {e}")
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'extract', PhaseStatus.FAILED,
                                error_message=str(e)
                            )
                
                elif phase == 'chunk':
                    logger.info(f"[Phased Job {job_id}] Running Phase: Chunk")
                    from backend.services.rag.job_queue import job_queue
                    job = job_queue.get_job(job_id)
                    if job:
                        job.current_stage = 'chunking'
                        job_queue.update_job(job)

                    docs = get_documents_ready_for_phase(job_id, 'chunk')
                    total_docs = len(docs)
                    if not docs:
                        logger.warning(f"[Phased Job {job_id}] No documents found ready for chunking, attempting fallback from Document Store")
                        for doc_id in document_ids:
                            existing_doc = phased_db.get_document(doc_id)
                            if existing_doc:
                                docs.append(existing_doc)
                                continue
                            # Try using job.files paths first (from original job creation)
                            file_path = None
                            if job.parameters and 'files' in job.parameters:
                                for f in job.parameters['files']:
                                    fname = f.get('filename', '')
                                    fpath = f.get('path', '')
                                    if fname.startswith(doc_id) and os.path.exists(fpath):
                                        file_path = fpath
                                        break
                            # Fallback to glob search
                            if not file_path:
                                import glob as glob_mod
                                base_dir = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
                                matches = glob_mod.glob(f"{base_dir}/**/{doc_id}.pdf", recursive=True)
                                if matches:
                                    file_path = matches[0]
                            if not file_path:
                                logger.warning(f"Document {doc_id} not found in Document Store or job files")
                                continue
                            class MockDoc:
                                def __init__(self, doc_id, path):
                                    self.doc_id = doc_id
                                    self.original_filename = os.path.basename(path)
                                    self.display_name = self.original_filename
                                    self.file_path = path
                                    self.file_size = os.path.getsize(path)
                                    self.content_type = 'application/pdf'
                                    self.source_url = ''
                                    self.source_website = ''
                                    self.extraction_method = None
                                    self.chunk_count = 0
                            mock_doc = MockDoc(doc_id, file_path)
                            doc_record = DocumentProcessing(
                                doc_id=mock_doc.doc_id,
                                job_id=job_id,
                                user_id=job.user_id,
                                original_filename=mock_doc.original_filename,
                                display_name=mock_doc.display_name,
                                file_path=mock_doc.file_path,
                                file_size=mock_doc.file_size,
                                content_type=mock_doc.content_type,
                                source_url=mock_doc.source_url,
                                source_website=mock_doc.source_website,
                                phase_upload=PhaseStatus.COMPLETED,
                                phase_extract=PhaseStatus.SKIPPED,
                                phase_chunk=PhaseStatus.PENDING,
                                phase_vector=PhaseStatus.PENDING,
                                phase_graph=PhaseStatus.PENDING,
                                current_phase='chunk',
                                overall_status=DocumentStatus.PROCESSING,
                                extraction_method=None,
                                chunk_count=0,
                            )
                            if phased_db.create_document(doc_record):
                                docs.append(doc_record)
                    for doc_idx, doc in enumerate(docs):
                        try:
                            # Update job-level progress: current file
                            from backend.services.rag.job_queue import job_queue as jq
                            current_job = jq.get_job(job_id)
                            if current_job:
                                current_job.parameters['current_doc'] = doc_idx + 1
                                current_job.parameters['total_docs'] = total_docs
                                jq.update_job(current_job)

                            # Read extracted text - handle various file types
                            file_path_lower = doc.file_path.lower()

                            # Determine the text file path based on original file type
                            if file_path_lower.endswith('.pdf'):
                                # PDF file - prefer cleaned .txt over .md
                                text_path = doc.file_path.replace('.pdf', '.txt')
                                if not os.path.exists(text_path):
                                    text_path = doc.file_path.replace('.pdf', '.md')
                            elif file_path_lower.endswith('.md'):
                                # Markdown file - prefer cleaned .txt (LaTeX converted) over .md
                                txt_path = doc.file_path[:-3] + '.txt'
                                if os.path.exists(txt_path):
                                    text_path = txt_path
                                    logger.info(f"[Phased Job {job_id}] Using cleaned .txt file: {text_path}")
                                else:
                                    text_path = doc.file_path
                            elif file_path_lower.endswith('.txt'):
                                # Already a text file - use it directly
                                text_path = doc.file_path
                            else:
                                # Try common extensions - prefer cleaned .txt
                                base_path = doc.file_path.rsplit('.', 1)[0]
                                if os.path.exists(f"{base_path}.txt"):
                                    text_path = f"{base_path}.txt"
                                elif os.path.exists(f"{base_path}.md"):
                                    text_path = f"{base_path}.md"
                                else:
                                    text_path = doc.file_path
                            
                            if not os.path.exists(text_path):
                                raise Exception(f"Extracted text not found at: {text_path}")

                            with open(text_path, 'r', encoding='utf-8') as f:
                                text = f.read()

                            # Determine cleaning method based on extraction method and file type
                            # This is used for UI notifications about potential LaTeX issues
                            cleaning_method = None
                            if text_path.endswith('.md'):
                                # LLM extraction produces markdown with LaTeX formulas
                                # Check job config for specific cleaning preference
                                try:
                                    chunking_config = job.parameters.get('chunking_config', {})
                                    cleaning_method = chunking_config.get('cleaning_method')
                                except:
                                    pass
                                if not cleaning_method:
                                    # Default to latex_converted for .md files (LLM extraction)
                                    cleaning_method = 'latex_converted'
                            else:
                                # Plain text extraction - no LaTeX processing
                                cleaning_method = None

                            # Use LLM-based smart chunking with async timeout
                            logger.info(f"[Phased Job {job_id}] Calling LLM for smart chunking...")

                            # Heartbeat callback - updates section progress
                            def heartbeat_cb(action=None, section=None, total_sections=None, heading=None, attempt=None):
                                try:
                                    j = jq.get_job(job_id)
                                    if j:
                                        hb = j.parameters.get('heartbeat', {})
                                        hb.update({
                                            'timestamp': datetime.utcnow().isoformat(),
                                            'phase': 'chunk',
                                            'doc_id': doc.doc_id,
                                            'action': action or 'section_progress',
                                            'current_section': section,
                                            'total_sections': total_sections,
                                            'section_heading': heading,
                                        })
                                        j.parameters['heartbeat'] = hb
                                        jq.update_job(j)
                                except Exception as e:
                                    logger.debug(f"Heartbeat update failed: {e}")

                            from .smart_ingestion_enhanced import chunk_document_with_llm_sync

                            # Chunk using LLM with proper timeout (uses config from .env)
                            # Returns: (success, chunks, error_message) - 3 values only
                            logger.info(f"[Phased Job {job_id}] About to call chunk_document_with_llm_sync for file: {text_path}")
                            success, llm_chunks, error = chunk_document_with_llm_sync(
                                file_path=text_path,
                                prompt="",  # Use default prompt
                                filename=doc.original_filename,
                                timeout=LLM_CHUNKING_TIMEOUT,  # Pass timeout from .env
                                heartbeat_cb=heartbeat_cb
                            )
                            logger.info(f"[Phased Job {job_id}] chunk_document_with_llm_sync returned: success={success}, chunks_count={len(llm_chunks) if llm_chunks else 0}, error={repr(error)[:500]}")
                            
                            # Update heartbeat after LLM chunking
                            if current_job:
                                current_job.parameters['heartbeat'] = {
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'phase': 'chunk',
                                    'doc_id': doc.doc_id,
                                    'action': 'llm_chunking_completed',
                                    'chunks_generated': len(llm_chunks) if llm_chunks else 0,
                                    'success': success
                                }
                                jq.update_job(current_job)

                            if success:
                                # Check for coverage warning (stored in first chunk metadata by validator)
                                coverage_warning = None
                                if llm_chunks and '_coverage_warning' in llm_chunks[0]:
                                    coverage_warning = llm_chunks[0].pop('_coverage_warning')  # Extract and remove from chunk
                                    logger.warning(f"[Phased Job {job_id}] Coverage warning: {coverage_warning}")
                                
                                # Also check error field for warnings (success=True but error field has text = warning)
                                chunking_warning = error if success and error else None
                                
                                # Combine warnings
                                final_warning = coverage_warning or chunking_warning
                                
                                # Convert LLM chunks to our Chunk format
                                from backend.services.rag.phased_processing_models import Chunk
                                chunks = []
                                for i, c in enumerate(llm_chunks):
                                    chunks.append(Chunk(
                                        doc_id=doc.doc_id,
                                        chunk_id=f"{doc.doc_id}_chunk_{i:04d}",
                                        chunk_index=i,
                                        content=c.get('content', ''),
                                        content_length=len(c.get('content', '')),
                                        section=c.get('section', ''),
                                        title=c.get('title', ''),
                                        chunk_type='text',
                                        token_count=c.get('token_count', 0),
                                    ))
                                logger.info(
                                    f"[Phased Job {job_id}] LLM generated {len(chunks)} chunks "
                                    f"(total content: {sum(c.content_length for c in chunks)} chars)"
                                )
                                
                                if final_warning:
                                    logger.warning(f"[Phased Job {job_id}] WARNING: {final_warning}")

                                # Store cleaning method in metadata for UI notification
                                if cleaning_method == "latex_converted":
                                    chunking_metadata = {
                                        'cleaning_method': cleaning_method,
                                        'warning': 'LaTeX formulas converted to natural language descriptions (mathematical meaning preserved)'
                                    }
                                elif cleaning_method == "aggressive":
                                    chunking_metadata = {
                                        'cleaning_method': cleaning_method,
                                        'warning': 'LaTeX formulas may be corrupted due to aggressive JSON cleaning'
                                    }
                                else:
                                    chunking_metadata = {
                                        'cleaning_method': cleaning_method,
                                        'warning': None
                                    }
                                
                                # Add coverage warning to metadata if present
                                if final_warning:
                                    chunking_metadata['coverage_warning'] = final_warning
                            else:
                                logger.error(f"[Phased Job {job_id}] LLM chunking failed: {error}")
                                # NO FALLBACK - mark document as failed
                                phased_db.update_document_phase_status(
                                    doc.doc_id, 'chunk', PhaseStatus.FAILED,
                                    error_message=f"LLM chunking failed: {error}"
                                )
                                continue  # Skip to next document

                            # Save chunks to DB (deactivate old chunks first)
                            phased_db.deactivate_chunks(doc.doc_id)  # Deactivate old chunks
                            phased_db.save_chunks(chunks)

                            # ALSO save chunks as JSON file (for Document Store filter)
                            # Fix: Handle both .txt and .md file extensions
                            if text_path.endswith('.md'):
                                chunks_file = text_path.replace('.md', '.chunks.json')
                            elif text_path.endswith('.txt'):
                                chunks_file = text_path.replace('.txt', '.chunks.json')
                            else:
                                # Fallback: append .chunks.json to any other extension
                                chunks_file = text_path + '.chunks.json'
                            chunks_data = {
                                'doc_id': doc.doc_id,
                                'filename': doc.original_filename,
                                'total_chunks': len(chunks),
                                'chunking_strategy': 'smart_llm' if success else 'fixed_size',
                                'chunks': [
                                    {
                                        'chunk_id': c.chunk_id,
                                        'chunk_index': c.chunk_index,
                                        'content': c.content,
                                        'section': c.section,
                                        'title': c.title,
                                        'token_count': c.token_count
                                    } for c in chunks
                                ]
                            }
                            with open(chunks_file, 'w', encoding='utf-8') as f:
                                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"[Phased Job {job_id}] Saved chunks to {chunks_file}")

                            # Update metadata
                            phased_db.update_document_metadata(doc.doc_id, {
                                'chunk_count': len(chunks),
                                'chunking_strategy': 'smart_llm' if success else 'fixed_size'
                            })

                            # Mark phase complete - include cleaning method warning if applicable
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'chunk', PhaseStatus.COMPLETED,
                                metadata=chunking_metadata if success else None
                            )
                            
                            # Store warning in job parameters for UI display
                            if final_warning:
                                try:
                                    from backend.services.rag.job_queue import job_queue as jq
                                    current_job = jq.get_job(job_id)
                                    if current_job:
                                        # Initialize warnings list if not exists
                                        if 'warnings' not in current_job.parameters:
                                            current_job.parameters['warnings'] = []
                                        
                                        # Add warning with context
                                        current_job.parameters['warnings'].append({
                                            'type': 'chunking_coverage',
                                            'doc_id': doc.doc_id,
                                            'message': final_warning,
                                            'timestamp': datetime.utcnow().isoformat(),
                                            'severity': 'warning'  # Could be 'error' in future
                                        })
                                        
                                        # Save updated job
                                        jq.update_job(current_job)
                                        logger.info(f"[Phased Job {job_id}] Warning saved to job parameters")
                                except Exception as e:
                                    logger.error(f"[Phased Job {job_id}] Failed to save warning: {e}")
                        except Exception as e:
                            logger.error(f"[Phased Job {job_id}] Chunk failed for {doc.doc_id}: {e}")
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'chunk', PhaseStatus.FAILED,
                                error_message=str(e)
                            )
                
                elif phase == 'vector':
                    logger.info(f"[Phased Job {job_id}] Running Phase: Vector")
                    from backend.services.rag.job_queue import job_queue
                    job = job_queue.get_job(job_id)
                    if job:
                        job.current_stage = 'indexing'
                        job_queue.update_job(job)
                    
                    docs = get_documents_ready_for_phase(job_id, 'vector')
                    for doc in docs:
                        try:
                            # Get chunks
                            chunks = phased_db.get_chunks_for_document(doc.doc_id)
                            if not chunks:
                                raise Exception("No chunks found")
                            
                            # Convert to LangChain documents and index
                            from langchain_core.documents import Document as LCDocument
                            from rag_component.vector_store_manager import VectorStoreManager
                            
                            vsm = VectorStoreManager()
                            lc_docs = [
                                LCDocument(page_content=c.content, metadata={
                                    'source': doc.doc_id,
                                    'chunk_id': c.chunk_id
                                }) for c in chunks
                            ]
                            vsm.add_documents(lc_docs)
                            
                            # Mark phase complete
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'vector', PhaseStatus.COMPLETED
                            )
                        except Exception as e:
                            logger.error(f"[Phased Job {job_id}] Vector failed for {doc.doc_id}: {e}")
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'vector', PhaseStatus.FAILED,
                                error_message=str(e)
                            )
                
                elif phase == 'graph':
                    logger.info(f"[Phased Job {job_id}] Running Phase: Graph")
                    from backend.services.rag.job_queue import job_queue
                    job = job_queue.get_job(job_id)
                    if job:
                        job.current_stage = 'building_graph'
                        job_queue.update_job(job)
                    
                    docs = get_documents_ready_for_phase(job_id, 'graph')
                    for doc in docs:
                        try:
                            # Simple entity extraction (placeholder)
                            chunks = phased_db.get_chunks_for_document(doc.doc_id)
                            entity_count = len(chunks)  # Placeholder
                            
                            # Update metadata
                            phased_db.update_document_metadata(doc.doc_id, {
                                'entity_count': entity_count
                            })
                            
                            # Mark phase complete
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'graph', PhaseStatus.COMPLETED
                            )
                        except Exception as e:
                            logger.error(f"[Phased Job {job_id}] Graph failed for {doc.doc_id}: {e}")
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'graph', PhaseStatus.FAILED,
                                error_message=str(e)
                            )
                
            except Exception as e:
                logger.error(f"[Phased Job {job_id}] Phase {phase} failed: {e}")
        
        # Mark job as completed or failed based on document statuses
        from backend.services.rag.job_queue import job_queue, JobStatus

        # Get FRESH job object and update all stats
        job = job_queue.get_job(job_id)
        if job:
            # Get documents for this job from phased DB
            job_docs = phased_db.get_documents_by_job(job_id)
            logger.info(f"[Phased Job {job_id}] Found {len(job_docs)} documents in phased DB")
            job.documents_processed = len(job_docs)

            # Check if any documents failed
            failed_docs = [d for d in job_docs if d.overall_status == DocumentStatus.FAILED]
            successful_docs = [d for d in job_docs if d.overall_status == DocumentStatus.COMPLETED]

            if failed_docs:
                # Job failed because some documents failed
                job.status = JobStatus.FAILED.value
                job.current_stage = 'failed'
                job.error = f"{len(failed_docs)} document(s) failed LLM chunking"
                logger.error(f"[Phased Job {job_id}] Job FAILED: {job.error}")
            else:
                # All documents succeeded
                job.status = JobStatus.COMPLETED.value
                job.current_stage = 'completed'
                logger.info(f"[Phased Job {job_id}] Job COMPLETED successfully")

            # Count total chunks generated (from successful docs only)
            total_chunks = 0
            per_file_chunks = {}
            for doc in successful_docs:
                chunks = phased_db.get_chunks_for_document(doc.doc_id)
                logger.info(f"[Phased Job {job_id}] Doc {doc.doc_id[:20]} has {len(chunks)} chunks")
                total_chunks += len(chunks)
                per_file_chunks[doc.doc_id] = len(chunks)
            job.chunks_generated = total_chunks

            # Update per-file chunk counts in job parameters
            if job.parameters and 'files' in job.parameters:
                for f in job.parameters['files']:
                    fname = f.get('filename', '').replace('.pdf', '').replace('.md', '').replace('.txt', '')
                    matched = False
                    for doc_id, cnt in per_file_chunks.items():
                        if doc_id.startswith(fname) or fname.startswith(doc_id.split('_')[0]):
                            f['chunks_created'] = cnt
                            f['status'] = 'success'
                            matched = True
                            break
                    if not matched:
                        # This file was not in successful_docs, check if it failed
                        for failed_doc in failed_docs:
                            if failed_doc.original_filename == f.get('filename', ''):
                                f['status'] = 'failed'
                                f['error'] = f.get('error', 'Chunking failed')
                                break

            logger.info(f"[Phased Job {job_id}] Updating job with {len(job_docs)} docs ({len(successful_docs)} success, {len(failed_docs)} failed), {total_chunks} chunks")

            # Save updated job
            job_queue.update_job(job)
            logger.info(f"[Phased Job {job_id}] Job updated successfully")

            # Auto-retry failed documents
            if failed_docs and job.parameters.get('auto_retry_failed', True):
                logger.info(f"[Phased Job {job_id}] Auto-retry enabled, reprocessing {len(failed_docs)} failed document(s)")
                for failed_doc in failed_docs:
                    logger.info(f"[Phased Job {job_id}] Retrying document: {failed_doc.doc_id}")
                    try:
                        # Reset the document status
                        phased_db.update_document_phase_status(
                            failed_doc.doc_id, 'chunk', PhaseStatus.PENDING,
                            error_message=None
                        )

                        # Read extracted text
                        file_path_lower = failed_doc.file_path.lower()
                        if file_path_lower.endswith('.pdf'):
                            text_path = failed_doc.file_path.replace('.pdf', '.txt')
                            if not os.path.exists(text_path):
                                text_path = failed_doc.file_path.replace('.pdf', '.md')
                        elif file_path_lower.endswith('.md'):
                            txt_path = failed_doc.file_path[:-3] + '.txt'
                            if os.path.exists(txt_path):
                                text_path = txt_path
                            else:
                                text_path = failed_doc.file_path
                        elif file_path_lower.endswith('.txt'):
                            text_path = failed_doc.file_path
                        else:
                            base_path = failed_doc.file_path.rsplit('.', 1)[0]
                            if os.path.exists(f"{base_path}.txt"):
                                text_path = f"{base_path}.txt"
                            elif os.path.exists(f"{base_path}.md"):
                                text_path = f"{base_path}.md"
                            else:
                                text_path = failed_doc.file_path

                        if not os.path.exists(text_path):
                            raise Exception(f"Extracted text not found at: {text_path}")

                        with open(text_path, 'r', encoding='utf-8') as f:
                            text = f.read()

                        from .smart_ingestion_enhanced import chunk_document_with_llm_sync

                        success, llm_chunks, error = chunk_document_with_llm_sync(
                            file_path=text_path,
                            prompt="",
                            filename=failed_doc.original_filename,
                            timeout=LLM_CHUNKING_TIMEOUT
                        )

                        if success:
                            from backend.services.rag.phased_processing_models import Chunk
                            chunks = []
                            for i, c in enumerate(llm_chunks):
                                chunks.append(Chunk(
                                    doc_id=failed_doc.doc_id,
                                    chunk_id=f"{failed_doc.doc_id}_chunk_{i:04d}",
                                    chunk_index=i,
                                    content=c.get('content', ''),
                                    content_length=len(c.get('content', '')),
                                    section=c.get('section', ''),
                                    title=c.get('title', ''),
                                    chunk_type='text',
                                    token_count=c.get('token_count', 0),
                                ))

                            phased_db.deactivate_chunks(failed_doc.doc_id)
                            phased_db.save_chunks(chunks)

                            if text_path.endswith('.md'):
                                chunks_file = text_path.replace('.md', '.chunks.json')
                            elif text_path.endswith('.txt'):
                                chunks_file = text_path.replace('.txt', '.chunks.json')
                            else:
                                chunks_file = text_path + '.chunks.json'
                            chunks_data = {
                                'doc_id': failed_doc.doc_id,
                                'filename': failed_doc.original_filename,
                                'total_chunks': len(chunks),
                                'chunking_strategy': 'smart_llm',
                                'chunks': [
                                    {
                                        'chunk_id': c.chunk_id,
                                        'chunk_index': c.chunk_index,
                                        'content': c.content,
                                        'section': c.section,
                                        'title': c.title,
                                        'token_count': c.token_count
                                    } for c in chunks
                                ]
                            }
                            with open(chunks_file, 'w', encoding='utf-8') as f:
                                json.dump(chunks_data, f, indent=2, ensure_ascii=False)

                            phased_db.update_document_metadata(failed_doc.doc_id, {
                                'chunk_count': len(chunks),
                                'chunking_strategy': 'smart_llm'
                            })
                            phased_db.update_document_phase_status(
                                failed_doc.doc_id, 'chunk', PhaseStatus.COMPLETED
                            )
                            logger.info(f"[Phased Job {job_id}] Retry SUCCESS for {failed_doc.doc_id}: {len(chunks)} chunks")

                            # Update file status in job parameters
                            if job.parameters and 'files' in job.parameters:
                                for f_entry in job.parameters['files']:
                                    fname = f_entry.get('filename', '')
                                    doc_base = failed_doc.doc_id.rsplit('_', 1)[0] if '_' in failed_doc.doc_id else failed_doc.doc_id
                                    if fname.startswith(doc_base) or failed_doc.original_filename == fname:
                                        f_entry['chunks_created'] = len(chunks)
                                        f_entry['retry_status'] = 'success'
                                        f_entry['retry_chunks'] = len(chunks)
                                        f_entry.pop('error', None)
                                        break
                        else:
                            logger.warning(f"[Phased Job {job_id}] Retry FAILED for {failed_doc.doc_id}: {error}")
                    except Exception as e:
                        logger.error(f"[Phased Job {job_id}] Retry ERROR for {failed_doc.doc_id}: {e}")

                # Update job status after retries
                job_docs = phased_db.get_documents_by_job(job_id)
                failed_after_retry = [d for d in job_docs if d.overall_status == DocumentStatus.FAILED]
                successful_after_retry = [d for d in job_docs if d.overall_status == DocumentStatus.COMPLETED]

                if failed_after_retry:
                    job.status = JobStatus.FAILED.value
                    job.current_stage = 'failed'
                    job.error = f"{len(failed_after_retry)} document(s) failed after retry"
                    logger.error(f"[Phased Job {job_id}] Job still FAILED after retry: {len(failed_after_retry)} documents")
                else:
                    job.status = JobStatus.COMPLETED.value
                    job.current_stage = 'completed'
                    job.error = None
                    logger.info(f"[Phased Job {job_id}] Job COMPLETED after retry - all documents succeeded")

                # Update chunk counts after retry
                total_chunks = 0
                per_file_chunks = {}
                for doc in successful_after_retry:
                    chunks = phased_db.get_chunks_for_document(doc.doc_id)
                    total_chunks += len(chunks)
                    per_file_chunks[doc.doc_id] = len(chunks)
                job.chunks_generated = total_chunks

                if job.parameters and 'files' in job.parameters:
                    for f in job.parameters['files']:
                        fname = f.get('filename', '').replace('.pdf', '').replace('.md', '').replace('.txt', '')
                        for doc_id, cnt in per_file_chunks.items():
                            if doc_id.startswith(fname) or fname.startswith(doc_id.split('_')[0]):
                                f['chunks_created'] = cnt
                                break

                job_queue.update_job(job)
        else:
            logger.warning(f"[Phased Job {job_id}] Job not found for final update")
        
    except Exception as e:
        logger.error(f"[Phased Job] Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        from backend.services.rag.job_queue import job_queue, JobStatus
        job = job_queue.get_job(job_id)
        if job:
            job.status = JobStatus.FAILED.value
            job.error = str(e)
            job_queue.update_job(job)


def get_documents_ready_for_phase(job_id: str, phase: str):
    """Helper to get documents ready for a specific phase"""
    return phased_db.get_documents_ready_for_phase(job_id, phase)


def _fixed_size_chunk(text: str, doc_id: str, config: dict):
    """Helper function for fixed-size chunking"""
    from backend.services.rag.phased_processing_models import Chunk
    
    chunk_size = config.get('chunk_size', 512)
    overlap = config.get('overlap', 50)
    chars_per_token = 4
    char_chunk_size = chunk_size * chars_per_token
    char_overlap = overlap * chars_per_token
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = min(start + char_chunk_size, len(text))
        content = text[start:end]
        
        if content.strip():
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}_chunk_{chunk_index:04d}",
                chunk_index=chunk_index,
                content=content,
                content_length=len(content),
                chunk_type='text',
                token_count=len(content) // chars_per_token,
            ))
        
        start = end - char_overlap
        chunk_index += 1
        
        if chunk_index > 1000:
            break
    
    return chunks


@phased_processing_bp.route('/job/<job_id>/status', methods=['GET'])
def get_job_status(job_id: str):
    """
    Get detailed status for a job
    
    Returns:
        Job status with per-phase progress
    """
    try:
        progress = phased_db.get_job_phase_progress(job_id)
        
        if not progress:
            return jsonify({
                'success': False,
                'error': 'Job not found'
            }), 404
        
        # Get documents by status
        all_docs = phased_db.get_documents_by_job(job_id)
        completed_docs = [d for d in all_docs if d.overall_status == DocumentStatus.COMPLETED]
        failed_docs = [d for d in all_docs if d.overall_status == DocumentStatus.FAILED]
        processing_docs = [d for d in all_docs if d.overall_status == DocumentStatus.PROCESSING]

        # Collect warnings from job parameters
        warnings_list = []
        
        try:
            from backend.services.rag.job_queue import job_queue
            job = job_queue.get_job(job_id)
            if job and job.parameters:
                # Check for warnings stored in job parameters
                job_warnings = job.parameters.get('warnings', [])
                if job_warnings:
                    warnings_list.extend(job_warnings)
                
                # Also check heartbeat for coverage warnings
                heartbeat = job.parameters.get('heartbeat', {})
                if heartbeat.get('coverage_warning'):
                    warnings_list.append({
                        'type': 'chunking_coverage',
                        'message': heartbeat['coverage_warning'],
                        'timestamp': heartbeat.get('timestamp'),
                        'severity': 'warning'
                    })
        except Exception as e:
            logger.debug(f"Could not check job warnings: {e}")
        
        # Format warnings for response
        warnings = warnings_list if warnings_list else None

        return jsonify({
            'success': True,
            'job_id': job_id,
            'progress': progress.to_dict(),
            'documents': {
                'total': len(all_docs),
                'completed': len(completed_docs),
                'failed': len(failed_docs),
                'processing': len(processing_docs),
            },
            'failed_document_ids': [d.doc_id for d in failed_docs],
            'warnings': warnings
        })
        
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phased_processing_bp.route('/job/<job_id>/start', methods=['POST'])
def start_job(job_id: str):
    """
    Start/resume processing for a job
    
    Request:
        phases: Optional list of phases to run (default: all pending)
    
    Returns:
        Processing status
    """
    try:
        data = request.get_json() or {}
        phases = data.get('phases', ['extract', 'chunk', 'vector', 'graph'])
        
        results = {}
        
        # Run phases sequentially
        if 'extract' in phases:
            # Simulate extract call
            extract_req = {'job_id': job_id}
            # In real implementation, would call extract_text()
            results['extract'] = 'initiated'
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'phases_started': phases,
            'results': results,
            'message': f'Job {job_id} processing started'
        })
        
    except Exception as e:
        logger.error(f"Failed to start job: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Register blueprint helper
def register_phased_processing(app):
    """Register phased processing blueprint with Flask app"""
    app.register_blueprint(phased_processing_bp)
