"""
API Gateway for AI Agent System
Routes requests to appropriate services
"""
import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import logging
from datetime import datetime
import json

# Import security components
from backend.security import require_permission, validate_input, Permission

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service endpoints
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
AGENT_SERVICE_URL = os.getenv('AGENT_SERVICE_URL', 'http://localhost:5002')
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://localhost:5003')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'gateway',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.2.0',
        'services': {
            'auth': AUTH_SERVICE_URL,
            'agent': AGENT_SERVICE_URL,
            'rag': RAG_SERVICE_URL
        }
    }), 200


# Proxy routes to Auth Service
@app.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/auth/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/auth', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_auth(path=''):
    """Proxy requests to the authentication service"""
    url = f"{AUTH_SERVICE_URL}/{path}"
    
    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = AUTH_SERVICE_URL.replace('http://', '').replace('https://', '')
    
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
        logger.error(f"Auth service proxy error: {str(e)}")
        return jsonify({'error': 'Auth service unavailable'}), 503


# Proxy routes to Agent Service
@app.route('/agent/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/agent/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/agent', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_agent(path=''):
    """Proxy requests to the agent service"""
    url = f"{AGENT_SERVICE_URL}/{path}"
    
    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = AGENT_SERVICE_URL.replace('http://', '').replace('https://', '')
    
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
        logger.error(f"Agent service proxy error: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503


# Proxy routes to RAG Service
@app.route('/rag/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/rag/', methods=['GET', 'POST', 'PUT', 'DELETE'])
@app.route('/rag', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_rag(path=''):
    """Proxy requests to the RAG service"""
    url = f"{RAG_SERVICE_URL}/{path}"
    
    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    headers['Host'] = RAG_SERVICE_URL.replace('http://', '').replace('https://', '')
    
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
        logger.error(f"RAG service proxy error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


# Convenience routes that map to appropriate services
@app.route('/api/agent/query', methods=['POST'])
@require_permission(Permission.WRITE_AGENT)
def agent_query():
    """Convenience route for agent queries"""
    try:
        # Forward to agent service
        url = f"{AGENT_SERVICE_URL}/query"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Agent query convenience route error: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503


@app.route('/api/rag/query', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_query():
    """Convenience route for RAG queries"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/query"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG query convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_ingest():
    """Convenience route for RAG ingestion"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/ingest"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG ingest convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/retrieve', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_retrieve():
    """Convenience route for RAG retrieval"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/retrieve"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG retrieve convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/lookup', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_lookup():
    """Convenience route for RAG lookup"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/lookup"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG lookup convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/auth/validate', methods=['POST'])
def auth_validate():
    """Convenience route for token validation"""
    try:
        # Forward to auth service
        url = f"{AUTH_SERVICE_URL}/validate"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }
        
        resp = requests.post(url, json=request.get_json(), headers=headers)
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Auth validation convenience route error: {str(e)}")
        return jsonify({'error': 'Auth service unavailable'}), 503


if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('GATEWAY_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)