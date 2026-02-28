"""
RAG Service for AI Agent System
Handles document processing and retrieval
"""
import os
import re
import json
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import time

# Import RAG components
from rag_component.main import RAGOrchestrator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from models.response_generator import ResponseGenerator

# Import security components
from backend.security import require_permission, validate_input, Permission

# Import job queue blueprint
from backend.services.rag.job_queue import jobs_bp

# Import smart ingestion endpoints (need to import after app is created to avoid circular imports)
# We'll register them directly by importing the functions

# Import robust JSON parsing utilities
from .json_utils import parse_json_robust, validate_chunking_result

# Initialize Flask app
app = Flask(__name__)
# Set maximum content length to 500MB to allow for multiple file uploads
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register job queue blueprint
app.register_blueprint(jobs_bp)

def secure_filename(filename: str) -> str:
    """
    Secure a filename by removing potentially dangerous characters and sequences.
    Preserves Unicode characters like Cyrillic letters.
    """
    if filename is None:
        return ''

    # Normalize the path to remove any Windows-style separators
    filename = filename.replace('\\', '/')

    # Get the basename to prevent directory traversal
    filename = os.path.basename(filename)

    # Remove leading dots and spaces
    filename = filename.lstrip('. ')

    # Replace any sequence of invalid characters with a single underscore
    # Allow Unicode word characters (letters, digits, underscores), dots, dashes, and spaces
    filename = re.sub(r'[^\w\-.]', '_', filename, flags=re.UNICODE)

    # Handle cases where the filename might be empty after sanitization
    if not filename:
        filename = "unnamed_file"

    # Prevent hidden files by ensuring the name doesn't start with a dot
    if filename.startswith('.'):
        filename = f"unnamed{filename}"

    return filename


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'rag',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/query', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_query(current_user_id):
    """Endpoint for RAG queries"""
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'query': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 1000,
                'sanitize': True
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        query = data.get('query')
        
        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )
        
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # Perform the query
        result = rag_orchestrator.query(query)
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        return jsonify({'error': f'RAG query failed: {str(e)}'}), 500


@app.route('/ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_ingest(current_user_id):
    """Endpoint for ingesting documents into RAG"""
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'file_paths': {
                'type': list,
                'required': True,
                'min_length': 1,
                'max_length': 50  # Max 50 files at once
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        file_paths = data.get('file_paths')
        
        # Additional validation for file paths
        for path in file_paths:
            if not isinstance(path, str) or len(path) == 0:
                return jsonify({'error': 'Each file path must be a non-empty string'}), 400
        
        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )
        
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # Ingest documents
        success = rag_orchestrator.ingest_documents(file_paths)

        if success:
            return jsonify({'message': 'Documents ingested successfully'}), 200
        else:
            return jsonify({'error': 'Document ingestion failed - check file paths and permissions'}), 400
    except Exception as e:
        logger.error(f"RAG ingestion error: {str(e)}")
        return jsonify({'error': f'RAG ingestion failed: {str(e)}'}), 500


@app.route('/retrieve', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_retrieve(current_user_id):
    """Endpoint for retrieving documents from RAG"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'query': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 1000,
                'sanitize': True
            },
            'top_k': {
                'type': int,
                'required': False,
                'min_value': 1,
                'max_value': 100
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400

        query = data.get('query')
        top_k = data.get('top_k', 5)  # Default to 5 results

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Retrieve documents
        documents = rag_orchestrator.retrieve_documents(query, top_k=top_k)

        # Enhance documents with download links if they have file IDs
        enhanced_documents = []
        for doc in documents:
            enhanced_doc = doc.copy()

            # Add download link if file ID is available
            if 'file_id' in doc.get('metadata', {}):
                file_id = doc['metadata']['file_id']
                filename = doc['metadata'].get('source', 'unknown_file')
                # Sanitize the filename to match the stored filename
                safe_filename = secure_filename(filename)
                # Construct the download URL using relative path
                download_url = f"/download/{file_id}/{safe_filename}"
                enhanced_doc['download_url'] = download_url

            enhanced_documents.append(enhanced_doc)

        return jsonify({'documents': enhanced_documents}), 200
    except Exception as e:
        logger.error(f"RAG retrieval error: {str(e)}")
        return jsonify({'error': f'RAG retrieval failed: {str(e)}'}), 500


@app.route('/lookup', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_lookup(current_user_id):
    """Endpoint for looking up documents in RAG"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'query': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 1000,
                'sanitize': True
            },
            'top_k': {
                'type': int,
                'required': False,
                'min_value': 1,
                'max_value': 100
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400

        query = data.get('query')
        top_k = data.get('top_k', 5)  # Default to 5 results

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Retrieve documents
        documents = rag_orchestrator.retrieve_documents(query, top_k=top_k)

        return jsonify({'documents': documents}), 200
    except Exception as e:
        logger.error(f"RAG lookup error: {str(e)}")
        return jsonify({'error': f'RAG lookup failed: {str(e)}'}), 500


@app.route('/upload', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_upload(current_user_id):
    """Endpoint for uploading documents to RAG"""
    try:
        import re
        import os
        import tempfile
        import uuid

        # Check if files were included in the request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        print(f"DEBUG: Backend received {len(files)} files in upload")
        for i, file in enumerate(files):
            if file and file.filename:
                print(f"DEBUG: Backend received file {i+1}: {file.filename}")

        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        # Validate file count
        if len(files) > 10:  # Maximum 10 files at once
            return jsonify({'error': 'Maximum 10 files allowed per upload'}), 400

        # Temporary directory to store uploaded files
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        original_filenames = []  # Store original filenames

        for file in files:
            if file.filename == '':
                continue

            # Validate file type
            # Store the original filename before sanitizing for filesystem operations
            original_filename_unsanitized = file.filename
            original_filenames.append(original_filename_unsanitized)  # Store original unsanitized filename
            secure_filename_for_fs = secure_filename(file.filename)  # Sanitize for filesystem operations
            file_ext = Path(secure_filename_for_fs).suffix.lower()
            allowed_extensions = ['.txt', '.pdf', '.docx', '.html', '.md']

            if file_ext not in allowed_extensions:
                return jsonify({'error': f'File type {file_ext} not allowed. Allowed types: {allowed_extensions}'}), 400

            # Validate file size (max 50MB for large file support)
            # Seek to end to get file size, then reset position
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset position to beginning

            # Increase the file size limit to support larger files
            max_file_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', 100 * 1024 * 1024))  # Default to 100MB per file
            if size > max_file_size:
                max_size_mb = max_file_size // (1024 * 1024)
                return jsonify({'error': f'File size exceeds {max_size_mb}MB limit'}), 400

            # Generate unique filename to prevent conflicts, using the secure filename for filesystem
            unique_filename = f"{uuid.uuid4()}_{secure_filename_for_fs}"
            file_path = os.path.join(temp_dir, unique_filename)

            # Save file
            file.save(file_path)
            file_paths.append(file_path)

        if not file_paths:
            return jsonify({'error': 'No valid files to process'}), 400

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Ingest documents from the uploaded files with original filenames
        success = rag_orchestrator.ingest_documents_from_upload(file_paths, original_filenames)

        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir)

        if success:
            return jsonify({
                'message': f'{len(file_paths)} document(s) uploaded and ingested successfully',
                'file_count': len(file_paths)
            }), 200
        else:
            return jsonify({'error': 'Document ingestion failed'}), 500
    except Exception as e:
        logger.error(f"RAG upload error: {str(e)}")
        # Clean up temporary files in case of error
        import shutil
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temp directory: {cleanup_error}")
        return jsonify({'error': f'RAG upload failed: {str(e)}'}), 500


import uuid
from queue import Queue
import threading
import time
from datetime import datetime, timedelta

# Use Redis for shared storage across multiple Gunicorn workers
import redis
import json
import os

# Connect to Redis (fallback to localhost if not specified)
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

# Prefix for upload progress keys
UPLOAD_PROGRESS_PREFIX = "upload_progress:"

@app.route('/upload_progress/<session_id>', methods=['GET'])
@require_permission(Permission.WRITE_RAG)
def get_upload_progress(current_user_id, session_id):
    """Endpoint to get upload progress for a specific session"""
    try:
        # Get session data from Redis
        key = f"{UPLOAD_PROGRESS_PREFIX}{session_id}"
        session_data_json = redis_client.get(key)

        if session_data_json is None:
            return jsonify({'error': 'Session not found'}), 404

        # Deserialize the session data
        session_data = json.loads(session_data_json)

        # Check if session has expired
        expires_at_str = session_data.get('expires_at')
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Clean up expired session
                redis_client.delete(key)
                return jsonify({'error': 'Session expired'}), 404

        # Format the response to match what the frontend expects
        # The frontend expects a 'results' field with individual file statuses
        formatted_response = {
            'progress': session_data.get('progress', 0),
            'status': session_data.get('status', 'Initializing'),
            'current_file': session_data.get('current_file', ''),
            'total_files': session_data.get('total_files', 0),
            'completed_files': session_data.get('completed_files', 0),
            'results': session_data.get('results', {})  # Include all file statuses from session data
        }

        return jsonify(formatted_response), 200
    except Exception as e:
        logger.error(f"Get upload progress error: {str(e)}")
        return jsonify({'error': f'Failed to get upload progress: {str(e)}'}), 500

@app.route('/upload_with_progress', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_upload_with_progress(current_user_id):
    """Endpoint for uploading documents to RAG with progress tracking"""
    session_id = None  # Initialize session_id at function scope

    try:
        import re
        import os
        import tempfile

        # Generate a unique session ID for this upload
        session_id = str(uuid.uuid4())

        # Initialize progress tracking for this session with expiration in Redis
        session_data = {
            'progress': 0,
            'status': 'Initializing upload...',
            'current_file': '',
            'total_files': 0,
            'completed_files': 0,
            'results': {},  # Initialize results dictionary to track individual file status
            'file_paths': [],  # Store file paths for later ingestion
            'temp_dir': '',  # Store temp directory path for cleanup
            'filename_to_path_map': {},  # Store mapping of original filename to temporary file path
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()  # Expire after 1 hour
        }

        key = f"{UPLOAD_PROGRESS_PREFIX}{session_id}"
        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
        pipe.execute()

        # Check if files were included in the request
        if 'files' not in request.files:
            # Clean up progress tracking
            redis_client.delete(key)
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        print(f"DEBUG: Backend received {len(files)} files in upload_with_progress")
        for i, file in enumerate(files):
            if file and file.filename:
                print(f"DEBUG: Backend received file {i+1}: {file.filename}")

        if not files or all(f.filename == '' for f in files):
            # Clean up progress tracking
            redis_client.delete(key)
            return jsonify({'error': 'No files selected'}), 400

        # Validate file count
        max_files_per_upload = int(os.getenv('MAX_FILES_PER_UPLOAD', 100))  # Default to 100 files per upload
        if len(files) > max_files_per_upload:  # Maximum configurable files at once
            # Clean up progress tracking
            redis_client.delete(key)
            return jsonify({'error': f'Maximum {max_files_per_upload} files allowed per upload'}), 400

        # Update progress tracking
        total_files_count = len([f for f in files if f.filename != ''])
        session_data['total_files'] = total_files_count
        session_data['status'] = f'Preparing to upload {total_files_count} files...'

        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
        pipe.execute()

        # Temporary directory to store uploaded files
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        original_filenames = []  # Store original filenames

        for file in files:
            if file.filename == '':
                continue

            # Update progress
            session_data['status'] = f'Validating file: {file.filename}'
            pipe = redis_client.pipeline()
            pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
            pipe.execute()

            # Validate file type
            # Store the original filename before sanitizing for filesystem operations
            original_filename_unsanitized = file.filename
            original_filenames.append(original_filename_unsanitized)  # Store original unsanitized filename
            secure_filename_for_fs = secure_filename(file.filename)  # Sanitize for filesystem operations
            file_ext = Path(secure_filename_for_fs).suffix.lower()
            allowed_extensions = ['.txt', '.pdf', '.docx', '.html', '.md']

            if file_ext not in allowed_extensions:
                # Clean up progress tracking and temp files
                redis_client.delete(key)
                import shutil
                shutil.rmtree(temp_dir)
                return jsonify({'error': f'File type {file_ext} not allowed. Allowed types: {allowed_extensions}'}), 400

            # Validate file size (max 50MB for large file support)
            # Seek to end to get file size, then reset position
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset position to beginning

            # Increase the file size limit to support larger files
            max_file_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', 100 * 1024 * 1024))  # Default to 100MB per file
            if size > max_file_size:
                max_size_mb = max_file_size // (1024 * 1024)
                # Clean up progress tracking and temp files
                redis_client.delete(key)
                import shutil
                shutil.rmtree(temp_dir)
                return jsonify({'error': f'File size exceeds {max_size_mb}MB limit'}), 400

            # Generate unique filename to prevent conflicts, using the secure filename for filesystem
            unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            file_path = os.path.join(temp_dir, unique_filename)

            # Save file
            file.save(file_path)
            file_paths.append(file_path)

        # Update session data to include file paths, temp directory, and filename-to-path mapping
        session_data['file_paths'] = file_paths
        session_data['temp_dir'] = temp_dir

        # Create mapping of original filename to temporary file path
        filename_to_path_map = {}
        for i, original_filename in enumerate(original_filenames):
            if i < len(file_paths):
                filename_to_path_map[original_filename] = file_paths[i]
        session_data['filename_to_path_map'] = filename_to_path_map

        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
        pipe.execute()

        # Initialize results for each file with 'pending' status after collecting all filenames
        session_data_with_results = json.loads(redis_client.get(key) or json.dumps(session_data))
        for filename in original_filenames:
            session_data_with_results['results'][filename] = {
                'status': 'pending',
                'message': f'{filename} waiting to be processed',
                'progress': 0
            }
        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data_with_results))
        pipe.execute()

        if not file_paths:
            # Clean up progress tracking
            redis_client.delete(key)
            return jsonify({'error': 'No valid files to process'}), 400

        # Update progress tracking to indicate upload is complete and ready for ingestion
        session_data['status'] = 'Upload complete. Ready for ingestion.'
        session_data['progress'] = 100  # Upload is complete
        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
        pipe.execute()

        # Return session ID to the client so they can poll for progress
        return jsonify({
            'message': f'{len(file_paths)} document(s) prepared for upload',
            'file_count': len(file_paths),
            'session_id': session_id,
            'progress_tracking_available': True
        }), 200
    except Exception as e:
        logger.error(f"RAG upload with progress error: {str(e)}")
        # Clean up temporary files in case of error
        import shutil
        try:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temp directory: {cleanup_error}")
        # Clean up progress tracking if session_id was created
        if session_id:
            key = f"{UPLOAD_PROGRESS_PREFIX}{session_id}"
            redis_client.delete(key)
        return jsonify({'error': f'RAG upload with progress failed: {str(e)}'}), 500




@app.route('/download/<file_id>/<filename>', methods=['GET'])
def rag_download_file(file_id, filename):
    """Endpoint to download an original file by its ID and filename"""
    try:
        import os
        from config.settings import RAG_FILE_STORAGE_DIR

        # Construct the file path using the file ID and filename
        # Ensure we use an absolute path for file storage directory
        base_storage_dir = RAG_FILE_STORAGE_DIR or "./data/rag_uploaded_files"
        if not os.path.isabs(base_storage_dir):
            # Convert relative path to absolute path relative to project root
            # Navigate up 4 levels from backend/services/rag/app.py to reach project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            base_storage_dir = os.path.join(project_root, base_storage_dir)
        file_storage_dir = os.path.join(base_storage_dir, file_id)

        # Try multiple possible filename formats to handle files stored before/after sanitization changes
        possible_filenames = [
            filename,  # Original filename as received (could be sanitized or not)
        ]

        # Also try the desanitized version (underscores to spaces) for files that were stored with original names
        # This handles the case where URL has sanitized name but file was stored with original name
        if '_' in filename:
            # Convert underscores back to spaces to check for original filename
            desanitized_filename = filename.replace('_', ' ')
            if desanitized_filename != filename:
                possible_filenames.append(desanitized_filename)

        # Also try the sanitized version in case file was stored with sanitized name
        sanitized_filename = secure_filename(filename)
        if sanitized_filename != filename:
            possible_filenames.append(sanitized_filename)

        # Remove duplicates while preserving order
        seen = set()
        unique_filenames = []
        for fname in possible_filenames:
            if fname not in seen:
                seen.add(fname)
                unique_filenames.append(fname)

        file_path = None
        for fname in unique_filenames:
            test_path = os.path.join(file_storage_dir, fname)
            if os.path.exists(test_path):
                file_path = test_path
                break

        # Verify that the file exists and is within the expected directory
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        # Double-check that the resolved path is within the expected directory
        # to prevent directory traversal attacks
        resolved_path = os.path.realpath(file_path)
        expected_dir = os.path.realpath(os.getenv("RAG_FILE_STORAGE_DIR", "./data/rag_uploaded_files"))

        if not resolved_path.startswith(expected_dir):
            return jsonify({'error': 'Access denied'}), 403

        # Serve the file
        from flask import send_file
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        logger.error(f"RAG file download error: {str(e)}")
        return jsonify({'error': f'RAG file download failed: {str(e)}'}), 500


# Chunked upload support for large files
upload_sessions = {}


@app.route('/chunked_upload/start', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def start_chunked_upload(current_user_id):
    """Start a chunked upload session for large files"""
    try:
        data = request.get_json()

        # Validate input
        if not data or 'filename' not in data or 'total_chunks' not in data:
            return jsonify({'error': 'Missing required fields: filename and total_chunks'}), 400

        filename = data['filename']
        total_chunks = int(data['total_chunks'])

        # Generate a unique session ID for this upload
        session_id = str(uuid.uuid4())

        # Create a temporary directory for this upload session
        session_dir = os.path.join(tempfile.gettempdir(), f"chunked_upload_{session_id}")
        os.makedirs(session_dir, exist_ok=True)

        # Store session info
        upload_sessions[session_id] = {
            'filename': filename,
            'total_chunks': total_chunks,
            'received_chunks': [],
            'session_dir': session_dir,
            'completed': False
        }

        return jsonify({
            'session_id': session_id,
            'message': f'Chunked upload session started for {filename} with {total_chunks} chunks'
        }), 200

    except Exception as e:
        logger.error(f"Start chunked upload error: {str(e)}")
        return jsonify({'error': f'Start chunked upload failed: {str(e)}'}), 500


@app.route('/chunked_upload/<session_id>', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def upload_chunk(current_user_id, session_id):
    """Upload a single chunk of a large file"""
    try:
        if session_id not in upload_sessions:
            return jsonify({'error': 'Invalid session ID'}), 400

        session_info = upload_sessions[session_id]

        # Get the chunk number and data
        chunk_number = int(request.form.get('chunk_number', -1))
        chunk_data = request.files.get('chunk')

        if chunk_number < 0 or chunk_data is None:
            return jsonify({'error': 'Invalid chunk data'}), 400

        # Validate chunk number
        if chunk_number >= session_info['total_chunks']:
            return jsonify({'error': 'Chunk number exceeds total chunks'}), 400

        # Save the chunk to the session directory
        chunk_path = os.path.join(session_info['session_dir'], f"chunk_{chunk_number}")
        chunk_data.save(chunk_path)

        # Record that we received this chunk
        if chunk_number not in session_info['received_chunks']:
            session_info['received_chunks'].append(chunk_number)
            session_info['received_chunks'].sort()

        # Check if all chunks have been received
        all_received = len(session_info['received_chunks']) == session_info['total_chunks']

        return jsonify({
            'chunk_number': chunk_number,
            'received_chunks': len(session_info['received_chunks']),
            'total_chunks': session_info['total_chunks'],
            'all_chunks_received': all_received
        }), 200

    except Exception as e:
        logger.error(f"Upload chunk error: {str(e)}")
        return jsonify({'error': f'Upload chunk failed: {str(e)}'}), 500


@app.route('/chunked_upload/<session_id>/complete', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def complete_chunked_upload(current_user_id, session_id):
    """Complete a chunked upload by assembling all chunks into a single file"""
    try:
        if session_id not in upload_sessions:
            return jsonify({'error': 'Invalid session ID'}), 400

        session_info = upload_sessions[session_id]

        # Check if all chunks have been received
        if len(session_info['received_chunks']) != session_info['total_chunks']:
            return jsonify({
                'error': 'Not all chunks have been received',
                'received_chunks': len(session_info['received_chunks']),
                'total_chunks': session_info['total_chunks']
            }), 400

        # Assemble the chunks into a single file
        assembled_file_path = os.path.join(session_info['session_dir'], 'assembled_file')

        with open(assembled_file_path, 'wb') as output_file:
            for chunk_num in range(session_info['total_chunks']):
                chunk_path = os.path.join(session_info['session_dir'], f"chunk_{chunk_num}")
                with open(chunk_path, 'rb') as chunk_file:
                    output_file.write(chunk_file.read())

        # Now ingest the assembled file using the existing RAG functionality
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Ingest the assembled file
        success = rag_orchestrator.ingest_documents_from_upload(
            [assembled_file_path],
            [session_info['filename']]
        )

        if success:
            # Mark session as completed
            session_info['completed'] = True

            # Clean up temporary files
            import shutil
            shutil.rmtree(session_info['session_dir'])

            # Remove session from tracking
            del upload_sessions[session_id]

            return jsonify({
                'message': f'Chunked upload completed successfully for {session_info["filename"]}',
                'filename': session_info['filename']
            }), 200
        else:
            return jsonify({'error': 'Failed to ingest the uploaded file'}), 500

    except Exception as e:
        logger.error(f"Complete chunked upload error: {str(e)}")
        return jsonify({'error': f'Complete chunked upload failed: {str(e)}'}), 500


@app.route('/clear', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_clear(current_user_id):
    """Endpoint for clearing all documents from the RAG store"""
    try:
        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Clear the collection
        rag_orchestrator.vector_store_manager.delete_collection()

        return jsonify({'message': 'All documents cleared successfully'}), 200
    except Exception as e:
        logger.error(f"RAG clear error: {str(e)}")
        return jsonify({'error': f'RAG clear failed: {str(e)}'}), 500


@app.route('/status', methods=['GET'])
@require_permission(Permission.READ_RAG)
def rag_status(current_user_id):
    """Get the status of the RAG component"""
    return jsonify({
        'status': 'running',
        'service': 'rag',
        'message': 'RAG component is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/limits', methods=['GET'])
@require_permission(Permission.READ_RAG)
def rag_limits(current_user_id):
    """Get the upload limits for the RAG component"""
    max_files_per_upload = int(os.getenv('MAX_FILES_PER_UPLOAD', 100))
    max_file_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', 100 * 1024 * 1024))  # Default to 100MB
    max_total_size = int(os.getenv('MAX_TOTAL_UPLOAD_SIZE', 500 * 1024 * 1024))  # Default to 500MB

    return jsonify({
        'max_files_per_upload': max_files_per_upload,
        'max_file_size_bytes': max_file_size,
        'max_file_size_mb': round(max_file_size / (1024 * 1024), 2),
        'max_total_size_bytes': max_total_size,
        'max_total_size_mb': round(max_total_size / (1024 * 1024), 2),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Note: Redis handles key expiration automatically, so no manual cleanup needed


@app.route('/ingest_from_session', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_ingest_from_session(current_user_id):
    """Ingest documents from a session - uses files previously uploaded with progress tracking"""
    try:
        import os
        data = request.get_json()

        session_id = data.get('session_id')
        filenames = data.get('filenames', [])

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400

        # Get session data from Redis to find uploaded files
        key = f"{UPLOAD_PROGRESS_PREFIX}{session_id}"
        session_data_json = redis_client.get(key)

        if session_data_json is None:
            return jsonify({'error': 'Session not found'}), 404

        # Deserialize the session data
        session_data = json.loads(session_data_json)

        # Check if session has expired
        expires_at_str = session_data.get('expires_at')
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.now() > expires_at:
                # Clean up expired session
                redis_client.delete(key)
                return jsonify({'error': 'Session expired'}), 404

        # Get the file paths from the session data
        file_paths = session_data.get('file_paths', [])
        temp_dir = session_data.get('temp_dir', '')

        if not file_paths:
            return jsonify({'error': 'No files found in session'}), 404

        # If specific filenames were provided, filter the file paths to only include those files
        if filenames:
            # Use the stored mapping to get the file paths for the requested filenames
            filename_to_path_map = session_data.get('filename_to_path_map', {})
            filtered_file_paths = []

            for filename in filenames:
                if filename in filename_to_path_map:
                    filtered_file_paths.append(filename_to_path_map[filename])

            if not filtered_file_paths:
                return jsonify({'error': 'Requested filenames not found in session'}), 404

            file_paths = filtered_file_paths
        else:
            # If no specific filenames requested, use all file paths
            # Get original filenames from the mapping
            filename_to_path_map = session_data.get('filename_to_path_map', {})
            filenames = list(filename_to_path_map.keys())

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Get original filenames from the mapping in session data
        filename_to_path_map = session_data.get('filename_to_path_map', {})
        original_filenames = list(filename_to_path_map.keys())

        # Ingest the files from the session
        success = rag_orchestrator.ingest_documents_from_upload(file_paths, filenames if filenames else original_filenames)

        if success:
            # Update session status to indicate ingestion is complete
            session_data['status'] = 'Ingestion completed successfully'
            session_data['ingestion_completed'] = datetime.now().isoformat()

            # Clean up the temporary directory after successful ingestion
            temp_dir = session_data.get('temp_dir', '')
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up temp directory {temp_dir}: {cleanup_error}")

            # Update Redis with updated session data
            pipe = redis_client.pipeline()
            pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
            pipe.execute()

            return jsonify({
                'message': f'Documents from session {session_id} ingested successfully',
                'session_id': session_id,
                'filenames': filenames if filenames else original_filenames
            }), 200
        else:
            return jsonify({'error': 'Document ingestion failed'}), 500
    except Exception as e:
        logger.error(f"RAG ingestion from session error: {str(e)}")
        return jsonify({'error': f'RAG ingestion from session failed: {str(e)}'}), 500


@app.route('/import_processed', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def import_processed_documents(current_user_id):
    """Endpoint for importing pre-processed JSON documents with chunks and metadata"""
    try:
        import json
        import tempfile
        import os
        from langchain_core.documents import Document as LCDocument
        from rag_component.file_storage_manager import FileStorageManager

        # Check if the request contains files
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        uploaded_files = request.files.getlist('file')

        if not uploaded_files or all(f.filename == '' for f in uploaded_files):
            return jsonify({'error': 'No file selected'}), 400

        # Validate file types
        for file in uploaded_files:
            if file and file.filename != '' and not file.filename.lower().endswith('.json'):
                return jsonify({'error': f'File {file.filename} is not a JSON file. Only JSON files are allowed for processed document import'}), 400

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)
        file_storage_manager = FileStorageManager()

        total_chunks_imported = 0
        successful_imports = []
        failed_imports = []

        # Process each file individually
        for file in uploaded_files:
            if not file or file.filename == '':
                continue

            temp_file_path = None
            try:
                # Save the uploaded file temporarily to store it
                with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name

                # Read and parse the JSON file
                try:
                    with open(temp_file_path, 'r', encoding='utf-8') as f:
                        processed_data = json.load(f)
                except json.JSONDecodeError as e:
                    failed_imports.append({
                        'filename': file.filename,
                        'error': f'Invalid JSON format: {str(e)}'
                    })
                    continue  # Skip to the next file
                except UnicodeDecodeError as e:
                    failed_imports.append({
                        'filename': file.filename,
                        'error': f'Invalid UTF-8 encoding: {str(e)}'
                    })
                    continue  # Skip to the next file

                # Validate the structure of the processed data
                required_fields = ['document', 'chunks']
                for field in required_fields:
                    if field not in processed_data:
                        failed_imports.append({
                            'filename': file.filename,
                            'error': f'Missing required field: {field}'
                        })
                        continue  # Skip to the next file

                if not isinstance(processed_data['chunks'], list):
                    failed_imports.append({
                        'filename': file.filename,
                        'error': 'Chunks must be an array'
                    })
                    continue  # Skip to the next file

                # Store the original JSON file using the file storage manager
                stored_file_path = file_storage_manager.store_file(temp_file_path, file.filename)

                # Extract the file ID from the stored file path
                stored_dir = os.path.dirname(stored_file_path)
                file_id = os.path.basename(stored_dir)

                # Convert the processed chunks to LangChain documents
                documents = []
                for chunk in processed_data['chunks']:
                    # Validate required fields in each chunk
                    if 'content' not in chunk:
                        failed_imports.append({
                            'filename': file.filename,
                            'error': 'Each chunk must have a content field'
                        })
                        continue  # Skip to the next file

                    # Create a LangChain document from the chunk
                    doc_content = chunk['content']

                    # Create metadata for the document
                    doc_metadata = {
                        'source': processed_data.get('document', 'processed_document'),
                        'chunk_id': chunk.get('chunk_id', ''),
                        'section': chunk.get('section', ''),
                        'title': chunk.get('title', ''),
                        'chunk_type': chunk.get('chunk_type', ''),
                        'token_count': chunk.get('token_count', 0),
                        'contains_formula': chunk.get('contains_formula', False),
                        'contains_table': chunk.get('contains_table', False),
                        'upload_method': 'Processed JSON Import',
                        'user_id': current_user_id,
                        # Add stored file path and file ID for download capability
                        'stored_file_path': stored_file_path,
                        'file_id': file_id
                    }

                    # Add trust level if present
                    if 'trust_level' in chunk:
                        doc_metadata['trust_level'] = chunk['trust_level']

                    # Add testing scenario if present
                    if 'testing_scenario' in chunk:
                        doc_metadata['testing_scenario'] = chunk['testing_scenario']

                    # Add formula ID if present
                    if 'formula_id' in chunk:
                        doc_metadata['formula_id'] = chunk['formula_id']

                    # Add overlap information if present
                    if 'overlap_source' in chunk:
                        doc_metadata['overlap_source'] = chunk['overlap_source']
                    if 'overlap_tokens' in chunk:
                        doc_metadata['overlap_tokens'] = chunk['overlap_tokens']

                    # Add any other custom metadata from the chunk
                    for key, value in chunk.items():
                        if key not in ['content', 'chunk_id', 'section', 'title', 'chunk_type',
                                       'token_count', 'contains_formula', 'contains_table',
                                       'trust_level', 'testing_scenario', 'formula_id',
                                       'overlap_source', 'overlap_tokens']:
                            doc_metadata[key] = value

                    # Create the LangChain document
                    lc_doc = LCDocument(page_content=doc_content, metadata=doc_metadata)
                    documents.append(lc_doc)

                # Add documents to the vector store using the RAG orchestrator
                rag_orchestrator.vector_store_manager.add_documents(documents)

                total_chunks_imported += len(documents)

                successful_imports.append({
                    'filename': file.filename,
                    'chunks_imported': len(documents),
                    'document': processed_data.get('document', 'unknown')
                })

            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

                failed_imports.append({
                    'filename': file.filename,
                    'error': str(e)
                })

            finally:
                # Clean up the temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except OSError:
                        pass  # Ignore errors during temp file cleanup

        # Prepare response
        response_data = {
            'message': f'Import completed. Successfully imported {len(successful_imports)} files with {total_chunks_imported} total chunks.',
            'successful_imports': successful_imports,
            'failed_imports': failed_imports,
            'total_files_attempted': len(uploaded_files),
            'total_successful': len(successful_imports),
            'total_failed': len(failed_imports)
        }

        # Return success if at least one file was imported successfully
        if successful_imports:
            status_code = 200
        else:
            status_code = 400  # Return 400 if no files were successfully imported

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error(f"Processed document import error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Processed document import failed: {str(e)}'}), 500


# Document Store endpoints
@app.route('/api/rag/document_store/jobs', methods=['GET'])
@require_permission(Permission.READ_RAG)
def list_document_store_jobs(current_user_id):
    """List all ingestion jobs from Document Store MCP Server with documents"""
    try:
        from .document_store_client import document_store_client

        # Get list of jobs
        jobs_result = document_store_client.list_ingestion_jobs()

        # Handle nested response structure
        if jobs_result.get('success'):
            result = jobs_result.get('result', {})
            # Check if result itself has success and jobs (nested MCP response)
            if isinstance(result, dict) and result.get('success'):
                jobs = result.get('jobs', [])
            else:
                jobs = result.get('jobs', [])

            # For each job, get the list of documents
            for job in jobs:
                job_id = job.get('job_id')
                if job_id:
                    # Call list_documents for this job
                    docs_result = document_store_client.list_documents(job_id)
                    logger.info(f"[DocStore API] list_documents result for {job_id}: {docs_result}")

                    if docs_result.get('success'):
                        docs_data = docs_result.get('result', {})
                        logger.info(f"[DocStore API] docs_data: {docs_data}")

                        if isinstance(docs_data, dict) and docs_data.get('success'):
                            job['documents'] = docs_data.get('documents', [])
                            logger.info(f"[DocStore API] Set job['documents'] from nested success: {job['documents'][:2] if job['documents'] else []}")
                        else:
                            job['documents'] = docs_data.get('documents', [])
                            logger.info(f"[DocStore API] Set job['documents'] directly: {job['documents'][:2] if job['documents'] else []}")
                    else:
                        job['documents'] = []
                        logger.warning(f"[DocStore API] list_documents failed: {docs_result}")
                else:
                    job['documents'] = []

            return jsonify({'jobs': jobs}), 200
        else:
            return jsonify({'error': jobs_result.get('error', 'Unknown error')}), 500

    except Exception as e:
        logger.error(f"Error listing Document Store jobs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/document_store/get_document', methods=['POST'])
@require_permission(Permission.READ_RAG)
def get_document_from_store(current_user_id):
    """Get a specific document from Document Store by job_id and doc_id"""
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        doc_id = data.get('doc_id')

        if not job_id or not doc_id:
            return jsonify({'error': 'job_id and doc_id are required'}), 400

        from .document_store_client import document_store_client

        # Get the document
        doc_result = document_store_client.get_document(job_id, doc_id, format='txt')

        if not doc_result.get('success'):
            return jsonify({'error': doc_result.get('error', 'Failed to get document')}), 500

        # Extract content from result
        result_data = doc_result.get('result', {})
        content = result_data.get('content', '')
        
        # If content is in nested structure
        if not content and isinstance(result_data, dict):
            content = result_data.get('text', '')

        return jsonify({
            'job_id': job_id,
            'doc_id': doc_id,
            'content': content,
            'text': content
        }), 200

    except Exception as e:
        logger.error(f"Error getting document from Document Store: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/document_store/import', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def import_from_document_store(current_user_id):
    """Import documents from Document Store and process them"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        doc_ids = data.get('doc_ids', [])
        
        if not job_id and not doc_ids:
            return jsonify({'error': 'job_id or doc_ids required'}), 400
        
        from .document_store_client import document_store_client
        from rag_component.main import RAGOrchestrator
        
        # Get documents from Document Store
        if job_id:
            docs_result = document_store_client.get_documents_by_job(job_id)
        else:
            docs_result = document_store_client.get_documents(doc_ids)
        
        if not docs_result.get('success'):
            return jsonify({'error': docs_result.get('error', 'Failed to get documents')}), 500
        
        documents = docs_result.get('result', {}).get('documents', [])
        
        # Process each document
        results = {'processed': 0, 'errors': [], 'chunks_total': 0}
        rag = RAGOrchestrator()
        
        for doc in documents:
            try:
                content = doc.get('content', '')
                if content:
                    # Add to RAG
                    rag_result = rag.ingest_text(
                        text=content,
                        metadata={
                            'source': 'document_store',
                            'filename': doc.get('filename', ''),
                            'doc_id': doc.get('doc_id', '')
                        }
                    )
                    results['processed'] += 1
                    results['chunks_total'] += len(rag_result.get('chunks', []))
            except Exception as e:
                results['errors'].append({
                    'doc_id': doc.get('doc_id', ''),
                    'error': str(e)
                })
        
        return jsonify(results), 200
        
    except Exception as e:
        logger.error(f"Error importing from Document Store: {e}")
        return jsonify({'error': str(e)}), 500


# Smart Ingestion endpoint - handles file uploads
@app.route('/api/rag/smart_ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def smart_ingest(current_user_id):
    """
    Smart ingestion endpoint - handles file uploads and LLM-based chunking
    """
    try:
        from rag_component.document_loader import DocumentLoader
        from rag_component.vector_store_manager import VectorStoreManager
        from langchain_core.documents import Document
        from models.response_generator import ResponseGenerator
        import re

        # Check if files were included in the request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400

        # Get parameters from form
        chunking_strategy = request.form.get('chunking_strategy', 'smart_chunking')
        ingest_chunks = request.form.get('ingest_chunks', 'true').lower() == 'true'
        custom_prompt = request.form.get('custom_prompt', '')
        process_mode = request.form.get('process_mode', 'vector_db')

        results = {
            'documents_processed': 0,
            'total_chunks': 0,
            'errors': []
        }

        document_loader = DocumentLoader()
        vector_store = VectorStoreManager() if ingest_chunks else None

        # Get LLM instance if using smart chunking
        llm = None
        if chunking_strategy == 'smart_chunking':
            response_gen = ResponseGenerator()
            llm = response_gen._get_llm_instance(
                provider=RESPONSE_LLM_PROVIDER,
                model=RESPONSE_LLM_MODEL
            )
            if not custom_prompt:
                from .smart_ingestion_enhanced import DEFAULT_SMART_CHUNKING_PROMPT
                custom_prompt = DEFAULT_SMART_CHUNKING_PROMPT

        for file in files:
            try:
                import tempfile
                import os

                # Save file temporarily
                temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                os.close(temp_fd)
                file.save(temp_path)

                # Extract text
                docs = document_loader.load_document(temp_path)
                document_content = "\n".join([doc.page_content for doc in docs])

                if not document_content.strip():
                    results['errors'].append({'filename': file.filename, 'error': 'Empty document'})
                    os.remove(temp_path)
                    continue

                # Apply chunking strategy
                chunks = []

                if chunking_strategy == 'smart_chunking' and llm and custom_prompt:
                    try:
                        # Qwen 3.5 35B has 262k context window - can handle most docs in single call
                        # Threshold: 800k chars ≈ 200k tokens (leaves room for prompt + output)
                        MAX_SINGLE_CALL = 800000  # chars
                        
                        if len(document_content) > MAX_SINGLE_CALL:
                            # VERY LARGE DOCUMENT (> 800k chars, ~200k tokens)
                            # Split into sections with Context Summary for coherence
                            logger.info(f"Large document ({len(document_content)} chars), splitting into sections")
                            
                            MAX_SECTION_SIZE = 700000  # ~175k tokens per section
                            sections = []
                            remaining = document_content
                            
                            while len(remaining) > MAX_SECTION_SIZE:
                                # Split at paragraph boundary
                                cut_point = remaining.rfind('\n\n', 0, MAX_SECTION_SIZE)
                                if cut_point == -1:
                                    cut_point = MAX_SECTION_SIZE
                                sections.append(remaining[:cut_point])
                                remaining = remaining[cut_point:].lstrip()
                            
                            if remaining:
                                sections.append(remaining)
                            
                            logger.info(f"Split into {len(sections)} sections for LLM chunking")
                            
                            # Process each section with Context Summary handoff
                            all_chunks = []
                            previous_summary = ""
                            previous_entities = []
                            
                            for section_idx, section in enumerate(sections):
                                logger.info(f"Processing section {section_idx + 1}/{len(sections)} ({len(section)} chars)")
                                
                                # Build context header for sections 2+
                                if previous_summary:
                                    context_header = f"""
## Context from Previous Section

**Summary:** {previous_summary}

**Key Entities:** {', '.join(previous_entities)}

Continue chunking with this context in mind. Maintain semantic continuity with adjacent sections.
"""
                                else:
                                    context_header = ""
                                
                                # Build prompt with document context
                                section_prompt = f"""{custom_prompt}

{context_header}

## Document: {file_info['original_filename']}
## Section {section_idx + 1} of {len(sections)}

{section}

## Output Format
Return JSON with these fields:
{{
  "document": "document identifier",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number",
      "title": "descriptive title",
      "chunk_type": "chunk type",
      "content": "chunk text here",
      "token_count": integer
    }}
  ],
  "document_summary": "2-3 sentences summarizing what this section covers",
  "key_entities": ["important entities from this section for graph context"],
  "embedding_recommendations": {{
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "metadata_indexing": "Index section, chunk_type, contains_formula fields"
  }}
}}
"""
                                
                                llm_response = llm.invoke(section_prompt)
                                response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

                                # Parse JSON from response using robust parser
                                chunking_result = parse_json_robust(response_content, default_on_error={'chunks': []})
                                
                                # Validate the result
                                is_valid, errors = validate_chunking_result(chunking_result)
                                if not is_valid:
                                    logger.warning(f"Section {section_idx + 1}: Invalid chunking result - {errors}")
                                
                                chunks_data = chunking_result.get('chunks', [])

                                section_chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
                                all_chunks.extend(section_chunks)

                                # Save context for next section
                                previous_summary = chunking_result.get('document_summary', '')
                                previous_entities = chunking_result.get('key_entities', [])

                                logger.info(f"Section {section_idx + 1}: LLM generated {len(section_chunks)} chunks")
                            
                            chunks = all_chunks
                            logger.info(f"Total: LLM generated {len(chunks)} chunks from {len(sections)} sections for {file_info['original_filename']}")
                            
                        else:
                            # MOST DOCUMENTS (97%): Single LLM call with full document context
                            logger.info(f"Document fits in single LLM call ({len(document_content)} chars)")
                            
                            # Build prompt for single-call processing
                            single_prompt = f"""{custom_prompt}

## Document: {file_info['original_filename']}

{document_content}

## Output Format
Return JSON with these fields:
{{
  "document": "document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number or appendix_X",
      "title": "descriptive title in language of document",
      "chunk_type": "one of: header_and_scope | references_and_definitions | formula_with_context | testing_procedure | appendix_example",
      "contains_formula": boolean,
      "contains_table": boolean,
      "formula_id": "1,2,3... or null",
      "formula_reference": "referenced formula number or null",
      "content": "chunk text here",
      "token_count": integer (200-450 tokens per chunk)
    }}
  ],
  "document_summary": "2-3 sentences summarizing document content for graph context",
  "key_entities": ["important entities from document for graph context (standards, organizations, technologies, etc.)"],
  "embedding_recommendations": {{
    "model": "text-embedding-3-large or equivalent multilingual",
    "chunk_size_target": "200-450 tokens",
    "overlap_strategy": "Apply overlaps ONLY at procedural boundaries to preserve algorithmic continuity",
    "metadata_indexing": "Index section, chunk_type, contains_formula, document_summary fields for hybrid search"
  }}
}}

## Chunking Guidelines
- Target 200-450 tokens per chunk
- Preserve semantic units (formulas, tables, procedures)
- Include section headers in chunk content
- Extract entities: GOST/ISO standards, organizations, technologies, dates, concepts
"""
                            
                            llm_response = llm.invoke(single_prompt)
                            response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

                            # Parse JSON from response using robust parser
                            chunking_result = parse_json_robust(response_content, default_on_error={'chunks': []})
                            
                            # Validate the result
                            is_valid, errors = validate_chunking_result(chunking_result)
                            if not is_valid:
                                logger.warning(f"Invalid chunking result - {errors}")
                            
                            chunks_data = chunking_result.get('chunks', [])

                            chunks = [c.get('content', '') for c in chunks_data if c.get('content')]

                            # Store document-level metadata for graph context
                            document_summary = chunking_result.get('document_summary', '')
                            key_entities = chunking_result.get('key_entities', [])

                            logger.info(f"Single-call LLM generated {len(chunks)} chunks for {file_info['original_filename']}")
                            if document_summary:
                                logger.info(f"Document summary: {document_summary[:100]}...")
                            if key_entities:
                                logger.info(f"Key entities: {len(key_entities)} entities extracted")

                    except Exception as llm_error:
                        logger.error(f"LLM chunking failed for {file_info['filename']}: {llm_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Fallback to simple chunking
                        chunks = document_content.split('\n\n')
                        chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                        logger.info(f"Fallback simple chunking generated {len(chunks)} chunks")
                        document_summary = ""
                        key_entities = []
                else:
                    # Simple chunking
                    chunks = document_content.split('\n\n')
                    chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                    document_summary = ""
                    key_entities = []

                if ingest_chunks and vector_store:
                    lc_docs = []
                    for i, chunk in enumerate(chunks):
                        if not chunk.strip():
                            continue
                        lc_docs.append(Document(
                            page_content=chunk,
                            metadata={
                                'source': file.filename,
                                'chunk_id': i,
                                'chunking_strategy': chunking_strategy,
                                'process_mode': process_mode
                            }
                        ))
                    if lc_docs:
                        vector_store.add_documents(lc_docs)
                        logger.info(f"Added {len(lc_docs)} chunks to vector store for {file.filename}")

                results['documents_processed'] += 1
                results['total_chunks'] += len(chunks)
                os.remove(temp_path)

            except Exception as e:
                logger.error(f"Error processing {file.filename}: {e}")
                results['errors'].append({'filename': file.filename, 'error': str(e)})

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Smart ingest error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Smart ingestion failed: {str(e)}'}), 500


# Smart Ingestion from Files endpoint - ASYNC
@app.route('/api/rag/smart_ingest_files', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def smart_ingest_files(current_user_id):
    """
    Smart ingestion from file uploads - ASYNC - creates background job
    Accepts multipart/form-data with files and parameters
    """
    try:
        import tempfile
        import os
        import uuid
        import shutil
        
        # Check if files were included
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Get parameters
        chunking_strategy = request.form.get('chunking_strategy', 'smart_chunking')
        ingest_chunks = request.form.get('ingest_chunks', 'true').lower() == 'true'
        process_mode = request.form.get('process_mode', 'vector_db')
        custom_prompt = request.form.get('custom_prompt', '')
        
        if not custom_prompt:
            from .smart_ingestion_enhanced import DEFAULT_SMART_CHUNKING_PROMPT
            custom_prompt = DEFAULT_SMART_CHUNKING_PROMPT
        
        # Create temp directory for this job
        job_temp_id = str(uuid.uuid4())
        temp_dir = os.path.join(tempfile.gettempdir(), f"rag_ingest_{job_temp_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save files and collect info
        saved_files = []
        for file in files:
            if file.filename == '':
                continue
            
            # Debug logging
            file_ext = os.path.splitext(file.filename)[1].lower()
            logger.info(f"Processing file: {file.filename}, ext: {file_ext}")
            
            # Validate file type
            file_ext = os.path.splitext(file.filename)[1].lower()
            allowed_extensions = ['.pdf', '.txt', '.md', '.docx', '.html']
            if file_ext not in allowed_extensions:
                continue
            
            # Save file
            safe_filename = secure_filename(file.filename)
            file_path = os.path.join(temp_dir, safe_filename)
            file.save(file_path)
            saved_files.append({
                'filename': safe_filename,
                'original_filename': file.filename,
                'path': file_path
            })
        
        if not saved_files:
            shutil.rmtree(temp_dir)
            return jsonify({'error': 'No valid files to process'}), 400
        
        # Create background job with configuration tracking
        from .job_queue import job_queue
        
        job = job_queue.create_job(
            user_id=current_user_id,
            job_type='smart_ingest_files',
            parameters={
                'temp_dir': temp_dir,
                'files': saved_files,
                'chunking_strategy': chunking_strategy,
                'ingest_chunks': ingest_chunks,
                'process_mode': process_mode,
                'prompt': custom_prompt,
                'total_documents': len(saved_files)
            },
            ingestion_mode='files',
            processing_mode=process_mode,
            chunking_strategy=chunking_strategy
        )
        
        # Start background worker
        def process_files_background(job):
            """Background processing function for uploaded files"""
            from .job_queue import job_queue
            from rag_component.document_loader import DocumentLoader
            from rag_component.vector_store_manager import VectorStoreManager
            from langchain_core.documents import Document
            from models.response_generator import ResponseGenerator
            import re
            import os
            import shutil
            
            try:
                job_id = job.job_id
                temp_dir = job.parameters.get('temp_dir')
                saved_files = job.parameters.get('files', [])
                chunking_strategy = job.chunking_strategy
                ingest_chunks = job.parameters.get('ingest_chunks', True)
                process_mode = job.processing_mode
                prompt = job.parameters.get('prompt', '')
                total_documents = len(saved_files)
                
                document_loader = DocumentLoader()
                vector_store = VectorStoreManager() if ingest_chunks else None
                
                # Get LLM instance if using smart chunking
                llm = None
                if chunking_strategy == 'smart_chunking':
                    response_gen = ResponseGenerator()
                    llm = response_gen._get_llm_instance(
                        provider=RESPONSE_LLM_PROVIDER,
                        model=RESPONSE_LLM_MODEL
                    )
                
                results = {
                    'documents_processed': 0,
                    'total_chunks': 0,
                    'errors': [],
                    'file_results': []
                }
                
                for idx, file_info in enumerate(saved_files):
                    try:
                        # Update job progress
                        job.progress = int((idx / total_documents) * 100) if total_documents > 0 else 0
                        job.current_stage = f"Processing {file_info['filename']}"
                        job.documents_processed = idx
                        job_queue.update_job(job)
                        
                        logger.info(f"[Job {job_id}] Processing {file_info['filename']}")
                        
                        file_path = file_info['path']
                        if not os.path.exists(file_path):
                            results['errors'].append({'file': file_info['filename'], 'error': 'File not found'})
                            results['file_results'].append({
                                'filename': file_info['filename'],
                                'status': 'failed',
                                'error': 'File not found'
                            })
                            continue
                        
                        # Extract text
                        docs = document_loader.load_document(file_path)
                        document_content = "\n".join([doc.page_content for doc in docs])
                        
                        if not document_content.strip():
                            results['errors'].append({'file': file_info['filename'], 'error': 'Empty document'})
                            results['file_results'].append({
                                'filename': file_info['filename'],
                                'status': 'empty',
                                'chunks': 0
                            })
                            continue
                        
                        # Apply chunking strategy
                        chunks = []

                        # Skip chunking if download_only mode
                        if process_mode == 'download_only':
                            logger.info(f"[Job {job_id}] Download-only mode - skipping chunking for {file_info['filename']}")
                            chunks = []
                        elif chunking_strategy == 'smart_chunking' and llm and prompt:
                            try:
                                # Prepare full prompt
                                full_prompt = f"{prompt}\n\n{document_content[:50000]}"

                                logger.info(f"[Job {job_id}] Calling LLM for chunking {file_info['filename']}...")
                                llm_response = llm.invoke(full_prompt)
                                
                                # Extract content from LLM response (handle both direct content and chat completion structures)
                                response_content = None
                                if hasattr(llm_response, 'content') and llm_response.content:
                                    response_content = llm_response.content
                                elif hasattr(llm_response, 'choices') and llm_response.choices:
                                    # Chat completion format (LM Studio, OpenAI, etc.)
                                    response_content = llm_response.choices[0].message.content
                                else:
                                    response_content = str(llm_response)

                                # Parse JSON from response - handle markdown code blocks
                                json_match = re.search(r'\{[\s\S]*\}', response_content)
                                if json_match:
                                    json_str = json_match.group(0)
                                    # Remove markdown code block markers if present
                                    json_str = re.sub(r'^```json\s*|\s*```$', '', json_str.strip())
                                    chunking_result = json.loads(json_str)
                                    chunks_data = chunking_result.get('chunks', [])
                                    chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
                                    logger.info(f"[Job {job_id}] LLM generated {len(chunks)} chunks for {file_info['filename']}")
                                else:
                                    logger.error(f"[Job {job_id}] No JSON found in LLM response")
                                    raise ValueError("No JSON in LLM response")

                            except Exception as llm_error:
                                logger.error(f"[Job {job_id}] LLM chunking failed: {llm_error}")
                                import traceback
                                logger.error(traceback.format_exc())
                                # Fallback to simple chunking
                                chunks = document_content.split('\n\n')
                                chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                        else:
                            # Simple chunking
                            chunks = document_content.split('\n\n')
                            chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                        
                        # Ingest chunks if requested
                        if ingest_chunks and vector_store:
                            lc_docs = []
                            for i, chunk in enumerate(chunks):
                                if not chunk.strip():
                                    continue
                                lc_docs.append(Document(
                                    page_content=chunk,
                                    metadata={
                                        'source': f'upload:{file_info["original_filename"]}',
                                        'chunk_id': i,
                                        'chunking_strategy': chunking_strategy,
                                        'process_mode': process_mode,
                                        'document_summary': document_summary if i == 0 else '',  # Store on first chunk
                                        'key_entities': key_entities if i == 0 else []  # Store on first chunk
                                    }
                                ))
                            if lc_docs:
                                vector_store.add_documents(lc_docs)
                                logger.info(f"[Job {job_id}] Added {len(lc_docs)} chunks to vector store")

                        # Save to Document Store if download_only mode
                        if process_mode == 'download_only':
                            docstore_dir = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_{job_id}/documents"
                            os.makedirs(docstore_dir, exist_ok=True)
                            
                            # Copy file to Document Store
                            import shutil
                            dest_path = os.path.join(docstore_dir, file_info['original_filename'])
                            shutil.copy2(file_info['path'], dest_path)
                            logger.info(f"[Job {job_id}] Saved {file_info['original_filename']} to Document Store")
                            
                            results['document_results'].append({
                                'filename': file_info['original_filename'],
                                'status': 'saved_to_store',
                                'chunks': 0,
                                'path': dest_path
                            })
                        else:
                            results['document_results'].append({
                                'filename': file_info['original_filename'],
                                'status': 'success',
                                'chunks': len(chunks)
                            })
                        
                        results['documents_processed'] += 1
                        results['total_chunks'] += len(chunks)
                        results['file_results'].append({
                            'filename': file_info['original_filename'],
                            'status': 'saved_to_store' if process_mode == 'download_only' else 'success',
                            'chunks': 0 if process_mode == 'download_only' else len(chunks)
                        })
                        
                    except Exception as e:
                        logger.error(f"[Job {job_id}] Error processing {file_info['filename']}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        results['errors'].append({'file': file_info['filename'], 'error': str(e)})
                        results['file_results'].append({
                            'filename': file_info['filename'],
                            'status': 'error',
                            'error': str(e)
                        })
                
                # Clean up temp directory
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception as cleanup_error:
                        logger.error(f"Failed to clean up temp dir: {cleanup_error}")
                
                # Mark job as completed
                job.progress = 100
                job.current_stage = "completed"
                job.documents_processed = results['documents_processed']
                job.chunks_generated = results['total_chunks']
                job.result = results
                job_queue.update_job(job)
                
                logger.info(f"[Job {job_id}] File ingestion completed: {results['documents_processed']} documents, {results['total_chunks']} chunks")
                
            except Exception as e:
                logger.error(f"[Job {job_id}] File ingest worker error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                job.status = 'failed'
                job.error = str(e)
                job_queue.update_job(job)
        
        job_queue.start_worker(job.job_id, process_files_background)
        
        logger.info(f"Created file ingest job {job.job_id} for user {current_user_id}")
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'files_count': len(saved_files),
            'message': f'File ingestion job created for {len(saved_files)} file(s)',
            'check_status_url': f'/jobs/{job.job_id}'
        }), 202
        
    except Exception as e:
        logger.error(f"Smart ingest files error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Smart ingestion failed: {str(e)}'}), 500


# Web Page Scanning endpoint
@app.route('/api/rag/scan_webpage', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def scan_webpage(current_user_id):
    """
    Scan a web page for document links (PDF, DOCX, TXT, HTML, MD)
    Returns list of document URLs found on the page
    """
    try:
        from .smart_ingestion_enhanced import extract_document_links_from_page
        import requests
        
        data = request.get_json()
        
        # Validate input
        schema = {
            'url': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 2048,
                'sanitize': True
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        page_url = data.get('url')
        
        # Fetch the web page
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AI Agent RAG Bot/1.0; +https://example.com/bot)'
        }
        
        logger.info(f"Scanning web page for documents: {page_url}")
        response = requests.get(page_url, headers=headers, timeout=30, verify=True)
        response.raise_for_status()
        
        # Extract document links
        document_urls = extract_document_links_from_page(page_url, response.text)
        
        logger.info(f"Found {len(document_urls)} document links on {page_url}")
        
        return jsonify({
            'documents': document_urls,
            'count': len(document_urls),
            'page_url': page_url
        }), 200
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching web page: {page_url}")
        return jsonify({'error': 'Timeout fetching web page. The server took too long to respond.'}), 408
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch web page: {str(e)}")
        return jsonify({'error': f'Failed to fetch web page: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Scan webpage error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500


# Smart Ingestion from Web Page endpoint - ASYNC
@app.route('/api/rag/smart_ingest_webpage', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def smart_ingest_webpage(current_user_id):
    """
    Smart ingestion from web page - ASYNC - creates background job
    Scans web page for documents, then processes them in background
    """
    try:
        from .smart_ingestion_enhanced import extract_document_links_from_page
        import requests
        
        data = request.get_json()
        page_url = data.get('url')
        
        if not page_url:
            return jsonify({'error': 'Web page URL is required'}), 400
        
        # Get processing parameters
        chunking_strategy = data.get('chunking_strategy', 'smart_chunking')
        ingest_chunks = data.get('ingest_chunks', True)
        process_mode = data.get('process_mode', 'vector_db')
        custom_prompt = data.get('custom_prompt', '')
        document_urls = data.get('document_urls', [])  # Pre-scanned URLs
        
        # If no document_urls provided, scan the page now
        if not document_urls:
            logger.info(f"Scanning web page for documents: {page_url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AI Agent RAG Bot/1.0; +https://example.com/bot)'
            }
            response = requests.get(page_url, headers=headers, timeout=30, verify=True)
            response.raise_for_status()
            document_urls = extract_document_links_from_page(page_url, response.text)
            
            if not document_urls:
                return jsonify({'error': 'No document links found on the page'}), 404
            
            logger.info(f"Found {len(document_urls)} document URLs")
        
        # Use default smart chunking prompt if not provided
        if not custom_prompt:
            from .smart_ingestion_enhanced import DEFAULT_SMART_CHUNKING_PROMPT
            custom_prompt = DEFAULT_SMART_CHUNKING_PROMPT
        
        # Create background job with configuration tracking
        from .job_queue import job_queue
        
        job = job_queue.create_job(
            user_id=current_user_id,
            job_type='smart_ingest_webpage',
            parameters={
                'page_url': page_url,
                'document_urls': document_urls,
                'chunking_strategy': chunking_strategy,
                'ingest_chunks': ingest_chunks,
                'process_mode': process_mode,
                'prompt': custom_prompt,
                'total_documents': len(document_urls)
            },
            ingestion_mode='webpage',
            processing_mode=process_mode,
            chunking_strategy=chunking_strategy,
            source_url=page_url,
            document_urls=document_urls
        )
        
        # Start background worker
        def process_webpage_background(job):
            """Background processing function for web page documents"""
            from .job_queue import job_queue
            from rag_component.document_loader import DocumentLoader
            from rag_component.vector_store_manager import VectorStoreManager
            from langchain_core.documents import Document
            from models.response_generator import ResponseGenerator
            import tempfile
            import os
            import re
            import requests
            
            try:
                job_id = job.job_id
                doc_urls = job.document_urls or job.parameters.get('document_urls', [])
                chunking_strategy = job.chunking_strategy
                ingest_chunks = job.parameters.get('ingest_chunks', True)
                process_mode = job.processing_mode
                prompt = job.parameters.get('prompt', '')
                total_documents = len(doc_urls)

                document_loader = DocumentLoader()
                vector_store = VectorStoreManager() if ingest_chunks and process_mode != 'download_only' else None

                results = {
                    'documents_processed': 0,
                    'total_chunks': 0,
                    'errors': [],
                    'document_results': []
                }

                # If download_only mode, download and save to Document Store
                if process_mode == 'download_only':
                    logger.info(f"[Job {job_id}] Download-only mode - saving to Document Store")

                    # Create document store directory for this job with source info
                    # Extract source domain from first URL for folder naming
                    source_domain = "unknown"
                    if doc_urls:
                        from urllib.parse import urlparse
                        parsed = urlparse(doc_urls[0])
                        source_domain = parsed.netloc.replace('.', '_')
                    
                    docstore_dir = f"/root/qwen/ai_agent/document-store-mcp-server/data/ingested/job_{job_id}_{source_domain}/documents"
                    os.makedirs(docstore_dir, exist_ok=True)

                    # Create metadata file to track source
                    metadata_file = os.path.join(docstore_dir, ".source_metadata.json")
                    import json
                    with open(metadata_file, 'w') as f:
                        json.dump({
                            'job_id': job_id,
                            'source_urls': doc_urls,
                            'downloaded_at': datetime.utcnow().isoformat(),
                            'process_mode': 'download_only'
                        }, f, indent=2)

                    for idx, doc_url in enumerate(doc_urls):
                        try:
                            job.progress = int((idx / total_documents) * 100) if total_documents > 0 else 0
                            job.current_stage = f"Downloading document {idx + 1}/{total_documents}"
                            job.documents_processed = idx
                            job_queue.update_job(job)

                            # Download document
                            download_response = requests.get(doc_url, timeout=60)
                            download_response.raise_for_status()

                            # Extract filename - try multiple methods in order of preference
                            from urllib.parse import urlparse, unquote
                            parsed_url = urlparse(doc_url)
                            
                            # Method 1: Check Content-Disposition header (most reliable)
                            filename = None
                            content_disposition = download_response.headers.get('content-disposition', '')
                            if content_disposition:
                                # Parse: attachment; filename="gost-r-34-10-2012.pdf"
                                import re
                                filename_match = re.findall('filename[^;=\n]*=["\']?([^"\';\n]*)', content_disposition)
                                if filename_match:
                                    filename = unquote(filename_match[0])
                                    logger.info(f"[Job {job_id}] Got filename from Content-Disposition: {filename}")
                            
                            # Method 2: Try to get filename from URL path
                            if not filename:
                                filename = os.path.basename(unquote(parsed_url.path))
                                logger.info(f"[Job {job_id}] Got filename from URL path: {filename}")
                            
                            # Method 3: Generate filename with source info
                            if not filename or filename == '' or filename == '/' or len(filename) < 4:
                                # Try to get meaningful part from URL
                                path_parts = parsed_url.path.strip('/').split('/')
                                # Look for parts that look like filenames (contain dots or are long)
                                for part in reversed(path_parts):
                                    if '.' in part and len(part) > 3:
                                        filename = unquote(part)
                                        break
                                
                                if not filename or len(filename) < 4:
                                    filename = f"doc_{source_domain}_{idx:03d}.pdf"
                                logger.info(f"[Job {job_id}] Generated filename: {filename}")
                            
                            # Clean filename - remove query params, special chars, timestamps that look like IDs
                            filename = filename.split('?')[0]
                            filename = filename.replace('%20', '_').replace(' ', '_')
                            
                            # Remove timestamp-like prefixes (e.g., "1699366818935-gost-r-34.pdf" → "gost-r-34.pdf")
                            timestamp_pattern = r'^\d{10,13}[-_]?'
                            filename = re.sub(timestamp_pattern, '', filename)
                            
                            # Ensure we have an extension
                            if not os.path.splitext(filename)[1]:
                                # Try to detect from content type
                                content_type = download_response.headers.get('content-type', '')
                                if 'pdf' in content_type:
                                    filename += '.pdf'
                                elif 'html' in content_type:
                                    filename += '.html'
                                elif 'text' in content_type:
                                    filename += '.txt'
                                else:
                                    filename += '.pdf'  # Default to PDF
                            
                            # Sanitize filename - remove any remaining problematic characters
                            filename = re.sub(r'[<>:"|?*]', '_', filename)
                            
                            # Make filename unique if it already exists
                            save_path = os.path.join(docstore_dir, filename)
                            if os.path.exists(save_path):
                                base, ext = os.path.splitext(filename)
                                counter = 1
                                while os.path.exists(f"{base}_{counter}{ext}"):
                                    counter += 1
                                filename = f"{base}_{counter}{ext}"
                                save_path = os.path.join(docstore_dir, filename)

                            # Save to Document Store
                            with open(save_path, 'wb') as f:
                                f.write(download_response.content)

                            logger.info(f"[Job {job_id}] Saved {filename} from {doc_url} to Document Store")
                            
                            # Save individual document metadata for Document Store MCP
                            import json
                            doc_metadata = {
                                'original_filename': filename,
                                'original_url': doc_url,
                                'source_website': source_domain,
                                'downloaded_at': datetime.utcnow().isoformat(),
                                'job_id': job_id,
                                'process_mode': 'download_only',
                                'content_type': download_response.headers.get('content-type', 'application/pdf')
                            }
                            metadata_path = os.path.join(docstore_dir, f"{os.path.splitext(filename)[0]}.metadata.json")
                            with open(metadata_path, 'w') as f:
                                json.dump(doc_metadata, f, indent=2)

                            results['documents_processed'] += 1
                            results['document_results'].append({
                                'url': doc_url,
                                'status': 'saved_to_store',
                                'chunks': 0,
                                'filename': filename,
                                'original_url': doc_url,
                                'source_domain': source_domain,
                                'path': save_path
                            })
                        except Exception as download_error:
                            logger.error(f"[Job {job_id}] Download failed for {doc_url}: {download_error}")
                            results['errors'].append({'url': doc_url, 'error': str(download_error)})
                            results['document_results'].append({
                                'url': doc_url,
                                'status': 'failed',
                                'error': str(download_error)
                            })

                    # Mark job as completed
                    job.progress = 100
                    job.current_stage = f"completed (saved to Document Store from {source_domain})"
                    job.documents_processed = results['documents_processed']
                    job.chunks_generated = 0
                    job.result = results
                    job_queue.update_job(job)

                    logger.info(f"[Job {job_id}] Download-only completed: {results['documents_processed']} documents saved to Document Store")
                    return  # Exit early - no processing needed
                
                for idx, doc_url in enumerate(doc_urls):
                    try:
                        # Update job progress
                        job.progress = int((idx / total_documents) * 100) if total_documents > 0 else 0
                        job.current_stage = f"Processing document {idx + 1}/{total_documents}"
                        job.documents_processed = idx
                        job_queue.update_job(job)
                        
                        logger.info(f"[Job {job_id}] Processing {doc_url}")
                        
                        # Download document
                        temp_path = None
                        try:
                            download_response = requests.get(doc_url, timeout=60)
                            download_response.raise_for_status()
                            
                            # Create temp file
                            file_ext = os.path.splitext(doc_url.split('?')[0])[1].lower()
                            if not file_ext:
                                file_ext = '.pdf'  # Default to PDF
                            
                            temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext)
                            os.close(temp_fd)
                            
                            with open(temp_path, 'wb') as f:
                                f.write(download_response.content)
                            
                            logger.info(f"[Job {job_id}] Downloaded {doc_url} to {temp_path}")
                            
                        except Exception as download_error:
                            logger.error(f"[Job {job_id}] Download failed for {doc_url}: {download_error}")
                            results['errors'].append({'url': doc_url, 'error': str(download_error)})
                            results['document_results'].append({
                                'url': doc_url,
                                'status': 'failed',
                                'error': str(download_error)
                            })
                            continue
                        
                        # Extract text
                        docs = document_loader.load_document(temp_path)
                        document_content = "\n".join([doc.page_content for doc in docs])
                        
                        if not document_content.strip():
                            results['errors'].append({'url': doc_url, 'error': 'Empty document'})
                            results['document_results'].append({
                                'url': doc_url,
                                'status': 'empty',
                                'chunks': 0
                            })
                            if temp_path and os.path.exists(temp_path):
                                os.remove(temp_path)
                            continue
                        
                        # Apply chunking strategy
                        chunks = []
                        
                        if chunking_strategy == 'smart_chunking' and prompt:
                            try:
                                # Get LLM instance
                                response_gen = ResponseGenerator()
                                llm = response_gen._get_llm_instance(
                                    provider=RESPONSE_LLM_PROVIDER,
                                    model=RESPONSE_LLM_MODEL
                                )
                                
                                # Prepare full prompt
                                full_prompt = f"{prompt}\n\n{document_content[:50000]}"  # Limit content
                                
                                logger.info(f"[Job {job_id}] Calling LLM for chunking...")
                                llm_response = llm.invoke(full_prompt)
                                response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
                                
                                # Parse JSON from response
                                json_match = re.search(r'\{[\s\S]*\}', response_content)
                                chunking_result = json.loads(json_match.group(0) if json_match else response_content)
                                chunks_data = chunking_result.get('chunks', [])
                                
                                # Extract content from chunks
                                chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
                                logger.info(f"[Job {job_id}] LLM generated {len(chunks)} chunks")
                                
                            except Exception as llm_error:
                                logger.error(f"[Job {job_id}] LLM chunking failed: {llm_error}")
                                # Fallback to simple chunking
                                chunks = document_content.split('\n\n')
                                chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                                logger.info(f"[Job {job_id}] Fallback simple chunking generated {len(chunks)} chunks")
                        else:
                            # Simple chunking
                            chunks = document_content.split('\n\n')
                            chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                        
                        # Ingest chunks if requested
                        if ingest_chunks and vector_store:
                            lc_docs = []
                            for i, chunk in enumerate(chunks):
                                if not chunk.strip():
                                    continue
                                lc_docs.append(Document(
                                    page_content=chunk,
                                    metadata={
                                        'source': f'webpage:{page_url}:{doc_url}',
                                        'chunk_id': i,
                                        'chunking_strategy': chunking_strategy,
                                        'process_mode': process_mode
                                    }
                                ))
                            if lc_docs:
                                vector_store.add_documents(lc_docs)
                                logger.info(f"[Job {job_id}] Added {len(lc_docs)} chunks to vector store")
                                
                                # If hybrid mode, also store in Neo4j (future enhancement)
                                if process_mode == 'hybrid':
                                    logger.info(f"[Job {job_id}] Hybrid mode selected - Neo4j integration pending")
                        
                        results['documents_processed'] += 1
                        results['total_chunks'] += len(chunks)
                        results['document_results'].append({
                            'url': doc_url,
                            'status': 'success',
                            'chunks': len(chunks)
                        })
                        
                        # Clean up temp file
                        if temp_path and os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                    except Exception as e:
                        logger.error(f"[Job {job_id}] Error processing {doc_url}: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        results['errors'].append({'url': doc_url, 'error': str(e)})
                        results['document_results'].append({
                            'url': doc_url,
                            'status': 'error',
                            'error': str(e)
                        })
                
                # Mark job as completed
                job.progress = 100
                job.current_stage = "completed"
                job.documents_processed = results['documents_processed']
                job.chunks_generated = results['total_chunks']
                job.result = results
                job_queue.update_job(job)
                
                logger.info(f"[Job {job_id}] Web page ingestion completed: {results['documents_processed']} documents, {results['total_chunks']} chunks")
                
            except Exception as e:
                logger.error(f"[Job {job_id}] Web page ingest worker error: {e}")
                import traceback
                logger.error(traceback.format_exc())
                job.status = 'failed'
                job.error = str(e)
                job_queue.update_job(job)
        
        job_queue.start_worker(job.job_id, process_webpage_background)
        
        logger.info(f"Created web page ingest job {job.job_id} for user {current_user_id}")
        
        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'documents_found': len(document_urls),
            'message': f'Web page ingestion job created for {len(document_urls)} documents',
            'check_status_url': f'/jobs/{job.job_id}'
        }), 202
        
    except Exception as e:
        logger.error(f"Smart ingest webpage error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Smart ingestion failed: {str(e)}'}), 500


# Smart Ingestion from Document Store endpoint - ASYNC
@app.route('/api/rag/smart_ingest_docstore', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def smart_ingest_docstore(current_user_id):
    """
    Smart ingestion from Document Store - ASYNC - creates background job
    """
    try:
        data = request.get_json()
        documents = data.get('documents', [])

        if not documents:
            return jsonify({'error': 'No documents specified'}), 400

        from .job_queue import job_queue, JobStatus

        chunking_strategy = data.get('chunking_strategy', 'smart_chunking')
        ingest_chunks = data.get('ingest_chunks', True)
        process_mode = data.get('process_mode', 'vector_db')

        # Create background job with configuration tracking
        job = job_queue.create_job(
            user_id=current_user_id,
            job_type='smart_ingest_docstore',
            parameters={
                'documents': documents,
                'chunking_strategy': chunking_strategy,
                'ingest_chunks': ingest_chunks,
                'process_mode': process_mode,
                'total_documents': len(documents)
            },
            ingestion_mode='docstore',
            processing_mode=process_mode,
            chunking_strategy=chunking_strategy
        )

        # Start background worker
        job_queue.start_worker(job.job_id, _process_smart_ingest_docstore)

        logger.info(f"Created smart ingest job {job.job_id} for user {current_user_id}")

        return jsonify({
            'job_id': job.job_id,
            'status': job.status,
            'message': 'Smart ingestion job created. Processing in background.',
            'check_status_url': f'/jobs/{job.job_id}'
        }), 202

    except Exception as e:
        logger.error(f"Smart ingest docstore error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Smart ingestion failed: {str(e)}'}), 500


def _process_smart_ingest_docstore(job):
    """
    Background worker for smart ingestion from Document Store
    """
    from .job_queue import job_queue
    from .document_store_client import document_store_client
    from rag_component.document_loader import DocumentLoader
    from rag_component.vector_store_manager import VectorStoreManager
    from langchain_core.documents import Document
    from models.response_generator import ResponseGenerator
    
    try:
        job_id = job.job_id
        documents = job.parameters.get('documents', [])
        chunking_strategy = job.parameters.get('chunking_strategy', 'smart_chunking')
        ingest_chunks = job.parameters.get('ingest_chunks', True)
        total_documents = len(documents)
        
        document_loader = DocumentLoader()
        vector_store = VectorStoreManager() if ingest_chunks else None
        
        results = {
            'documents_processed': 0,
            'total_chunks': 0,
            'errors': []
        }
        
        for idx, doc_ref in enumerate(documents):
            try:
                # Update job progress
                job.progress = int((idx / total_documents) * 100)
                job.current_stage = f"Processing document {idx + 1}/{total_documents}"
                job.documents_processed = idx
                job_queue.update_job(job)
                
                doc_id = doc_ref.get('doc_id')
                job_id_param = doc_ref.get('job_id')
                
                if not job_id_param or not doc_id:
                    results['errors'].append({'doc_id': doc_id, 'error': 'Missing job_id or doc_id'})
                    continue
                
                logger.info(f"[Job {job_id}] Processing {doc_id} from {job_id_param}")
                
                # Get document from Document Store as PDF
                doc_result = document_store_client.get_document(job_id_param, doc_id, format='pdf')
                
                if not doc_result.get('success'):
                    results['errors'].append({'doc_id': doc_id, 'error': 'Failed to get document'})
                    continue
                
                # Get the PDF content - handle nested structure
                result_data = doc_result.get('result', {})
                pdf_data = result_data.get('content', '')
                
                # Handle case where content is itself a dict with 'content' field
                if isinstance(pdf_data, dict):
                    pdf_data = pdf_data.get('content', '')
                
                if not pdf_data:
                    results['errors'].append({'doc_id': doc_id, 'error': 'Empty document'})
                    continue
                
                # Save PDF to temp file and extract text
                import tempfile
                import base64
                import os
                
                temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
                os.close(temp_fd)
                
                # Decode base64 PDF data
                if isinstance(pdf_data, str) and pdf_data.startswith('JVBER'):
                    with open(temp_path, 'wb') as f:
                        f.write(base64.b64decode(pdf_data))
                else:
                    results['errors'].append({'doc_id': doc_id, 'error': 'Unsupported PDF format'})
                    continue
                
                # Extract text using document loader
                docs = document_loader.load_document(temp_path)
                document_content = "\n".join([doc.page_content for doc in docs])
                os.remove(temp_path)
                
                if not document_content.strip():
                    results['errors'].append({'doc_id': doc_id, 'error': 'Could not extract text from PDF'})
                    continue
                
                # Use LLM-based smart chunking if requested
                chunks = []
                document_summary = ""
                key_entities = []
                
                if chunking_strategy == 'smart_chunking':
                    try:
                        response_gen = ResponseGenerator()
                        llm = response_gen._get_llm_instance(
                            provider=RESPONSE_LLM_PROVIDER,
                            model=RESPONSE_LLM_MODEL
                        )

                        # Qwen 3.5 35B has 262k context window - can handle most docs in single call
                        # Threshold: 800k chars ≈ 200k tokens (leaves room for prompt + output)
                        MAX_SINGLE_CALL = 800000  # chars
                        
                        if len(document_content) > MAX_SINGLE_CALL:
                            # VERY LARGE DOCUMENT (> 800k chars, ~200k tokens)
                            # Split into sections with Context Summary for coherence
                            logger.info(f"[Job {job_id}] Large document ({len(document_content)} chars), splitting into sections")
                            
                            MAX_SECTION_SIZE = 700000  # ~175k tokens per section
                            sections = []
                            remaining = document_content
                            
                            while len(remaining) > MAX_SECTION_SIZE:
                                # Split at paragraph boundary
                                cut_point = remaining.rfind('\n\n', 0, MAX_SECTION_SIZE)
                                if cut_point == -1:
                                    cut_point = MAX_SECTION_SIZE
                                sections.append(remaining[:cut_point])
                                remaining = remaining[cut_point:].lstrip()
                            
                            if remaining:
                                sections.append(remaining)
                            
                            logger.info(f"[Job {job_id}] Split into {len(sections)} sections for LLM chunking")
                            
                            # Process each section with Context Summary handoff
                            all_chunks = []
                            previous_summary = ""
                            previous_entities = []
                            
                            for section_idx, section in enumerate(sections):
                                logger.info(f"[Job {job_id}] Processing section {section_idx + 1}/{len(sections)} ({len(section)} chars)")
                                
                                # Build context header for sections 2+
                                if previous_summary:
                                    context_header = f"""
## Context from Previous Section

**Summary:** {previous_summary}

**Key Entities:** {', '.join(previous_entities)}

Continue chunking with this context in mind. Maintain semantic continuity with adjacent sections.
"""
                                else:
                                    context_header = ""
                                
                                # Build prompt with document context
                                section_prompt = f"""# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards for vector database ingestion.

## CORE PRINCIPLES
1. PRESERVE SEMANTIC UNITS: Never split complete concepts
2. TARGET SIZE: 200-450 tokens per chunk
3. MINIMAL OVERLAP: Apply overlap ONLY at procedural boundaries to preserve algorithmic continuity
4. CONTEXT ANCHORING: Always include section headers/subheaders

## OUTPUT FORMAT
Return ONLY valid JSON with these fields:
{{
  "document": "document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number or appendix_X",
      "title": "descriptive title in language of document",
      "chunk_type": "one of: header_and_scope | references_and_definitions | formula_with_context | testing_procedure | appendix_example",
      "contains_formula": boolean,
      "contains_table": boolean,
      "content": "chunk text here",
      "token_count": integer (200-450 tokens per chunk)
    }}
  ],
  "document_summary": "2-3 sentences summarizing what this section covers for graph context",
  "key_entities": ["important entities from this section for graph context (standards, organizations, technologies, etc.)"]
}}

{context_header}

## Document: {doc_id}
## Section {section_idx + 1} of {len(sections)}

{section}
"""
                                
                                llm_response = llm.invoke(section_prompt)
                                response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
                                
                                # Parse JSON from response
                                import json
                                json_match = re.search(r'\{[\s\S]*\}', response_content)
                                chunking_result = json.loads(json_match.group(0) if json_match else response_content)
                                chunks_data = chunking_result.get('chunks', [])
                                
                                section_chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
                                all_chunks.extend(section_chunks)
                                
                                # Save context for next section
                                previous_summary = chunking_result.get('document_summary', '')
                                previous_entities = chunking_result.get('key_entities', [])
                                
                                logger.info(f"[Job {job_id}] Section {section_idx + 1}: LLM generated {len(section_chunks)} chunks")
                            
                            chunks = all_chunks
                            
                            # Use last section's summary and entities (or merge all)
                            document_summary = previous_summary
                            key_entities = previous_entities
                            
                            logger.info(f"[Job {job_id}] Total: LLM generated {len(chunks)} chunks from {len(sections)} sections for {doc_id}")
                            
                        else:
                            # MOST DOCUMENTS (97%): Single LLM call with full document context
                            logger.info(f"[Job {job_id}] Document fits in single LLM call ({len(document_content)} chars)")
                            
                            # Build prompt for single-call processing
                            single_prompt = f"""# ROLE
You are an expert document engineer specializing in semantic chunking of technical standards for vector database ingestion.

## CORE PRINCIPLES
1. PRESERVE SEMANTIC UNITS: Never split complete concepts
2. TARGET SIZE: 200-450 tokens per chunk
3. MINIMAL OVERLAP: Apply overlap ONLY at procedural boundaries to preserve algorithmic continuity
4. CONTEXT ANCHORING: Always include section headers/subheaders

## OUTPUT FORMAT
Return ONLY valid JSON with these fields:
{{
  "document": "document identifier (e.g., GOST_R_XXXXX-YYYY)",
  "total_chunks": integer,
  "chunks": [
    {{
      "chunk_id": 1,
      "section": "section number or appendix_X",
      "title": "descriptive title in language of document",
      "chunk_type": "one of: header_and_scope | references_and_definitions | formula_with_context | testing_procedure | appendix_example",
      "contains_formula": boolean,
      "contains_table": boolean,
      "content": "chunk text here",
      "token_count": integer (200-450 tokens per chunk)
    }}
  ],
  "document_summary": "2-3 sentences summarizing document content for graph context",
  "key_entities": ["important entities from document for graph context (standards, organizations, technologies, dates, concepts)"]
}}

## Document: {doc_id}

{document_content}
"""
                            
                            llm_response = llm.invoke(single_prompt)
                            response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
                            
                            # Parse JSON from response
                            import json
                            json_match = re.search(r'\{[\s\S]*\}', response_content)
                            chunking_result = json.loads(json_match.group(0) if json_match else response_content)
                            chunks_data = chunking_result.get('chunks', [])
                            
                            chunks = [c.get('content', '') for c in chunks_data if c.get('content')]
                            
                            # Store document-level metadata for graph context
                            document_summary = chunking_result.get('document_summary', '')
                            key_entities = chunking_result.get('key_entities', [])
                            
                            logger.info(f"[Job {job_id}] Single-call LLM generated {len(chunks)} chunks for {doc_id}")
                            if document_summary:
                                logger.info(f"[Job {job_id}] Document summary: {document_summary[:100]}...")
                            if key_entities:
                                logger.info(f"[Job {job_id}] Key entities: {len(key_entities)} entities extracted")

                    except Exception as chunk_error:
                        logger.error(f"[Job {job_id}] LLM chunking failed for {doc_id}: {chunk_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Fallback to simple chunking
                        chunks = document_content.split('\n\n')
                        chunks = [c.strip() for c in chunks if len(c.strip()) > 100]
                        logger.info(f"[Job {job_id}] Fallback simple chunking generated {len(chunks)} chunks")
                else:
                    # Simple chunking
                    chunks = document_content.split('\n\n')
                    chunks = [c.strip() for c in chunks if len(c.strip()) > 100]

                if ingest_chunks and vector_store:
                    lc_docs = []
                    for i, chunk in enumerate(chunks):
                        if not chunk.strip():
                            continue
                        lc_docs.append(Document(
                            page_content=chunk,
                            metadata={
                                'source': f'docstore:{job_id_param}:{doc_id}',
                                'chunk_id': i,
                                'chunking_strategy': chunking_strategy,
                                'document_summary': document_summary if i == 0 else '',  # Store on first chunk
                                'key_entities': key_entities if i == 0 else []  # Store on first chunk
                            }
                        ))
                    if lc_docs:
                        vector_store.add_documents(lc_docs)
                        logger.info(f"[Job {job_id}] Added {len(lc_docs)} chunks to vector store for {doc_id}")
                        
                        # If hybrid mode, also store in Neo4j
                        if job.parameters.get('process_mode') == 'hybrid':
                            try:
                                from .neo4j_integration import get_neo4j_connection
                                from .smart_ingestion_enhanced import process_hybrid_mode

                                neo4j = get_neo4j_connection()
                                if neo4j and neo4j.connected:
                                    # Convert chunks to dict format for Neo4j
                                    chunk_dicts = []
                                    for i, chunk in enumerate(chunks):
                                        if chunk.strip():
                                            chunk_dicts.append({
                                                'chunk_id': i,
                                                'content': chunk,
                                                'section': '',
                                                'title': '',
                                                'chunk_type': 'document_chunk'
                                            })

                                    # Get user_id from job metadata (background job doesn't have current_user_id)
                                    job_user_id = job.user_id or 'unknown'

                                    # Store in Neo4j
                                    graph_result = process_hybrid_mode(
                                        chunks=chunk_dicts,
                                        doc_id=f"docstore_{job_id_param}_{doc_id}",
                                        filename=doc_id,
                                        metadata={
                                            'user_id': job_user_id,
                                            'job_id': job_id,
                                            'document_summary': document_summary,
                                            'key_entities': key_entities
                                        }
                                    )

                                    logger.info(f"[Job {job_id}] Hybrid mode: stored in Neo4j")
                                else:
                                    logger.warning(f"[Job {job_id}] Neo4j not connected - skipping graph storage")
                            except Exception as graph_error:
                                logger.error(f"[Job {job_id}] Neo4j storage failed: {graph_error}")
                                import traceback
                                logger.error(traceback.format_exc())

                results['documents_processed'] += 1
                results['total_chunks'] += len(chunks)
                
            except Exception as e:
                logger.error(f"[Job {job_id}] Error processing document {doc_ref}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                results['errors'].append({'doc_ref': str(doc_ref), 'error': str(e)})
        
        # Mark job as completed
        job.progress = 100
        job.current_stage = "completed"
        job.documents_processed = total_documents
        job.chunks_generated = results['total_chunks']
        job.result = results
        job_queue.update_job(job)

        logger.info(f"[Job {job_id}] Smart ingestion completed: {results['documents_processed']} documents, {results['total_chunks']} chunks")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Smart ingest docstore worker error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        job.status = 'failed'
        job.error = str(e)
        job_queue.update_job(job)


# Graph Knowledge Base Endpoints
@app.route('/api/rag/graph/search', methods=['POST'])
@require_permission(Permission.READ_RAG)
def graph_search(current_user_id):
    """
    Search the knowledge graph for entities and relationships.
    
    Request body:
    {
        "query": "search query",
        "entity_types": ["STANDARD", "TECHNOLOGY", ...],  // optional filter
        "limit": 20
    }
    """
    try:
        from .neo4j_integration import get_neo4j_connection
        
        data = request.get_json() or {}
        query = data.get('query', '')
        entity_types = data.get('entity_types', [])
        limit = data.get('limit', 20)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        neo4j = get_neo4j_connection()
        if not neo4j or not neo4j.connected:
            return jsonify({'error': 'Neo4j not available'}), 503
        
        with neo4j.driver.session() as session:
            # Search entities
            if entity_types:
                type_filter = "AND e.type IN $entity_types"
            else:
                type_filter = ""
            
            entity_query = f"""
                MATCH (e:Entity)
                WHERE e.name CONTAINS $query OR e.description CONTAINS $query
                {type_filter}
                RETURN e.name as name, e.type as type, e.relevance as relevance
                ORDER BY e.relevance DESC
                LIMIT $limit
            """
            
            result = session.run(
                entity_query,
                query=query,
                entity_types=entity_types,
                limit=limit
            )
            
            entities = [{'name': r['name'], 'type': r['type'], 'relevance': r['relevance']} for r in result]
            
            # Get relationships for found entities
            if entities:
                entity_names = [e['name'] for e in entities]
                rel_query = """
                    MATCH (source:Entity)-[r]-(target:Entity)
                    WHERE source.name IN $names OR target.name IN $names
                    RETURN source.name as source, target.name as target, type(r) as relationship
                    LIMIT 50
                """
                rel_result = session.run(rel_query, names=entity_names)
                relationships = [{'source': r['source'], 'target': r['target'], 'relationship': r['relationship']} for r in rel_result]
            else:
                relationships = []
            
            return jsonify({
                'entities': entities,
                'relationships': relationships,
                'total': len(entities)
            }), 200
            
    except Exception as e:
        logger.error(f"Graph search error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/graph/stats', methods=['GET'])
@require_permission(Permission.READ_RAG)
def graph_statistics(current_user_id):
    """Get statistics about the knowledge graph"""
    try:
        from .neo4j_integration import get_neo4j_connection
        
        neo4j = get_neo4j_connection()
        if not neo4j or not neo4j.connected:
            return jsonify({'error': 'Neo4j not available'}), 503
        
        with neo4j.driver.session() as session:
            # Count entities by type
            type_counts = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC
            """)
            entities_by_type = {r['type']: r['count'] for r in type_counts}
            
            # Total entities
            total = session.run("MATCH (e:Entity) RETURN count(e) as count").single()['count']
            
            # Total relationships
            rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            # Top entities
            top = session.run("""
                MATCH (e:Entity)
                OPTIONAL MATCH (e)--(other:Entity)
                WITH e, count(other) as connections
                RETURN e.name as name, e.type as type, connections
                ORDER BY connections DESC
                LIMIT 10
            """)
            top_entities = [{'name': r['name'], 'type': r['type'], 'connections': r['connections']} for r in top]
            
            return jsonify({
                'total_entities': total,
                'entities_by_type': entities_by_type,
                'total_relationships': rels,
                'top_entities': top_entities
            }), 200
            
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/graph/entity/<entity_name>', methods=['GET'])
@require_permission(Permission.READ_RAG)
def get_entity(current_user_id, entity_name: str):
    """Get a specific entity and its relationships"""
    try:
        from .neo4j_integration import get_neo4j_connection
        
        neo4j = get_neo4j_connection()
        if not neo4j or not neo4j.connected:
            return jsonify({'error': 'Neo4j not available'}), 503
        
        from urllib.parse import unquote
        entity_name = unquote(entity_name)
        
        with neo4j.driver.session() as session:
            # Get entity details
            entity = session.run("""
                MATCH (e:Entity {name: $name})
                RETURN e.name as name, e.type as type, e.relevance as relevance, e.updated_at as updated_at
            """, {'name': entity_name}).single()
            
            if not entity:
                return jsonify({'error': 'Entity not found'}), 404
            
            # Get relationships
            rels = session.run("""
                MATCH (e:Entity {name: $name})-[r]-(other:Entity)
                RETURN other.name as other_name, other.type as other_type, type(r) as relationship
            """, {'name': entity_name})
            
            relationships = [{'other_name': r['other_name'], 'other_type': r['other_type'], 'relationship': r['relationship']} for r in rels]
            
            return jsonify({
                'name': entity['name'],
                'type': entity['type'],
                'relevance': entity['relevance'],
                'updated_at': entity['updated_at'],
                'relationships': relationships
            }), 200
            
    except Exception as e:
        logger.error(f"Get entity error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/graph/visualize', methods=['POST'])
@require_permission(Permission.READ_RAG)
def graph_visualize(current_user_id):
    """
    Get graph data for visualization.
    
    Request body:
    {
        "entity_types": ["STANDARD", "ORGANIZATION", ...],  // optional filter
        "search_query": "search term",  // optional search in entity names
        "limit": 100  // max nodes to return
    }
    """
    try:
        from .neo4j_integration import get_neo4j_connection

        data = request.get_json() or {}
        entity_types = data.get('entity_types', [])
        search_query = data.get('search_query', '')
        limit = data.get('limit', 100)

        neo4j = get_neo4j_connection()
        if not neo4j or not neo4j.connected:
            return jsonify({'error': 'Neo4j not available'}), 503

        with neo4j.driver.session() as session:
            # Build query
            type_filter = ""
            params = {'limit': limit}
            
            if entity_types:
                type_filter = "AND e.type IN $entity_types"
                params['entity_types'] = entity_types
            
            search_filter = ""
            if search_query:
                search_filter = "AND (e.name CONTAINS $search_query OR e.description CONTAINS $search_query)"
                params['search_query'] = search_query
            
            # Get entities
            entity_query = f"""
                MATCH (e:Entity)
                WHERE true {type_filter} {search_filter}
                RETURN e.name as name, e.type as type, e.relevance as relevance, 
                       e.updated_at as updated_at
                ORDER BY e.relevance DESC
                LIMIT $limit
            """
            
            result = session.run(entity_query, **params)
            nodes = []
            node_names = set()
            entity_timestamps = {}  # Map entity name to timestamp for co-occurrence detection
            
            for r in result:
                nodes.append({
                    'id': r['name'],  # Use name as ID since we don't have elementId
                    'name': r['name'],
                    'type': r['type'],
                    'relevance': r['relevance'] or 0,
                    'updated_at': str(r['updated_at']) if r['updated_at'] else ''
                })
                node_names.add(r['name'])
                if r['updated_at']:
                    entity_timestamps[r['name']] = r['updated_at']
            
            # Get relationships - including both direct and co-occurrence based
            links = []
            
            if nodes:
                # First: Get any existing Entity-Entity relationships
                entity_rel_query = """
                    MATCH (source:Entity)-[r]-(target:Entity)
                    WHERE source.name IN $names AND target.name IN $names
                    RETURN source.name as source, target.name as target, type(r) as relationship
                    LIMIT 500
                """
                rel_result = session.run(entity_rel_query, names=list(node_names))
                for r in rel_result:
                    links.append({
                        'source': r['source'],
                        'target': r['target'],
                        'relationship': r['relationship']
                    })
                
                # Second: Create co-occurrence relationships based on timestamp proximity
                # Entities created within 2 seconds of each other likely came from same document
                cooccur_query = """
                    MATCH (e1:Entity), (e2:Entity)
                    WHERE e1.name IN $names AND e2.name IN $names
                    AND e1.name < e2.name  // Avoid duplicates
                    AND e1.type <> e2.type  // Different types more likely to be related
                    AND e1.updated_at IS NOT NULL AND e2.updated_at IS NOT NULL
                    AND abs(duration.between(e1.updated_at, e2.updated_at).seconds) < 2
                    RETURN e1.name as source, e2.name as target, 'CO_OCCUR' as relationship
                    LIMIT 500
                """
                cooccur_result = session.run(cooccur_query, names=list(node_names))
                for r in cooccur_result:
                    # Avoid duplicate links
                    link_exists = any(
                        (l['source'] == r['source'] and l['target'] == r['target']) or
                        (l['source'] == r['target'] and l['target'] == r['source'])
                        for l in links
                    )
                    if not link_exists:
                        links.append({
                            'source': r['source'],
                            'target': r['target'],
                            'relationship': r['relationship']
                        })
            
            # Count by type
            type_counts = {}
            for node in nodes:
                t = node['type']
                type_counts[t] = type_counts.get(t, 0) + 1
            type_counts['total'] = len(nodes)
            
            return jsonify({
                'nodes': nodes,
                'links': links,
                'type_counts': type_counts
            }), 200

    except Exception as e:
        logger.error(f"Graph visualize error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/graph/entity/connections', methods=['POST'])
@require_permission(Permission.READ_RAG)
def get_entity_connections(current_user_id):
    """
    Get connections for a specific entity.
    
    Request body:
    {
        "entity_name": "entity name",
        "entity_type": "STANDARD",
        "limit": 20
    }
    """
    try:
        from .neo4j_integration import get_neo4j_connection

        data = request.get_json() or {}
        entity_name = data.get('entity_name', '')
        entity_type = data.get('entity_type', '')
        limit = data.get('limit', 20)

        if not entity_name:
            return jsonify({'error': 'Entity name is required'}), 400

        neo4j = get_neo4j_connection()
        if not neo4j or not neo4j.connected:
            return jsonify({'error': 'Neo4j not available'}), 503

        with neo4j.driver.session() as session:
            # Get connected entities
            query = """
                MATCH (e:Entity {name: $name})-[r]-(other:Entity)
                RETURN other.name as target_name, other.type as target_type, type(r) as relationship,
                       other.relevance as relevance, other.document as document
                ORDER BY other.relevance DESC
                LIMIT $limit
            """
            
            result = session.run(query, name=entity_name, limit=limit)
            connections = []
            for r in result:
                connections.append({
                    'target_name': r['target_name'],
                    'target_type': r['target_type'],
                    'relationship': r['relationship'],
                    'relevance': r['relevance'],
                    'document': r['document']
                })
            
            return jsonify({
                'entity_name': entity_name,
                'entity_type': entity_type,
                'connections': connections,
                'total': len(connections)
            }), 200

    except Exception as e:
        logger.error(f"Get entity connections error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# NLP Data Scientist Endpoints
@app.route('/api/rag/nlp/extract_entities', methods=['POST'])
@require_permission(Permission.READ_RAG)
def nlp_extract_entities(current_user_id):
    """Extract entities from text using spaCy + patterns"""
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        from nlp_tools.entity_extractor import get_entity_extractor
        
        extractor = get_entity_extractor()
        entities = extractor.extract_all_entities(text)
        stats = extractor.get_entity_statistics(entities)
        
        return jsonify({
            'entities': entities,
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/nlp/extract_entities_llm', methods=['POST'])
@require_permission(Permission.READ_RAG)
def nlp_extract_entities_llm(current_user_id):
    """Extract entities from text using LLM"""
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        from nlp_tools.llm_entity_extractor import get_llm_entity_extractor
        
        extractor = get_llm_entity_extractor()
        result = extractor.extract_entities(text)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"LLM entity extraction error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/nlp/analyze_document', methods=['POST'])
@require_permission(Permission.READ_RAG)
def nlp_analyze_document(current_user_id):
    """Analyze document with entity extraction"""
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        from nlp_tools.entity_extractor import get_entity_extractor
        
        extractor = get_entity_extractor()
        analysis = extractor.analyze_document(text)
        
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Document analysis error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/rag/nlp/extract_standards', methods=['POST'])
@require_permission(Permission.READ_RAG)
def nlp_extract_standards(current_user_id):
    """Extract technical standards from text"""
    try:
        data = request.get_json() or {}
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        from nlp_tools.entity_extractor import get_entity_extractor
        
        extractor = get_entity_extractor()
        standards = extractor.extract_standards_pattern(text)
        
        return jsonify({
            'standards': standards,
            'count': len(standards)
        }), 200
        
    except Exception as e:
        logger.error(f"Standards extraction error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Get port from environment variable or default to 5003
    port = int(os.getenv('RAG_SERVICE_PORT', 5003))

    # Check if running in production mode
    if os.getenv('FLASK_ENV') == 'production':
        try:
            # Production: Use Gunicorn programmatically
            from gunicorn.app.base import BaseApplication

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super(StandaloneApplication, self).__init__()

                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                'bind': f'0.0.0.0:{port}',
                'workers': 4,
                'worker_class': 'sync',
                'timeout': 43200,  # 12 hours to accommodate long-running requests
                'keepalive': 10,
                'max_requests': 1000,
                'max_requests_jitter': 100,
                'preload_app': True,
                'accesslog': '-',
                'errorlog': '-',
            }
            StandaloneApplication(app, options).run()
        except Exception as e:
            print(f"Gunicorn error: {type(e).__name__}: {e}")
            print("Running in development mode instead...")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development: Use Flask's built-in server
        app.run(host='0.0.0.0', port=port, debug=False)