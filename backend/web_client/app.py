import os
import json
import requests
import uuid
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import jwt
from functools import wraps
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional
import threading
import time

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['BACKEND_API_URL'] = os.environ.get('BACKEND_API_URL', 'http://localhost:5000')
# Set maximum content length to 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Enable CORS
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import security components to use the centralized authentication
from backend.security import security_manager, require_permission, Permission


def token_required(f):
    """Decorator to require a valid authentication token - compatible with backend services"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Use the centralized security manager to verify the token
            # The security manager expects the full token with Bearer prefix
            user_info = security_manager.verify_token(token)
            if not user_info:
                raise jwt.InvalidTokenError("Token not valid")

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    """Serve the main web client interface"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'frontend',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user - forwards to backend service"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400

        # Forward registration request to the backend service
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/auth/register",
            json=data
        )

        # Return the response from the backend service
        return jsonify(backend_response.json()), backend_response.status_code
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed!'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate a user and return a token - forwards to backend service"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400

        # Forward login request to the backend service
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/auth/login",
            json=data
        )

        # Return the response from the backend service
        return jsonify(backend_response.json()), backend_response.status_code
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed!'}), 500

@app.route('/api/agent/query', methods=['POST'])
@token_required
def agent_query():
    """Query the AI agent through the backend API"""
    try:
        data = request.get_json()
        
        user_request = data.get('user_request')
        if not user_request:
            return jsonify({'error': 'user_request is required'}), 400
        
        # Extract optional parameters
        disable_sql_blocking = data.get('disable_sql_blocking', False)
        disable_databases = data.get('disable_databases', False)
        
        # Prepare the request to the backend API
        backend_payload = {
            'user_request': user_request,
            'disable_sql_blocking': disable_sql_blocking,
            'disable_databases': disable_databases
        }
        
        # Make request to backend API
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/agent/query",
            json=backend_payload,
            headers={'Authorization': request.headers.get('Authorization')}
        )
        
        if backend_response.status_code != 200:
            return jsonify({'error': 'Backend service error'}), backend_response.status_code
        
        return jsonify(backend_response.json()), 200
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        return jsonify({'error': f'Agent query failed: {str(e)}'}), 500

@app.route('/api/rag/query', methods=['POST'])
@token_required
def rag_query():
    """Query the RAG system through the backend API"""
    try:
        data = request.get_json()
        
        query = data.get('query')
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        # Prepare the request to the backend API
        backend_payload = {
            'query': query
        }
        
        # Make request to backend API
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/rag/query",
            json=backend_payload,
            headers={'Authorization': request.headers.get('Authorization')}
        )
        
        if backend_response.status_code != 200:
            return jsonify({'error': 'Backend RAG service error'}), backend_response.status_code
        
        return jsonify(backend_response.json()), 200
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        return jsonify({'error': f'RAG query failed: {str(e)}'}), 500

@app.route('/api/rag/ingest', methods=['POST'])
@token_required
def rag_ingest():
    """Ingest documents into the RAG system"""
    try:
        data = request.get_json()
        
        file_paths = data.get('file_paths')
        if not file_paths:
            return jsonify({'error': 'file_paths is required'}), 400
        
        # Prepare the request to the backend API
        backend_payload = {
            'file_paths': file_paths
        }
        
        # Make request to backend API
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/rag/ingest",
            json=backend_payload,
            headers={'Authorization': request.headers.get('Authorization')}
        )

        # Return the response from the backend API with its original status code
        return jsonify(backend_response.json()), backend_response.status_code
    except Exception as e:
        logger.error(f"RAG ingestion error: {str(e)}")
        return jsonify({'error': f'RAG ingestion failed: {str(e)}'}), 500

@app.route('/api/rag/retrieve', methods=['POST'])
@token_required
def rag_retrieve():
    """Retrieve documents from the RAG system"""
    try:
        data = request.get_json()
        
        query = data.get('query')
        top_k = data.get('top_k', 5)  # Default to 5 results
        
        if not query:
            return jsonify({'error': 'query is required'}), 400
        
        # Prepare the request to the backend API
        backend_payload = {
            'query': query,
            'top_k': top_k
        }
        
        # Make request to backend API
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/rag/retrieve",
            json=backend_payload,
            headers={'Authorization': request.headers.get('Authorization')}
        )
        
        if backend_response.status_code != 200:
            return jsonify({'error': 'Backend RAG retrieval service error'}), backend_response.status_code
        
        return jsonify(backend_response.json()), 200
    except Exception as e:
        logger.error(f"RAG retrieval error: {str(e)}")
        return jsonify({'error': f'RAG retrieval failed: {str(e)}'}), 500

@app.route('/streamlit/<path:subpath>')
def proxy_streamlit(subpath):
    """Proxy requests to the Streamlit GUI"""
    try:
        # In a real implementation, you would proxy the request to the Streamlit service
        # For now, we'll return a placeholder
        return jsonify({
            'message': f'Proxying to Streamlit: /{subpath}',
            'status': 'placeholder'
        })
    except Exception as e:
        logger.error(f"Streamlit proxy error: {str(e)}")
        return jsonify({'error': f'Streamlit proxy failed: {str(e)}'}), 500

@app.route('/api/rag/upload', methods=['POST'])
@token_required
def rag_upload():
    """Upload documents to the RAG system"""
    try:
        # Debug: Print out information about received files
        print(f"DEBUG: Received {len(request.files.getlist('files'))} files in upload")
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename:
                file_content = file_storage.read()
                print(f"DEBUG: File {i+1} - filename='{file_storage.filename}', size={len(file_content)}")
                file_storage.seek(0)  # Reset file pointer after reading size

        # Prepare multipart form data
        files = []
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                # Ensure content_type is not None, use a default if needed
                content_type = file_storage.content_type or 'application/octet-stream'
                files.append(('files', (file_storage.filename, file_content, content_type)))

        print(f"DEBUG: Forwarding {len(files)} files to backend")
        for i, (key, (filename, _, _)) in enumerate(files):
            print(f"DEBUG: Forwarding file {i+1}: {filename}")

        # Forward headers
        headers = {'Authorization': request.headers.get('Authorization')}

        # Make request to the backend API (which should route through the gateway)
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/rag/upload",
            files=files,
            headers=headers
        )

        if backend_response.status_code != 200:
            return jsonify({'error': 'Backend RAG upload service error'}), backend_response.status_code

        return jsonify(backend_response.json()), 200
    except Exception as e:
        logger.error(f"RAG upload error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'RAG upload failed: {str(e)}'}), 500


@app.route('/api/rag/upload_with_progress', methods=['POST'])
@token_required
def rag_upload_with_progress():
    """Upload documents to the RAG system with progress tracking - forwards to backend service"""
    try:
        # Debug: Print out information about received files
        print(f"DEBUG: Received {len(request.files.getlist('files'))} files in upload_with_progress")
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename:
                file_content = file_storage.read()
                print(f"DEBUG: File {i+1} - filename='{file_storage.filename}', size={len(file_content)}")
                file_storage.seek(0)  # Reset file pointer after reading size

        # Prepare multipart form data
        files = []
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                # Ensure content_type is not None, use a default if needed
                content_type = file_storage.content_type or 'application/octet-stream'
                files.append(('files', (file_storage.filename, file_content, content_type)))

        print(f"DEBUG: Forwarding {len(files)} files to backend")
        for i, (key, (filename, _, _)) in enumerate(files):
            print(f"DEBUG: Forwarding file {i+1}: {filename}")

        # Forward headers
        headers = {'Authorization': request.headers.get('Authorization')}

        # Make request to the backend API (which should route through the gateway)
        backend_response = requests.post(
            f"{app.config['BACKEND_API_URL']}/api/rag/upload_with_progress",
            files=files,
            headers=headers
        )

        if backend_response.status_code != 200:
            return jsonify({'error': 'Backend RAG upload service error'}), backend_response.status_code

        return jsonify(backend_response.json()), 200
    except Exception as e:
        logger.error(f"RAG upload with progress error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'RAG upload with progress failed: {str(e)}'}), 500


@app.route('/api/rag/upload_progress/<session_id>', methods=['GET'])
@token_required
def get_upload_progress(session_id):
    """Get the upload progress for a specific session - forwards to backend service"""
    try:
        # Forward the request to the backend service to get upload progress
        headers = {'Authorization': request.headers.get('Authorization')}

        # Use the backend API URL to get progress from the RAG service
        backend_response = requests.get(
            f"{app.config['BACKEND_API_URL']}/api/rag/upload_progress/{session_id}",
            headers=headers
        )

        # Return the response from the backend service
        return jsonify(backend_response.json()), backend_response.status_code
    except Exception as e:
        logger.error(f"Get upload progress error: {str(e)}")
        return jsonify({'error': f'Failed to get upload progress: {str(e)}'}), 500


@app.route('/react/<path:subpath>')
def proxy_react(subpath):
    """Proxy requests to the React GUI"""
    try:
        # In a real implementation, you would proxy the request to the React service
        # For now, we'll return a placeholder
        return jsonify({
            'message': f'Proxying to React: /{subpath}',
            'status': 'placeholder'
        })
    except Exception as e:
        logger.error(f"React proxy error: {str(e)}")
        return jsonify({'error': f'React proxy failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)