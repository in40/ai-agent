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

        if not document_ids:
            return jsonify({
                'success': False,
                'error': 'No document IDs provided'
            }), 400

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
                    'extraction_config': extraction_config  # Store extraction config
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
        created_count = 0
        for doc_id in document_ids:
            existing_doc = phased_db.get_document(doc_id)

            if not existing_doc:
                logger.warning(f"Document {doc_id} not found in phased DB")
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
        method: Extraction method (pymupdf, pdfminer, pypdf, tesseract, auto)
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

        loader = DocumentLoader()
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
                                pass

                if method == 'pdfminer':
                    extracted_text = loader._extract_with_pdfminer(doc.file_path)
                    extraction_method_used = 'pdfminer'

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
                
                # Read extracted text
                text_path = doc.file_path.replace('.pdf', '.txt')
                if not os.path.exists(text_path):
                    raise Exception("Extracted text not found")
                
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
        
        # Get documents for this job
        all_docs = phased_db.get_documents_by_job(job_id)
        if not all_docs:
            logger.error(f"[Phased Job {job_id}] No documents found")
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
                    
                    # Get documents ready for extraction
                    docs = get_documents_ready_for_phase(job_id, 'extract')
                    for doc in docs:
                        try:
                            # Extract text
                            from rag_component.document_loader import DocumentLoader
                            loader = DocumentLoader()
                            text = loader._extract_with_pymupdf(doc.file_path)
                            
                            # Save text
                            text_path = doc.file_path.replace('.pdf', '.txt')
                            with open(text_path, 'w', encoding='utf-8') as f:
                                f.write(text)
                            
                            # Update metadata
                            phased_db.update_document_metadata(doc.doc_id, {
                                'extraction_method': 'pymupdf',
                                'extracted_char_count': len(text)
                            })
                            
                            # Mark phase complete
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'extract', PhaseStatus.COMPLETED
                            )
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
                    for doc in docs:
                        try:
                            # Read extracted text
                            text_path = doc.file_path.replace('.pdf', '.txt')
                            if not os.path.exists(text_path):
                                raise Exception("Extracted text not found")

                            with open(text_path, 'r', encoding='utf-8') as f:
                                text = f.read()

                            # Use LLM-based smart chunking with async timeout
                            logger.info(f"[Phased Job {job_id}] Calling LLM for smart chunking...")
                            
                            from .smart_ingestion_enhanced import chunk_document_with_llm_sync
                            
                            # Chunk using LLM with proper timeout (uses config from .env)
                            success, llm_chunks, error = chunk_document_with_llm_sync(
                                file_path=text_path,
                                prompt="",  # Use default prompt
                                filename=doc.original_filename,
                                timeout=LLM_CHUNKING_TIMEOUT  # Pass timeout from .env
                            )
                            
                            if success:
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
                                logger.info(f"[Phased Job {job_id}] LLM generated {len(chunks)} chunks")
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
                            import json
                            chunks_file = text_path.replace('.txt', '.chunks.json')
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

                            # Mark phase complete
                            phased_db.update_document_phase_status(
                                doc.doc_id, 'chunk', PhaseStatus.COMPLETED
                            )
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
            for doc in successful_docs:
                chunks = phased_db.get_chunks_for_document(doc.doc_id)
                logger.info(f"[Phased Job {job_id}] Doc {doc.doc_id[:20]} has {len(chunks)} chunks")
                total_chunks += len(chunks)
            job.chunks_generated = total_chunks

            logger.info(f"[Phased Job {job_id}] Updating job with {len(job_docs)} docs ({len(successful_docs)} success, {len(failed_docs)} failed), {total_chunks} chunks")

            # Save updated job
            job_queue.update_job(job)
            logger.info(f"[Phased Job {job_id}] Job updated successfully")
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
            'failed_document_ids': [d.doc_id for d in failed_docs]
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
