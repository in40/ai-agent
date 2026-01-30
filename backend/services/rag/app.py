"""
RAG Service for AI Agent System
Handles document processing and retrieval
"""
import os
import re
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

# Initialize Flask app
app = Flask(__name__)
# Set maximum content length to 500MB to allow for multiple file uploads
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Check if the request contains files
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file type
        if not file.filename.lower().endswith('.json'):
            return jsonify({'error': 'Only JSON files are allowed for processed document import'}), 400

        # Read and parse the JSON file
        try:
            file_content = file.read().decode('utf-8')
            processed_data = json.loads(file_content)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON format: {str(e)}'}), 400
        except UnicodeDecodeError as e:
            return jsonify({'error': f'Invalid UTF-8 encoding: {str(e)}'}), 400

        # Validate the structure of the processed data
        required_fields = ['document', 'chunks']
        for field in required_fields:
            if field not in processed_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        if not isinstance(processed_data['chunks'], list):
            return jsonify({'error': 'Chunks must be an array'}), 400

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Convert the processed chunks to LangChain documents
        documents = []
        for chunk in processed_data['chunks']:
            # Validate required fields in each chunk
            if 'content' not in chunk:
                return jsonify({'error': 'Each chunk must have a content field'}), 400

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
                'user_id': current_user_id
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

        return jsonify({
            'message': f'Successfully imported {len(documents)} chunks from processed document',
            'document': processed_data.get('document', 'unknown'),
            'total_chunks': len(documents)
        }), 200

    except Exception as e:
        logger.error(f"Processed document import error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Processed document import failed: {str(e)}'}), 500


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
                'timeout': 7200,  # 2 hours to accommodate long-running PDF processing
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