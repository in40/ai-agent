"""
Backend API server for the AI Agent with authentication and multiple service endpoints

NOTE: This is the API GATEWAY. When updating AI agent functionality, 
DO NOT modify this file. Instead, modify the agent service at:
/root/qwen/ai_agent/backend/services/agent/app.py
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, Response
from flask_cors import CORS
import bcrypt
import logging
from typing import Dict, Any, Optional
import threading
import time

from rag_component.main import RAGOrchestrator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from models.response_generator import ResponseGenerator

# Import security module
from backend.security import security_manager, require_permission, rate_limit, validate_input, Permission

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '54d989bcf904ffb5fd8aa5842f929953985837026d64b1314046d6b8a9c1c801')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', '71ab14072ee24cb288aae255edb2f670c9a9e0d181365b04e45815f0c04ef41d')

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/auth/*": {"origins": "*"},
    r"/rag/*": {"origins": "*"},
    r"/agent/*": {"origins": "*"},
    r"/streamlit/*": {"origins": "*"},
    r"/react/*": {"origins": "*"}
})

# Initialize logging
logging.basicConfig(level=logging.DEBUG)  # Changed from INFO to DEBUG to capture debug messages
logger = logging.getLogger(__name__)

# In-memory user store (replace with database in production)
users_db = {}

# Authentication decorator (kept for backward compatibility)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated

# Routes

@app.route('/auth/register', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=300)  # 5 registrations per 5 minutes
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'username': {
                'type': str,
                'required': True,
                'min_length': 3,
                'max_length': 50,
                'sanitize': True
            },
            'password': {
                'type': str,
                'required': True,
                'min_length': 8,
                'max_length': 128,
                'sanitize': True
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'message': f'Validation error: {validation_errors}'}), 400

        username = data.get('username')
        password = data.get('password')

        if username in users_db:
            return jsonify({'message': 'Username already exists!'}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Store user (in production, use a database)
        users_db[username] = {
            'password': hashed_password,
            'created_at': datetime.utcnow(),
            'role': 'user'  # Default role
        }

        # Log audit event
        security_manager.log_audit_event(
            'system',
            'create',
            'user',
            request.remote_addr,
            success=True
        )

        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed!'}), 500

@app.route('/auth/login', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)  # 10 login attempts per minute
def login():
    """Login a user and return JWT token"""
    try:
        data = request.get_json()

        # Validate input
        schema = {
            'username': {
                'type': str,
                'required': True,
                'min_length': 3,
                'max_length': 50,
                'sanitize': True
            },
            'password': {
                'type': str,
                'required': True,
                'min_length': 8,
                'max_length': 128,
                'sanitize': True
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'message': f'Validation error: {validation_errors}'}), 400

        username = data.get('username')
        password = data.get('password')

        user = users_db.get(username)
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # Log failed login attempt
            security_manager.log_audit_event(
                username or 'unknown',
                'login',
                'auth',
                request.remote_addr,
                success=False
            )
            return jsonify({'message': 'Invalid credentials!'}), 401

        # Authenticate user and get permissions
        user_info = security_manager.authenticate_user(username, password)
        if not user_info:
            return jsonify({'message': 'Authentication failed!'}), 401

        # Generate JWT token
        token = security_manager.generate_token(user_info)

        # Create session
        session_id = security_manager.create_session(
            user_info,
            request.remote_addr,
            request.headers.get('User-Agent', 'Unknown')
        )

        # Log successful login
        security_manager.log_audit_event(
            username,
            'login',
            'auth',
            request.remote_addr,
            success=True
        )

        return jsonify({
            'token': token,
            'session_id': session_id,
            'message': 'Login successful!',
            'user_info': {
                'user_id': user_info['user_id'],
                'role': user_info['role'].value,
                'permissions': [p.value for p in user_info['permissions']]
            }
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")

        # Log failed login attempt
        username = data.get('username', 'unknown') if 'data' in locals() else 'unknown'
        security_manager.log_audit_event(
            username,
            'login',
            'auth',
            request.remote_addr,
            success=False
        )

        return jsonify({'message': 'Login failed!'}), 500

# Proxy route for AI Agent service
@app.route('/api/agent/query', methods=['POST'])
@require_permission(Permission.WRITE_AGENT)
@rate_limit(max_requests=30, window_seconds=60)  # 30 requests per minute
def proxy_agent_query():
    """Proxy agent query requests to the AI Agent service"""
    import requests
    import json

    agent_url = os.getenv('AGENT_URL', 'http://localhost:5002')
    url = f"{agent_url}/query"  # Direct to the agent service's query endpoint

    # Get the current user ID from the token validation decorator
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    # Get current user info for logging
    try:
        current_user_data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        current_user_id = current_user_data['user_id']
    except:
        current_user_id = 'unknown'

    # Get the request data and ensure it's properly formatted
    request_data = request.get_json()
    if not request_data:
        logger.error(f"No JSON data in agent query request from user {current_user_id}")
        return jsonify({'error': 'Invalid request: no JSON data provided'}), 400
    
    # Log the incoming request data to debug
    logger.debug(f"Incoming agent query request from user {current_user_id}: {request_data}")

    # Ensure the user_request field exists and is not None
    user_request = request_data.get('user_request')
    if user_request is None:
        logger.error(f"Missing user_request in agent query from user {current_user_id}")
        return jsonify({'error': 'Missing user_request in request'}), 400
    
    # Ensure user_request is a string and not empty
    if not isinstance(user_request, str) or len(user_request.strip()) == 0:
        logger.error(f"Invalid user_request in agent query from user {current_user_id}: {user_request}")
        return jsonify({'error': 'user_request must be a non-empty string'}), 400

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = agent_url.replace('http://', '').replace('https://', '')
    # Add content-type header if not already present
    if 'Content-Type' not in headers and 'content-type' not in headers:
        headers['Content-Type'] = 'application/json'

    try:
        # Send the request data as JSON to the agent service
        resp = requests.post(
            url=url,
            headers=headers,
            json=request_data,  # Use json parameter to send as JSON
            cookies=request.cookies,
            allow_redirects=False
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        
        # Log successful proxy
        logger.info(f"Agent query proxied successfully for user {current_user_id}")
        return response
    except Exception as e:
        logger.error(f"Agent proxy error for user {current_user_id}: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503

@app.route('/api/rag/query', methods=['POST'])
@require_permission(Permission.READ_RAG)
@rate_limit(max_requests=20, window_seconds=60)  # 20 requests per minute
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

@app.route('/api/rag/ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
@rate_limit(max_requests=10, window_seconds=60)  # 10 requests per minute
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
            return jsonify({'error': 'Document ingestion failed'}), 500
    except Exception as e:
        logger.error(f"RAG ingestion error: {str(e)}")
        return jsonify({'error': f'RAG ingestion failed: {str(e)}'}), 500

@app.route('/api/rag/retrieve', methods=['POST'])
@require_permission(Permission.READ_RAG)
@rate_limit(max_requests=20, window_seconds=60)  # 20 requests per minute
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

@app.route('/api/rag/lookup', methods=['POST'])
@require_permission(Permission.READ_RAG)
@rate_limit(max_requests=20, window_seconds=60)  # 20 requests per minute
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


@app.route('/api/health', methods=['GET'])
@rate_limit(max_requests=60, window_seconds=60)  # 60 requests per minute
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Agent Backend API is running',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200

@app.route('/api/config', methods=['GET'])
@require_permission(Permission.READ_SYSTEM)
def get_config(current_user_id):
    """Get system configuration"""
    return jsonify({
        'databases_enabled': not os.getenv('DISABLE_DATABASES', 'false').lower() == 'true',
        'rag_enabled': os.getenv('RAG_ENABLED', 'true').lower() == 'true',
        'sql_blocking_enabled': os.getenv('TERMINATE_ON_POTENTIALLY_HARMFUL_SQL', 'true').lower() == 'true',
        'version': '0.5.0',
        'security_features': {
            'rbac_enabled': True,
            'rate_limiting': True,
            'input_validation': True,
            'audit_logging': True
        }
    }), 200

# Proxy routes for Streamlit and React GUIs (no authentication required for these)
@app.route('/streamlit/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/streamlit/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/streamlit', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_streamlit(path=''):
    """Proxy requests to the Streamlit GUI"""
    import requests

    streamlit_url = os.getenv('STREAMLIT_URL', 'http://localhost:8501')
    url = f"{streamlit_url}/{path}"

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = streamlit_url.replace('http://', '').replace('https://', '')

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"Streamlit proxy error: {str(e)}")
        return jsonify({'error': 'Streamlit service unavailable'}), 503

@app.route('/react/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/react/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/react', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_react(path=''):
    """Proxy requests to the React GUI"""
    import requests

    react_url = os.getenv('REACT_URL', 'http://localhost:3000')
    url = f"{react_url}/{path}"

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = react_url.replace('http://', '').replace('https://', '')

    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"React proxy error: {str(e)}")
        return jsonify({'error': 'React service unavailable'}), 503

# Serve static files for the web client
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files for the web client"""
    import os
    from flask import send_from_directory

    # Define the static directory
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_client')

    # If path is empty, serve index.html
    if not path or path == '':
        return send_from_directory(static_dir, 'index.html')

    # Check if the file exists in the static directory
    if os.path.exists(os.path.join(static_dir, path)):
        return send_from_directory(static_dir, path)
    else:
        # If file doesn't exist, serve index.html (for client-side routing)
        return send_from_directory(static_dir, 'index.html')

# Additional API endpoints
@app.route('/api/agent/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy_agent(path=''):
    """Proxy requests to the AI Agent service"""
    import requests

    agent_url = os.getenv('AGENT_URL', 'http://localhost:5002')
    url = f"{agent_url}/{path}"

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = agent_url.replace('http://', '').replace('https://', '')
    
    # Prepare request data based on method
    if request.method in ['POST', 'PUT', 'PATCH']:
        request_data = request.get_data()
        if request.is_json:
            # Use json parameter for JSON requests
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                json=request.get_json(),  # Use json parameter to preserve structure
                cookies=request.cookies,
                allow_redirects=False
            )
        else:
            # Use data parameter for non-JSON requests
            resp = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request_data,
                cookies=request.cookies,
                allow_redirects=False
            )
    else:
        # For GET, DELETE, etc., no request body is expected
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False
        )

    try:
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"Agent proxy error: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503


@app.route('/api/agent/status', methods=['GET'])
@require_permission(Permission.READ_AGENT)
def proxy_agent_status():
    """Proxy agent status requests to the AI Agent service"""
    import requests

    agent_url = os.getenv('AGENT_URL', 'http://localhost:5002')
    url = f"{agent_url}/status"  # Direct to the agent service's status endpoint

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = agent_url.replace('http://', '').replace('https://', '')

    try:
        # For GET requests, no request body is expected
        resp = requests.get(
            url=url,
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False
        )

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"Agent status proxy error: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503

@app.route('/api/rag/status', methods=['GET'])
@require_permission(Permission.READ_RAG)
def rag_status(current_user_id):
    """Get the status of the RAG component"""
    return jsonify({
        'status': 'running',
        'message': 'RAG component is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200

@app.route('/api/services', methods=['GET'])
@require_permission(Permission.READ_SYSTEM)
def get_services(current_user_id):
    """Get information about available services"""
    return jsonify({
        'services': [
            {'name': 'AI Agent', 'endpoint': '/api/agent/query', 'method': 'POST', 'permission': 'write:agent'},
            {'name': 'RAG Query', 'endpoint': '/api/rag/query', 'method': 'POST', 'permission': 'read:rag'},
            {'name': 'RAG Ingest', 'endpoint': '/api/rag/ingest', 'method': 'POST', 'permission': 'write:rag'},
            {'name': 'RAG Retrieve', 'endpoint': '/api/rag/retrieve', 'method': 'POST', 'permission': 'read:rag'},
            {'name': 'RAG Lookup', 'endpoint': '/api/rag/lookup', 'method': 'POST', 'permission': 'read:rag'},
            {'name': 'Authentication', 'endpoint': '/auth/login', 'method': 'POST', 'permission': 'none'},
            {'name': 'Health Check', 'endpoint': '/api/health', 'method': 'GET', 'permission': 'none'},
            {'name': 'System Config', 'endpoint': '/api/config', 'method': 'GET', 'permission': 'read:system'}
        ],
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('BACKEND_PORT', 5000))

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