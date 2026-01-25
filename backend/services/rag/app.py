"""
RAG Service for AI Agent System
Handles document processing and retrieval
"""
import os
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
# Set maximum content length to 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                # Construct the download URL
                download_url = f"{request.url_root}download/{file_id}/{filename}"
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
        
        # Retrieve documents
        documents = rag_orchestrator.retrieve_documents(query)
        
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

        def secure_filename(filename: str) -> str:
            """
            Secure a filename by removing potentially dangerous characters and sequences.
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
            # Allow only alphanumeric, dots, dashes, and underscores
            filename = re.sub(r'[^A-Za-z0-9.\-_]', '_', filename)

            # Handle cases where the filename might be empty after sanitization
            if not filename:
                filename = "unnamed_file"

            # Prevent hidden files by ensuring the name doesn't start with a dot
            if filename.startswith('.'):
                filename = f"unnamed{filename}"

            return filename

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
            max_file_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', 50 * 1024 * 1024))  # Default to 50MB
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

        def secure_filename(filename: str) -> str:
            """
            Secure a filename by removing potentially dangerous characters and sequences.
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
            # Allow only alphanumeric, dots, dashes, and underscores
            filename = re.sub(r'[^A-Za-z0-9.\-_]', '_', filename)

            # Handle cases where the filename might be empty after sanitization
            if not filename:
                filename = "unnamed_file"

            # Prevent hidden files by ensuring the name doesn't start with a dot
            if filename.startswith('.'):
                filename = f"unnamed{filename}"

            return filename

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
        if len(files) > 10:  # Maximum 10 files at once
            # Clean up progress tracking
            redis_client.delete(key)
            return jsonify({'error': 'Maximum 10 files allowed per upload'}), 400

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
            max_file_size = int(os.getenv('MAX_FILE_UPLOAD_SIZE', 50 * 1024 * 1024))  # Default to 50MB
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

        # Initialize RAG orchestrator with appropriate LLM
        response_generator = ResponseGenerator()
        llm = response_generator._get_llm_instance(
            provider=RESPONSE_LLM_PROVIDER,
            model=RESPONSE_LLM_MODEL
        )

        rag_orchestrator = RAGOrchestrator(llm=llm)

        # Update progress tracking
        session_data['status'] = 'Starting document ingestion...'
        pipe = redis_client.pipeline()
        pipe.setex(key, timedelta(hours=1), json.dumps(session_data))
        pipe.execute()

        # Process ingestion in a separate thread to allow progress tracking
        def process_ingestion():
            try:
                total_files = len(file_paths)

                # Update all files to 'processing' status before starting actual ingestion
                # Get current session data from Redis
                current_session_data_json = redis_client.get(key)
                if current_session_data_json:
                    current_session_data = json.loads(current_session_data_json)
                else:
                    # If session doesn't exist anymore, stop processing
                    return

                print(f"DEBUG: About to update all {len(original_filenames)} files to 'processing' status")
                print(f"DEBUG: Original filenames: {original_filenames}")
                print(f"DEBUG: Current session data results: {current_session_data.get('results', {})}")

                # Ensure results dict exists and update all files to 'processing'
                if 'results' not in current_session_data:
                    current_session_data['results'] = {}

                # Update all files to 'processing' status
                for original_filename in original_filenames:
                    current_session_data['results'][original_filename] = {
                        'status': 'processing',
                        'message': f'{original_filename} is being processed',
                        'progress': 50  # Set to 50% to indicate processing has started
                    }

                print(f"DEBUG: Updated session data results: {current_session_data['results']}")

                # Update session data with overall progress
                current_session_data.update({
                    'progress': 50,  # Set to 50% to indicate processing has started
                    'status': f'Processing all {total_files} files...',
                    'current_file': ', '.join(original_filenames),  # List all files being processed
                    'completed_files': 0  # Will be updated after ingestion
                })

                # Use Redis transaction to ensure atomic update
                pipe = redis_client.pipeline()
                pipe.setex(key, timedelta(hours=1), json.dumps(current_session_data))
                pipe.execute()

                # Small delay to allow the status to propagate
                time.sleep(0.01)

                # Final ingestion call
                success = rag_orchestrator.ingest_documents_from_upload(file_paths, original_filenames)

                # Get current session data from Redis
                current_session_data_json = redis_client.get(key)
                if current_session_data_json:
                    current_session_data = json.loads(current_session_data_json)
                else:
                    # If session doesn't exist anymore, exit
                    return

                print(f"DEBUG: About to update all files to completion status. Success={success}")
                print(f"DEBUG: Original filenames: {original_filenames}")
                print(f"DEBUG: Current session data results: {current_session_data.get('results', {})}")

                # Update individual file statuses based on overall success
                for filename in original_filenames:
                    print(f"DEBUG: Updating status for filename: {filename}")
                    if 'results' in current_session_data and filename in current_session_data['results']:
                        print(f"DEBUG: Found {filename} in results, updating status")
                        if success:
                            current_session_data['results'][filename] = {
                                'status': 'completed',
                                'message': f'{filename} processed successfully',
                                'progress': 100
                            }
                        else:
                            current_session_data['results'][filename] = {
                                'status': 'failed',
                                'message': f'{filename} processing failed',
                                'progress': 100
                            }
                    else:
                        print(f"DEBUG: {filename} not found in results, initializing it")
                        # If results dict doesn't exist or filename not in it, initialize it
                        if 'results' not in current_session_data:
                            current_session_data['results'] = {}
                        if success:
                            current_session_data['results'][filename] = {
                                'status': 'completed',
                                'message': f'{filename} processed successfully',
                                'progress': 100
                            }
                        else:
                            current_session_data['results'][filename] = {
                                'status': 'failed',
                                'message': f'{filename} processing failed',
                                'progress': 100
                            }

                print(f"DEBUG: Final session data results: {current_session_data.get('results', {})}")

                # Mark completion
                if success:
                    current_session_data.update({
                        'progress': 100,
                        'status': 'All files processed successfully',
                        'completed_files': total_files
                    })
                else:
                    current_session_data.update({
                        'progress': 100,
                        'status': 'Document ingestion completed with errors'
                    })

                # Extend the expiration time after completion to ensure client can get final status
                current_session_data['expires_at'] = (datetime.now() + timedelta(minutes=30)).isoformat()

                # Update Redis with final session data
                pipe = redis_client.pipeline()
                pipe.setex(key, timedelta(minutes=30), json.dumps(current_session_data))
                pipe.execute()
            except Exception as e:
                logger.error(f"Error in ingestion thread: {str(e)}")

                # Get current session data from Redis
                current_session_data_json = redis_client.get(key)
                if current_session_data_json:
                    current_session_data = json.loads(current_session_data_json)
                else:
                    # If session doesn't exist anymore, exit
                    return

                print(f"DEBUG: Error occurred during ingestion: {str(e)}")
                print(f"DEBUG: About to update all files to error status")
                print(f"DEBUG: Original filenames: {original_filenames}")
                print(f"DEBUG: Current session data results: {current_session_data.get('results', {})}")

                # Update individual file statuses to reflect the error
                for filename in original_filenames:
                    print(f"DEBUG: Updating error status for filename: {filename}")
                    if 'results' in current_session_data and filename in current_session_data['results']:
                        print(f"DEBUG: Found {filename} in results, updating to error status")
                        current_session_data['results'][filename] = {
                            'status': 'failed',
                            'message': f'{filename} processing failed: {str(e)}',
                            'progress': 100
                        }
                    else:
                        print(f"DEBUG: {filename} not found in results, initializing to error status")
                        # If results dict doesn't exist or filename not in it, initialize it
                        if 'results' not in current_session_data:
                            current_session_data['results'] = {}
                        current_session_data['results'][filename] = {
                            'status': 'failed',
                            'message': f'{filename} processing failed: {str(e)}',
                            'progress': 100
                        }

                print(f"DEBUG: Final session data results after error: {current_session_data.get('results', {})}")

                current_session_data.update({
                    'progress': 100,
                    'status': f'Error during ingestion: {str(e)}',
                    'completed_files': 0
                })

                # Extend the expiration time even for failed sessions to ensure client can get final status
                current_session_data['expires_at'] = (datetime.now() + timedelta(minutes=30)).isoformat()

                # Update Redis with error session data
                pipe = redis_client.pipeline()
                pipe.setex(key, timedelta(minutes=30), json.dumps(current_session_data))
                pipe.execute()

        # Start the ingestion process in a separate thread
        ingestion_thread = threading.Thread(target=process_ingestion)
        ingestion_thread.daemon = True  # Ensure thread doesn't prevent shutdown
        ingestion_thread.start()

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
@require_permission(Permission.READ_RAG)
def rag_download_file(current_user_id, file_id, filename):
    """Endpoint to download an original file by its ID and filename"""
    try:
        import os
        from config.settings import RAG_FILE_STORAGE_DIR
        from werkzeug.utils import secure_filename

        # Sanitize the filename to prevent path traversal
        safe_filename = secure_filename(filename)

        # Construct the file path using the file ID and filename
        file_storage_dir = os.path.join(RAG_FILE_STORAGE_DIR or "./data/rag_uploaded_files", file_id)
        file_path = os.path.join(file_storage_dir, safe_filename)

        # Verify that the file exists and is within the expected directory
        if not os.path.exists(file_path):
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


# Note: Redis handles key expiration automatically, so no manual cleanup needed


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
                'timeout': 600,  # 10 minutes to match our timeout configuration
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