"""
API Gateway for AI Agent System
Routes requests to appropriate services
"""
import os
import requests
from flask import Flask, request, jsonify, Response, render_template, send_from_directory
from flask_cors import CORS
import logging
from datetime import datetime
import json

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

# Service endpoints
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:5001')
AGENT_SERVICE_URL = os.getenv('AGENT_SERVICE_URL', 'http://localhost:5002')
RAG_SERVICE_URL = os.getenv('RAG_SERVICE_URL', 'http://localhost:5003')

# Web client directory
WEB_CLIENT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'web_client')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'gateway',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0',
        'services': {
            'auth': AUTH_SERVICE_URL,
            'agent': AGENT_SERVICE_URL,
            'rag': RAG_SERVICE_URL
        }
    }), 200


@app.route('/', methods=['GET'])
def serve_web_client():
    """Serve the main web client interface"""
    try:
        # Try to serve index.html from the web client directory
        return send_from_directory(WEB_CLIENT_DIR, 'index.html')
    except FileNotFoundError:
        # If index.html doesn't exist, return a simple welcome message
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Agent System</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .container { max-width: 600px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to the AI Agent System</h1>
                <p>The microservices architecture is running.</p>
                <p>Available endpoints:</p>
                <ul style="text-align: left;">
                    <li><code>/health</code> - System health check</li>
                    <li><code>/auth/*</code> - Authentication endpoints</li>
                    <li><code>/api/agent/*</code> - Agent API endpoints</li>
                    <li><code>/api/rag/*</code> - RAG API endpoints</li>
                </ul>
                <p>For the web interface, ensure the web client files are in the correct directory.</p>
            </div>
        </body>
        </html>
        '''


@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve static files from the web client directory"""
    try:
        return send_from_directory(WEB_CLIENT_DIR, path)
    except FileNotFoundError:
        # If the file doesn't exist, serve the index.html for SPA routing
        return send_from_directory(WEB_CLIENT_DIR, 'index.html')


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
            allow_redirects=False,
            timeout=600  # Increased timeout to 10 minutes for AI model responses
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
            allow_redirects=False,
            timeout=600  # Increased timeout to 10 minutes for AI model responses
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
            allow_redirects=False,
            timeout=600  # Increased timeout to 10 minutes for AI model responses
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
def agent_query(current_user_id):
    """Convenience route for agent queries"""
    try:
        # Forward to agent service
        url = f"{AGENT_SERVICE_URL}/query"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Agent query convenience route error: {str(e)}")
        return jsonify({'error': 'Agent service unavailable'}), 503


@app.route('/api/rag/query', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_query(current_user_id):
    """Convenience route for RAG queries"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/query"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG query convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/ingest', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_ingest(current_user_id):
    """Convenience route for RAG ingestion"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/ingest"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG ingest convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/retrieve', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_retrieve(current_user_id):
    """Convenience route for RAG retrieval"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/retrieve"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG retrieve convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/lookup', methods=['POST'])
@require_permission(Permission.READ_RAG)
def rag_lookup(current_user_id):
    """Convenience route for RAG lookup"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/lookup"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG lookup convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/upload', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_upload(current_user_id):
    """Convenience route for RAG upload"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/upload"

        # Handle multipart form data for file uploads
        import requests
        from flask import request

        # Prepare files for forwarding
        files = []
        for key, file_storage in request.files.items():
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                files.append((key, (file_storage.filename, file_content, file_storage.content_type)))

        # Prepare headers (excluding Content-Type which will be set by requests for multipart)
        forwarded_headers = {}
        for key, value in request.headers:
            if key.lower() not in ['content-type', 'content-length']:
                forwarded_headers[key] = value

        # Add authorization header
        forwarded_headers['Authorization'] = request.headers.get('Authorization', '')

        resp = requests.post(url, files=files, headers=forwarded_headers, timeout=600)  # 10 minute timeout for large uploads and processing
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG upload convenience route error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/clear', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_clear(current_user_id):
    """Convenience route for clearing all documents from RAG"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/clear"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG clear convenience route error: {str(e)}")
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=600)  # Increased timeout to 10 minutes for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Auth validation convenience route error: {str(e)}")
        return jsonify({'error': 'Auth service unavailable'}), 503


if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('GATEWAY_PORT', 5000))

    # Check if running in production mode
    if os.getenv('FLASK_ENV') == 'production':
        try:
            # Production: Use Gunicorn programmatically
            from gunicorn.app.base import BaseApplication
            from gunicorn.six import iteritems

            class StandaloneApplication(BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super(StandaloneApplication, self).__init__()

                def load_config(self):
                    config = dict([(key, value) for key, value in iteritems(self.options)
                                   if key in self.cfg.settings and value is not None])
                    for key, value in iteritems(config):
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
        except ImportError:
            print("Gunicorn not installed. Please install it with: pip install gunicorn")
            print("Running in development mode instead...")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development: Use Flask's built-in server
        app.run(host='0.0.0.0', port=port, debug=False)