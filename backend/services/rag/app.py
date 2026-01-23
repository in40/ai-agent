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
        
        return jsonify({'documents': documents}), 200
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

            # Validate file size (max 10MB)
            # Seek to end to get file size, then reset position
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset position to beginning

            if size > 10 * 1024 * 1024:  # 10MB
                return jsonify({'error': 'File size exceeds 10MB limit'}), 400

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