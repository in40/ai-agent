"""
Backend API server for the AI Agent with authentication and multiple service endpoints
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session, Response
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash
import logging
from typing import Dict, Any, Optional
import threading
import time

# Import the LangGraph agent
from langgraph_agent.langgraph_agent import run_enhanced_agent
from rag_component.main import RAGOrchestrator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL
from models.response_generator import ResponseGenerator

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-this-too')

# Enable CORS for all routes
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/auth/*": {"origins": "*"},
    r"/rag/*": {"origins": "*"},
    r"/streamlit/*": {"origins": "*"},
    r"/react/*": {"origins": "*"}
})

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory user store (replace with database in production)
users_db = {}

# Authentication decorator
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
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400

        if username in users_db:
            return jsonify({'message': 'Username already exists!'}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Store user (in production, use a database)
        users_db[username] = {
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }

        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed!'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    """Login a user and return JWT token"""
    try:
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required!'}), 400

        user = users_db.get(username)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'message': 'Invalid credentials!'}), 401

        # Generate JWT token
        token = jwt.encode({
            'user_id': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['JWT_SECRET_KEY'], algorithm="HS256")

        return jsonify({
            'token': token,
            'message': 'Login successful!'
        }), 200
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed!'}), 500

@app.route('/api/agent/query', methods=['POST'])
@token_required
def agent_query(current_user_id):
    """Endpoint for the main AI agent functionality"""
    try:
        data = request.get_json()

        user_request = data.get('user_request')
        if not user_request:
            return jsonify({'error': 'user_request is required'}), 400

        # Extract optional parameters
        disable_sql_blocking = data.get('disable_sql_blocking', False)
        disable_databases = data.get('disable_databases', False)

        # Run the agent
        result = run_enhanced_agent(
            user_request=user_request,
            disable_sql_blocking=disable_sql_blocking,
            disable_databases=disable_databases
        )

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        return jsonify({'error': f'Agent query failed: {str(e)}'}), 500

@app.route('/api/rag/query', methods=['POST'])
@token_required
def rag_query(current_user_id):
    """Endpoint for RAG queries"""
    try:
        data = request.get_json()

        query = data.get('query')
        if not query:
            return jsonify({'error': 'query is required'}), 400

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
@token_required
def rag_ingest(current_user_id):
    """Endpoint for ingesting documents into RAG"""
    try:
        data = request.get_json()

        file_paths = data.get('file_paths')
        if not file_paths:
            return jsonify({'error': 'file_paths is required'}), 400

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
@token_required
def rag_retrieve(current_user_id):
    """Endpoint for retrieving documents from RAG"""
    try:
        data = request.get_json()

        query = data.get('query')
        top_k = data.get('top_k', 5)  # Default to 5 results

        if not query:
            return jsonify({'error': 'query is required'}), 400

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
@token_required
def rag_lookup(current_user_id):
    """Endpoint for looking up documents in RAG"""
    try:
        data = request.get_json()

        query = data.get('query')
        if not query:
            return jsonify({'error': 'query is required'}), 400

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
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Agent Backend API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/config', methods=['GET'])
@token_required
def get_config(current_user_id):
    """Get system configuration"""
    return jsonify({
        'databases_enabled': not os.getenv('DISABLE_DATABASES', 'false').lower() == 'true',
        'rag_enabled': os.getenv('RAG_ENABLED', 'true').lower() == 'true',
        'sql_blocking_enabled': os.getenv('TERMINATE_ON_POTENTIALLY_HARMFUL_SQL', 'true').lower() == 'true'
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
@app.route('/api/agent/status', methods=['GET'])
@token_required
def agent_status(current_user_id):
    """Get the status of the AI agent"""
    return jsonify({
        'status': 'running',
        'message': 'AI Agent is operational',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/rag/status', methods=['GET'])
@token_required
def rag_status(current_user_id):
    """Get the status of the RAG component"""
    return jsonify({
        'status': 'running',
        'message': 'RAG component is operational',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/services', methods=['GET'])
@token_required
def get_services(current_user_id):
    """Get information about available services"""
    return jsonify({
        'services': [
            {'name': 'AI Agent', 'endpoint': '/api/agent/query', 'method': 'POST'},
            {'name': 'RAG Query', 'endpoint': '/api/rag/query', 'method': 'POST'},
            {'name': 'RAG Ingest', 'endpoint': '/api/rag/ingest', 'method': 'POST'},
            {'name': 'RAG Retrieve', 'endpoint': '/api/rag/retrieve', 'method': 'POST'},
            {'name': 'RAG Lookup', 'endpoint': '/api/rag/lookup', 'method': 'POST'},
            {'name': 'Authentication', 'endpoint': '/auth/login', 'method': 'POST'},
            {'name': 'Health Check', 'endpoint': '/api/health', 'method': 'GET'}
        ],
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('BACKEND_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)