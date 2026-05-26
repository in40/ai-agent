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
import re
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
        chunking_strategy: Optional strategy (default: smart_chunking)
        OR JSON with URLs to download
    
    Returns:
        job_id and list of document IDs
    """
    try:
        # Get chunking strategy from form data
        chunking_strategy = request.form.get('chunking_strategy', 'smart_chunking')
        
        # Generate job ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        user_id = request.headers.get('X-User-ID', 'anonymous')
        
        logger.info(f"[Upload] chunking_strategy={chunking_strategy}")
        
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
        chunking_strategy = data.get('chunking_strategy', 'smart_chunking')

        # Log received config
        logger.info(f"[create_job_from_docstore] Phases received: {phases}")
        logger.info(f"[create_job_from_docstore] Phases type: {type(phases)}")
        logger.info(f"[create_job_from_docstore] Received extraction_config: {json.dumps(extraction_config, indent=2)}")
        logger.info(f"[create_job_from_docstore] chunking_strategy={chunking_strategy}")

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
                    'auto_retry_failed': auto_retry,
                    'enable_regex_entities': data.get('enable_regex_entities', True),
                    'chunking_strategy': chunking_strategy  # Store chunking strategy
                },
                ingestion_mode='docstore',
                processing_mode='vector_db',
                chunking_strategy=chunking_strategy
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
                
                elif strategy == 'recursive_semantic':
                    # NEW: Hybrid recursive semantic chunking
                    from .smart_ingestion_enhanced import hybrid_chunk_document, validate_and_fix_chunks
                    
                    logger.info(f"[Job {job_id}] Using recursive semantic chunking")
                    raw_chunks = hybrid_chunk_document(text_content, doc.original_filename or doc.doc_id)
                    
                    # Post-process to fix size issues
                    chunks_list = validate_and_fix_chunks(raw_chunks)
                    
                    # Convert to Chunk model format
                    from backend.services.rag.phased_processing_models import Chunk
                    chunks = []
                    for c in chunks_list:
                        chunks.append(Chunk(
                            doc_id=doc.doc_id,
                            chunk_id=c.get('chunk_id', f"{doc.doc_id}_chunk_{c.get('chunk_index', 0)}"),
                            chunk_index=c.get('chunk_index', 0),
                            content=c.get('content', ''),
                            content_length=c.get('content_length', len(c.get('content', ''))),
                            section=c.get('section', ''),
                            title=c.get('title', ''),
                            chunk_type=c.get('chunk_type', 'text'),
                            token_count=c.get('token_count', 0),
                        ))
                    chunking_strategy = 'recursive_semantic'
                
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
                
                # Get chunks for this document (only active chunks)
                chunks = phased_db.get_chunks_for_document(doc.doc_id)
                
                # If chunks not found, check for inactive chunks (may need re-activation)
                if not chunks:
                    # Check if there are inactive chunks for this doc
                    with db_manager.engine.connect() as conn:
                        inactive_result = conn.execute(text("""
                            SELECT chunk_id FROM chunks_cache 
                            WHERE doc_id = :doc_id AND version = :version
                        """), {'doc_id': doc.doc_id, 'version': 'v1'})
                        inactive_chunks = inactive_result.fetchall()
                    
                    if inactive_chunks:
                        # Re-activate the chunks
                        logger.info(f"[Vector Indexing {job_id}] Found {len(inactive_chunks)} inactive chunks for {doc.doc_id}, re-activating...")
                        phased_db.activate_chunks(doc.doc_id, 'v1')
                        chunks = phased_db.get_chunks_for_document(doc.doc_id)
                        logger.info(f"[Vector Indexing {job_id}] Re-activated {len(chunks)} chunks for {doc.doc_id}")
                    
                    # If still no chunks, try to load from Document Store
                    if not chunks:
                        try:
                            chunks = _load_chunks_from_docstore(doc.doc_id)
                            if chunks:
                                logger.info(f"[Vector Indexing {job_id}] Loaded {len(chunks)} chunks from Document Store for {doc.doc_id}")
                                # Save loaded chunks to phased DB for future use
                                phased_db.save_chunks(chunks)
                        except Exception as e:
                            logger.warning(f"[Vector Indexing {job_id}] Failed to load chunks from Document Store: {e}")
                
                if not chunks:
                    raise Exception("No chunks found for document")
                
                # FINAL SAFETY NET: force-split any chunk still exceeding 5000 chars
                from .smart_ingestion_enhanced import force_split_oversized
                chunk_dicts = [{
                    'content': c.content, 'chunk_id': c.chunk_id, 'chunk_index': c.chunk_index,
                    'section': c.section or '', 'title': c.title or '', 'chunk_type': c.chunk_type,
                    'token_count': c.token_count or 0,
                } for c in chunks]
                fixed_dicts = force_split_oversized(chunk_dicts, hard_limit=5000)
                if len(fixed_dicts) != len(chunk_dicts):
                    logger.info(f"[Vector Indexing {job_id}] Force-split {len(chunk_dicts)} chunks into {len(fixed_dicts)}")
                    from backend.services.rag.phased_processing_models import Chunk
                    chunks = []
                    for i, cd in enumerate(fixed_dicts):
                        chunks.append(Chunk(
                            doc_id=doc.doc_id,
                            chunk_id=cd.get('chunk_id', f"{doc.doc_id}_chunk_{i:04d}"),
                            chunk_index=i,
                            content=cd.get('content', ''),
                            content_length=len(cd.get('content', '')),
                            section=cd.get('section', ''),
                            title=cd.get('title', ''),
                            chunk_type=cd.get('chunk_type', 'text'),
                            token_count=cd.get('token_count', 0),
                        ))
                
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
        enable_regex = data.get('enable_regex_entities', True)
        
        if not job_id:
            return jsonify({
                'success': False,
                'error': 'job_id is required'
            }), 400
        
        # If not passed in request, try loading from job parameters
        if 'enable_regex_entities' not in data:
            try:
                from backend.services.rag.job_queue import job_queue
                job_obj = job_queue.get_job(job_id)
                if job_obj and job_obj.parameters:
                    enable_regex = job_obj.parameters.get('enable_regex_entities', True)
            except Exception:
                pass
        
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
                
                # Extract entities from chunks using LLM-enhanced hybrid extraction
                # This enables automatic pattern discovery for abbreviations, organizations, etc.
                try:
                    from backend.services.rag.neo4j_integration import Neo4jIntegration
                    from models.response_generator import ResponseGenerator
                    
                    # Set job ID for LLM response logging
                    os.environ['CURRENT_JOB_ID'] = job_id
                    
                    # Initialize LLM for entity extraction
                    response_gen = ResponseGenerator()
                    llm = response_gen._get_llm_instance()
                    
                    # Initialize Neo4j with LLM support
                    neo4j = Neo4jIntegration(llm=llm)
                    if not neo4j.connected:
                        if not neo4j.connect():
                            logger.warning(f"Neo4j connection failed: {neo4j.last_error}. Using fallback extraction.")
                            neo4j = None
                    
                    if neo4j and neo4j.connected:
                        # Prepare chunks for Neo4j graph creation
                        # Note: Chunks from DB don't have 'metadata' field, so we pass chunk_id directly
                        chunk_data = []
                        for chunk in chunks:
                            chunk_data.append({
                                'content': chunk.content,
                                'chunk_id': chunk.chunk_id,  # Pass chunk_id at top level
                                'metadata': {
                                    'chunk_id': chunk.chunk_id,
                                    'chunk_uuid': chunk.chunk_id  # Also in metadata for compatibility
                                }
                            })
                        
                        # Use LLM-enhanced extraction with pattern discovery
                        logger.info(f"Running LLM entity extraction for document {doc.doc_id}")
                        graph_stats = neo4j.create_knowledge_graph(
                            chunks=chunk_data,
                            use_llm_extraction=True,
                            use_regex_entities=enable_regex
                        )
                        
                        doc_entities = graph_stats['entities']
                        doc_relationships = graph_stats['chunk_refs']
                        
                        # Accumulate totals across all documents
                        total_entities += doc_entities
                        total_relationships += doc_relationships
                        
                        logger.info(f"Extracted {doc_entities} entities and {doc_relationships} chunk references (total: {total_entities} entities)")
                        neo4j.close()
                    else:
                        # Fallback to simple regex extraction if Neo4j/LLM unavailable
                        logger.warning("Using fallback regex extraction (Neo4j/LLM unavailable)")
                        total_entities = 0
                        total_relationships = 0
                        
                        for chunk in chunks:
                            import re
                            gost_pattern = r'ГОСТ\s*[Рр]?\s*(\d+(?:\.\d+)?-\d{4})'
                            matches = re.findall(gost_pattern, chunk.content)
                            
                            for match in matches:
                                entity_name = f"ГОСТ {match}"
                                if not any(e.get('name') == entity_name for e in [{'name': 'test'}]):  # Simplified check
                                    total_entities += 1
                except Exception as e:
                    logger.error(f"LLM entity extraction failed: {e}. Using fallback.")
                    total_entities = 0
                    total_relationships = 0
                
                # Update document metadata
                phased_db.update_document_metadata(doc.doc_id, {
                    'entity_count': total_entities,
                    'relationship_count': total_relationships,
                })
                
                # Mark phase as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                phased_db.update_document_phase_status(
                    doc.doc_id, 'graph', PhaseStatus.COMPLETED,
                    metadata={
                        'entities_extracted': total_entities,
                        'relationships_created': total_relationships,
                        'extraction_method': 'LLM+hybrid' if neo4j and neo4j.connected else 'regex_fallback'
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
                    items_processed=total_entities,
                    metadata={
                        'entities': total_entities,
                        'relationships': total_relationships,
                        'extraction_method': 'LLM+hybrid' if neo4j and neo4j.connected else 'regex_fallback'
                    }
                ))
                
                processed_count += 1
                
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
        
        # Debug logging to understand what phases were received
        logger.info(f"[Phased Job {job_id}] Starting background processing")
        logger.info(f"[Phased Job {job_id}] Job parameters keys: {list(job.parameters.keys())}")
        phases_raw = job.parameters.get('phases')
        logger.info(f"[Phased Job {job_id}] Phases raw value from parameters: {phases_raw}")
        if phases_raw is None:
            logger.info(f"[Phased Job {job_id}] Phases NOT FOUND in parameters - using default: {phases}")
        else:
            logger.info(f"[Phased Job {job_id}] Phases to process: {phases}")
        
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

                            # Get chunking strategy from job parameters
                            chunking_strategy = job.parameters.get('chunking_strategy', 'smart_chunking')
                            logger.info(f"[Phased Job {job_id}] Using chunking_strategy: {chunking_strategy}")

                            chunks = []
                            
                            if chunking_strategy == 'recursive_semantic':
                                # Use hybrid recursive semantic chunking (NO LLM)
                                from .smart_ingestion_enhanced import hybrid_chunk_document, validate_and_fix_chunks
                                from backend.services.rag.phased_processing_models import Chunk
                                
                                logger.info(f"[Phased Job {job_id}] Using recursive semantic chunking for {doc.original_filename}")
                                raw_chunks = hybrid_chunk_document(text, doc.original_filename or doc.doc_id)
                                chunks_list = validate_and_fix_chunks(raw_chunks)
                                
                                # Convert to Chunk model format
                                for c in chunks_list:
                                    # Truncate section/title to fit DB column limits
                                    section = (c.get('section', '') or '')[:500]
                                    title = (c.get('title', '') or '')[:500]
                                    chunks.append(Chunk(
                                        doc_id=doc.doc_id,
                                        chunk_id=c.get('chunk_id', f"{doc.doc_id}_chunk_{c.get('chunk_index', 0)}"),
                                        chunk_index=c.get('chunk_index', 0),
                                        content=c.get('content', ''),
                                        content_length=c.get('content_length', len(c.get('content', ''))),
                                        section=section,
                                        title=title,
                                        chunk_type=c.get('chunk_type', 'text'),
                                        token_count=c.get('token_count', 0),
                                    ))
                                
                                logger.info(f"[Phased Job {job_id}] Recursive semantic generated {len(chunks)} chunks")
                                success = True  # Define success for recursive_semantic branch
                                final_warning = None  # Define final_warning for recursive_semantic branch
                                chunking_metadata = {'cleaning_method': None, 'warning': None}
                                
                                # Deactivate old chunks before saving new ones
                                phased_db.deactivate_chunks(doc.doc_id)
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
                                'chunking_strategy': chunking_strategy,
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
                                'chunking_strategy': chunking_strategy
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
                    logger.info(f"[Phased Job {job_id}] *** DEBUG: Starting graph phase processing ***")
                    from backend.services.rag.job_queue import job_queue
                    from backend.services.rag.neo4j_integration import get_neo4j_connection
                    
                    job = job_queue.get_job(job_id)
                    if job:
                        job.current_stage = 'building_graph'
                        job_queue.update_job(job)
                    
                    docs = get_documents_ready_for_phase(job_id, 'graph')
                    logger.info(f"[Phased Job {job_id}] *** DEBUG: Found {len(docs)} documents ready for graph phase ***")
                    for doc in docs:
                        try:
                            # Get chunks from phased DB
                            chunks = phased_db.get_chunks_for_document(doc.doc_id)
                            
                            if not chunks:
                                raise Exception("No chunks found for graph creation")
                            
                            # Convert to format expected by Neo4jIntegration
                            chunk_data = []
                            for c in chunks:
                                # Use chunk_id directly as the unique identifier
                                chunk_uuid = c.chunk_id
                                
                                chunk_data.append({
                                    'content': c.content,
                                    'chunk_uuid': chunk_uuid,  # Use chunk_id as unique identifier
                                    'metadata': {
                                        'source': doc.doc_id,
                                        'chunk_id': c.chunk_id,
                                        'chunk_uuid': chunk_uuid
                                    }
                                })
                            
                            # Create knowledge graph in Neo4j with LLM entity extraction
                            from models.response_generator import ResponseGenerator
                            
                            # Set job ID for LLM response logging
                            os.environ['CURRENT_JOB_ID'] = job_id
                            
                            # Initialize LLM for entity extraction
                            response_gen = ResponseGenerator()
                            llm = response_gen._get_llm_instance()
                            
                            # Use Neo4jIntegration with LLM support
                            from backend.services.rag.neo4j_integration import Neo4jIntegration
                            neo4j = Neo4jIntegration(llm=llm)
                            
                            if not neo4j.connected:
                                if not neo4j.connect():
                                    logger.warning(f"[Phased Job {job_id}] Neo4j connection failed: {neo4j.last_error}. Using fallback.")
                                    phased_db.update_document_phase_status(
                                        doc.doc_id, 'graph', PhaseStatus.SKIPPED,
                                        error_message="Neo4j connection failed"
                                    )
                                    continue
                            
                            logger.info(f"[Phased Job {job_id}] Running LLM entity extraction with {len(chunk_data)} chunks")
                            enable_regex = job.parameters.get('enable_regex_entities', True) if job.parameters else True
                            graph_stats = neo4j.create_knowledge_graph(chunk_data, use_llm_extraction=True, use_regex_entities=enable_regex)
                            
                            # Check if LLM extraction succeeded or fell back to regex
                            extraction_method = 'LLM'
                            if neo4j.llm_extraction_failed:
                                logger.warning(f"[Phased Job {job_id}] ⚠️ LLM extraction failed - using regex fallback")
                                extraction_method = 'regex_fallback'
                            
                            neo4j.close()
                            
                            logger.info(f"[Phased Job {job_id}] Graph created: {graph_stats['entities']} entities, {graph_stats['chunk_refs']} chunk references (method: {extraction_method})")
                            
                            # Update metadata with extraction method
                            phased_db.update_document_metadata(doc.doc_id, {
                                'entity_count': graph_stats['entities'],
                                'chunk_references': graph_stats['chunk_refs'],
                                'extraction_method': extraction_method,
                                'llm_extraction_success': extraction_method == 'LLM'
                            })
                            
                            # Mark phase complete with extraction method info
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'graph', PhaseStatus.COMPLETED,
                                metadata={
                                    'entities_created': graph_stats['entities'],
                                    'chunk_refs_created': graph_stats['chunk_refs'],
                                    'extraction_method': extraction_method,
                                    'llm_extraction_success': extraction_method == 'LLM',
                                    'status_message': f"Extracted {graph_stats['entities']} entities using {extraction_method}" if extraction_method == 'LLM' else f"⚠️ LLM failed, used regex fallback. Extracted {graph_stats['entities']} entities."
                                }
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


def _load_chunks_from_docstore(doc_id: str) -> Optional[List['Chunk']]:
    """
    Load chunks from Document Store .chunks.json file
    
    Args:
        doc_id: Document ID to load chunks for
        
    Returns:
        List of Chunk objects or None if not found
    """
    try:
        from backend.services.rag.phased_processing_models import Chunk
        import json
        
        logger.info(f"[Load Chunks] Loading chunks for doc_id={doc_id}")
        
        # Document Store base directory
        docstore_base = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
        
        # Look for .chunks.json file
        chunks_file = os.path.join(docstore_base, f"documents/{doc_id}.chunks.json")
        
        if not os.path.exists(chunks_file):
            logger.info(f"[Load Chunks] File not found at {chunks_file}, trying glob pattern")
            # Try nested structure
            import glob as glob_mod
            matches = glob_mod.glob(f"{docstore_base}/**/{doc_id}.chunks.json", recursive=True)
            if matches:
                chunks_file = matches[0]
                logger.info(f"[Load Chunks] Found chunks at nested path: {chunks_file}")
            else:
                logger.info(f"[Load Chunks] No chunks file found for doc_id={doc_id}")
                return None
        
        logger.info(f"[Load Chunks] Loading chunks from {chunks_file}")
        
        with open(chunks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different chunk formats
        # Format 1: {'chunks': [...]} (smart chunking output)
        if 'chunks' in data:
            chunks_data = data['chunks']
        # Format 2: Direct list of chunks
        elif isinstance(data, list):
            chunks_data = data
        else:
            logger.warning(f"Unknown chunks format in {chunks_file}")
            return None
        
        chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = Chunk(
                doc_id=doc_id,
                chunk_id=chunk_data.get('chunk_id', f"{doc_id}_chunk_{i:04d}"),
                chunk_index=i,
                content=chunk_data.get('content', ''),
                content_length=len(chunk_data.get('content', '')),
                section=(chunk_data.get('section', '') or '')[:500],
                title=(chunk_data.get('title', '') or '')[:500],
                chunk_type=chunk_data.get('chunk_type', 'text'),
                token_count=chunk_data.get('token_count'),
                start_char=chunk_data.get('start_char'),
                end_char=chunk_data.get('end_char'),
                contains_formula=chunk_data.get('contains_formula', False),
                contains_table=chunk_data.get('contains_table', False),
                entity_hints=chunk_data.get('entity_hints', []),
                version='v1',
                version_label=None,
                is_active=True,
            )
            chunks.append(chunk)
        
        # Apply hard safety split on any oversized chunk loaded from disk
        from .smart_ingestion_enhanced import force_split_oversized
        chunk_dicts = [c.to_dict() for c in chunks]
        fixed_dicts = force_split_oversized(chunk_dicts, hard_limit=5000)
        if len(fixed_dicts) != len(chunk_dicts):
            logger.info(f"Force-split {len(chunk_dicts)} loaded chunks into {len(fixed_dicts)} (max_size safety)")
            # Recreate Chunk objects from fixed dicts
            from backend.services.rag.phased_processing_models import Chunk
            new_chunks = []
            for i, cd in enumerate(fixed_dicts):
                new_chunks.append(Chunk(
                    doc_id=doc_id,
                    chunk_id=cd.get('chunk_id', f"{doc_id}_chunk_{i:04d}"),
                    chunk_index=i,
                    content=cd.get('content', ''),
                    content_length=len(cd.get('content', '')),
                    section=cd.get('section', ''),
                    title=cd.get('title', ''),
                    chunk_type=cd.get('chunk_type', 'text'),
                ))
            chunks = new_chunks
        
        logger.info(f"Loaded {len(chunks)} chunks from Document Store for {doc_id}")
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to load chunks from Document Store: {e}")
        return None


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


@phased_processing_bp.route('/job/<job_id>/documents', methods=['GET'])
def get_job_documents_status(job_id: str):
    """
    Get per-document phase progress for a job.
    
    Returns:
        List of documents with per-phase status, chunk counts, and entity counts
    """
    try:
        from backend.services.rag.phased_processing_models import DocumentStatus, PhaseStatus
        from backend.services.rag.phased_processing_db import phased_db
        
        all_docs = phased_db.get_documents_by_job(job_id)
        
        if not all_docs:
            return jsonify({
                'success': True,
                'documents': [],
                'total': 0
            })
        
        doc_list = []
        for doc in all_docs:
            doc_list.append({
                'doc_id': doc.doc_id,
                'filename': doc.display_name or doc.original_filename,
                'overall_status': doc.overall_status.value if doc.overall_status else 'pending',
                'phases': {
                    'upload': doc.phase_upload.value if doc.phase_upload else 'pending',
                    'extract': doc.phase_extract.value if doc.phase_extract else 'pending',
                    'chunk': doc.phase_chunk.value if doc.phase_chunk else 'pending',
                    'vector': doc.phase_vector.value if doc.phase_vector else 'pending',
                    'graph': doc.phase_graph.value if doc.phase_graph else 'pending',
                },
                'current_phase': doc.current_phase or 'upload',
                'chunk_count': doc.chunk_count or 0,
                'vector_chunk_count': doc.vector_chunk_count or 0,
                'entity_count': doc.entity_count or 0,
                'relationship_count': doc.relationship_count or 0,
                'file_size': doc.file_size,
                'extracted_char_count': doc.extracted_char_count,
                'error': doc.last_error if doc.overall_status == DocumentStatus.FAILED else None,
            })
        
        completed = sum(1 for d in all_docs if d.overall_status == DocumentStatus.COMPLETED)
        failed = sum(1 for d in all_docs if d.overall_status == DocumentStatus.FAILED)
        processing = sum(1 for d in all_docs if d.overall_status == DocumentStatus.PROCESSING)
        
        return jsonify({
            'success': True,
            'documents': doc_list,
            'total': len(all_docs),
            'completed': completed,
            'failed': failed,
            'processing': processing
        })
        
    except Exception as e:
        logger.error(f"Failed to get job documents: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@phased_processing_bp.route('/document/<doc_id>/pipeline', methods=['GET'])
def get_document_pipeline(doc_id: str):
    """
    Get full pipeline status for a document.
    
    Returns extraction, chunks (with vector DB status), entities, and graph status.
    """
    try:
        from backend.services.rag.phased_processing_db import phased_db
        from backend.services.rag.phased_processing_models import DocumentProcessing, DocumentStatus
        
        # 1. Get document from phased DB
        doc = phased_db.get_document(doc_id)
        if not doc:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # 2. Get chunks
        chunks = []
        chunk_rows = phased_db.get_chunks_for_document(doc_id)
        for c in chunk_rows:
            chunks.append({
                'chunk_id': c.chunk_id,
                'index': c.chunk_index,
                'size': c.content_length or len(c.content or ''),
                'preview': (c.content or '')[:120].replace('\n', ' '),
                'section': c.section,
                'title': c.title,
                'token_count': c.token_count,
                'contains_formula': c.contains_formula,
                'contains_table': c.contains_table,
                'entity_hints': c.entity_hints,
                'vector_id': c.vector_id,
            })
        
        # Chunk stats
        chunk_sizes = [c['size'] for c in chunks if c['size'] > 0]
        chunk_stats = {
            'total': len(chunks),
            'min_size': min(chunk_sizes) if chunk_sizes else 0,
            'max_size': max(chunk_sizes) if chunk_sizes else 0,
            'avg_size': round(sum(chunk_sizes) / len(chunk_sizes)) if chunk_sizes else 0,
        }
        
        # 3. Check vector DB for each chunk
        vector_count = 0
        try:
            from rag_component.vector_store_manager import VectorStoreManager
            vsm = VectorStoreManager()
            if hasattr(vsm, 'collection_name'):
                from qdrant_client import QdrantClient
                qdrant_url = os.getenv("RAG_QDRANT_URL", "http://localhost:6333")
                qdrant_api_key = os.getenv("RAG_QDRANT_API_KEY", "")
                if qdrant_api_key:
                    qclient = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, prefer_grpc=False)
                else:
                    qclient = QdrantClient(url=qdrant_url, prefer_grpc=False)
                collection = vsm.collection_name
                
                # Check which chunk IDs exist in vector DB
                chunk_ids = [c['chunk_id'] for c in chunks if c['chunk_id']]
                if chunk_ids:
                    from qdrant_client.http.models import Filter, FilterSelector, HasIdCondition
                    from qdrant_client.http.models import PointIdsList
                    from qdrant_client import models
                    
                    # Qdrant scroll to find points matching these chunk IDs
                    # Use scroll with ID filtering
                    existing_ids = set()
                    scroll_limit = 100
                    for i in range(0, len(chunk_ids), scroll_limit):
                        batch = chunk_ids[i:i+scroll_limit]
                        try:
                            scroll_result = qclient.scroll(
                                collection_name=collection,
                                limit=len(batch),
                                with_payload=False,
                                with_vectors=False,
                            )
                            for point in scroll_result[0]:
                                existing_ids.add(str(point.id))
                        except Exception:
                            pass
                    
                    for c in chunks:
                        cid = c['chunk_id']
                        # Check both chunk_id and index-based matching
                        c['in_vector_db'] = cid in existing_ids or c['vector_id'] is not None
                        if c['in_vector_db']:
                            vector_count += 1
                else:
                    for c in chunks:
                        c['in_vector_db'] = c['vector_id'] is not None
                        if c['in_vector_db']:
                            vector_count += 1
        except Exception as e:
            logger.warning(f"Could not check vector DB for {doc_id}: {e}")
            for c in chunks:
                c['in_vector_db'] = c['vector_id'] is not None
                if c['in_vector_db']:
                    vector_count += 1
        
        # 4. Check file system for .md / .txt
        md_exists = False
        md_size = 0
        txt_exists = False
        txt_size = 0
        ing_dir = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
        try:
            import glob
            # Search for doc_id with various patterns
            for root, dirs, files in os.walk(ing_dir):
                for f in files:
                    name, ext = os.path.splitext(f)
                    if doc_id.startswith(name) or name.startswith(doc_id.split('_')[0]):
                        fpath = os.path.join(root, f)
                        fsize = os.path.getsize(fpath)
                        if ext.lower() == '.md':
                            md_exists = True
                            md_size = fsize
                        elif ext.lower() == '.txt':
                            txt_exists = True
                            txt_size = fsize
        except Exception as e:
            logger.warning(f"Could not check file system for {doc_id}: {e}")
        
        # Extract document title from .md or .txt content
        document_title = None
        try:
            ing_dir = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"
            for root, dirs, files in os.walk(ing_dir):
                for f in files:
                    name, ext = os.path.splitext(f)
                    if not (doc_id.startswith(name) or name.startswith(doc_id.split('_')[0])):
                        continue
                    if ext.lower() not in ('.md', '.txt'):
                        continue
                    fpath = os.path.join(root, f)
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        first_lines = fh.readlines()[:30]
                    
                    # Helper to clean markdown formatting from a candidate title
                    def clean_title(s):
                        s = s.strip().rstrip('#*-').strip()
                        s = re.sub(r'\*\*', '', s)  # remove **bold**
                        s = re.sub(r'__(.+?)__', r'\1', s)  # remove __underline__
                        s = s.strip()
                        return s
                    
                    # Strategy 1: Find first markdown heading (# or ##)
                    for line in first_lines:
                        h_match = re.match(r'^#{1,3}\s+(.+)$', line.strip())
                        if h_match:
                            candidate = clean_title(h_match.group(1))
                            if candidate and len(candidate) > 5:
                                document_title = candidate
                                break
                    if document_title:
                        break
                    
                    # Strategy 2: Find bold text (** ... **) on its own line (common in GOST docs)
                    for line in first_lines:
                        stripped = line.strip()
                        b_match = re.match(r'^\*\*(.+?)\*\*$', stripped)
                        if b_match:
                            candidate = clean_title(b_match.group(1))
                            if candidate and len(candidate) > 10:
                                document_title = candidate
                                break
                    if document_title:
                        break
                    
                    # Strategy 3: Concatenate consecutive bold lines (multi-line titles)
                    bold_lines = []
                    for line in first_lines:
                        stripped = line.strip()
                        if re.match(r'^\*\*.+?\*\*$', stripped):
                            bold_lines.append(re.sub(r'\*\*', '', stripped))
                        elif bold_lines and stripped == '':
                            continue  # skip blank lines between bold lines
                        elif bold_lines:
                            break  # non-bold, non-blank line -> stop
                    if bold_lines:
                        combined = ' '.join(bold_lines)
                        if len(combined) > 10:
                            document_title = combined
                            break
                    
                    # Strategy 4: First meaningful text line (fallback)
                    for line in first_lines:
                        stripped = line.strip()
                        if not stripped or stripped.startswith('<!--') or stripped.startswith('<'):
                            continue
                        if len(stripped) > 10 and re.search(r'[А-Яа-яA-Za-z]{4,}', stripped):
                            candidate = clean_title(stripped)
                            if candidate and len(candidate) > 5:
                                document_title = candidate
                                break
                    if document_title:
                        break
            if document_title:
                document_title = document_title.strip().rstrip('#*-.').strip()
        except Exception as e:
            logger.warning(f"Could not extract title from files for {doc_id}: {e}")
        
        # 5. Get entities from Neo4j
        entities = []
        graph_entity_count = 0
        try:
            from backend.services.rag.neo4j_integration import Neo4jIntegration
            neo4j = Neo4jIntegration()
            if neo4j.connect():
                graph_data = neo4j.get_document_graph(doc_id)
                if graph_data and 'entities' in graph_data:
                    for ent in graph_data['entities']:
                        ent_name = ent.get('name', '')
                        ent_type = ent.get('type', '')
                        # Get relationship count for each entity
                        rel_count = 0
                        try:
                            rels = neo4j.get_entity_relationships(ent_name)
                            rel_count = len(rels)
                        except Exception:
                            pass
                        entities.append({
                            'name': ent_name,
                            'type': ent_type,
                            'relationship_count': rel_count,
                        })
                    graph_entity_count = len(entities)
                neo4j.close()
        except Exception as e:
            logger.warning(f"Could not check Neo4j for {doc_id}: {e}")
        
        # 6. Relationships total from doc
        relationship_total = sum(e['relationship_count'] for e in entities)
        
        return jsonify({
            'success': True,
            'document': {
                'doc_id': doc.doc_id,
                'filename': doc.display_name or doc.original_filename,
                'title': document_title or '',
                'file_size': doc.file_size,
                'content_type': doc.content_type,
                'overall_status': doc.overall_status.value if doc.overall_status else 'unknown',
                'phases': {
                    'upload': doc.phase_upload.value if doc.phase_upload else 'pending',
                    'extract': doc.phase_extract.value if doc.phase_extract else 'pending',
                    'chunk': doc.phase_chunk.value if doc.phase_chunk else 'pending',
                    'vector': doc.phase_vector.value if doc.phase_vector else 'pending',
                    'graph': doc.phase_graph.value if doc.phase_graph else 'pending',
                },
            },
            'extraction': {
                'method': doc.extraction_method,
                'page_count': doc.page_count,
                'extracted_char_count': doc.extracted_char_count,
                'md_exists': md_exists,
                'md_size': md_size,
                'txt_exists': txt_exists,
                'txt_size': txt_size,
            },
            'chunks': {
                'stats': chunk_stats,
                'in_vector_db': vector_count,
                'list': chunks[:200],  # Limit to 200 chunks
            },
            'graph': {
                'entity_count': graph_entity_count,
                'relationship_total': relationship_total,
                'entities': entities,
            },
        })
        
    except Exception as e:
        logger.error(f"Failed to get document pipeline: {e}")
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
