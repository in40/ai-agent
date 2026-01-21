import os
import json
import requests
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import jwt
from functools import wraps
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional

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

# In-memory store for auth tokens (in production, use a database or Redis)
tokens_db = {}

def token_required(f):
    """Decorator to require a valid authentication token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode the token to verify it's valid
            # In a real implementation, you would verify against a known secret
            # For this example, we'll just check if it exists in our tokens_db
            if token not in tokens_db:
                raise jwt.InvalidTokenError("Token not found in database")
                
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
    """Register a new user"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400
        
        # In a real implementation, you would hash the password and store it in a database
        # For this example, we'll just store it in memory
        user_id = len(tokens_db) + 1  # Simple ID generation
        tokens_db[user_id] = {
            'username': username,
            'password': password,  # In production, hash this!
            'created_at': datetime.utcnow()
        }
        
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed!'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate a user and return a token"""
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400
        
        # Find user in our in-memory store
        user_id = None
        for uid, user_data in tokens_db.items():
            if user_data['username'] == username and user_data['password'] == password:
                user_id = uid
                break
        
        if not user_id:
            return jsonify({'message': 'Invalid credentials!'}), 401
        
        # Generate a token (in a real implementation, use proper JWT signing)
        token = jwt.encode({
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        # Store the token
        tokens_db[token] = {
            'user_id': user_id,
            'username': username,
            'created_at': datetime.utcnow()
        }
        
        return jsonify({
            'token': token,
            'message': 'Login successful!'
        }), 200
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
        # Prepare multipart form data
        files = []
        for key, file_storage in request.files.items():
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                files.append((key, (file_storage.filename, file_content, file_storage.content_type)))

        # Forward headers
        headers = {'Authorization': request.headers.get('Authorization')}

        # Make request directly to RAG service (bypassing gateway to avoid circular reference)
        import requests
        rag_service_url = os.environ.get('RAG_SERVICE_URL', 'http://localhost:5003')
        backend_response = requests.post(
            f"{rag_service_url}/upload",
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
    app.run(host='0.0.0.0', port=5000, debug=False)