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
# Set maximum content length to 500MB to allow for multiple file uploads
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

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
            timeout=43200  # Increased timeout to 12 hours for AI model responses
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
            timeout=43200  # Increased timeout to 12 hours for AI model responses
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
            timeout=43200  # Increased timeout to 12 hours for AI model responses
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG lookup convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/mcp/search', methods=['POST'])
@require_permission(Permission.READ_MCP)
def mcp_search(current_user_id):
    """Convenience route for MCP search"""
    try:
        data = request.get_json()

        # Validate input
        from backend.security import validate_input
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
            },
            'enhanced': {
                'type': bool,
                'required': False
            }
        }

        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400

        query = data.get('query')
        top_k = data.get('top_k', 5)  # Default to 5 results
        enhanced = data.get('enhanced', False)  # Whether to use enhanced processing

        # Import MCP-related modules
        from registry.registry_client import ServiceRegistryClient
        from models.dedicated_mcp_model import DedicatedMCPModel

        # Get registry URL from environment
        registry_url = os.getenv('MCP_REGISTRY_URL', 'http://127.0.0.1:8080')

        # Connect to the registry
        registry_client = ServiceRegistryClient(registry_url)

        # Discover search services
        search_services = registry_client.discover_services(service_type="mcp_search")

        if not search_services:
            return jsonify({'error': 'No MCP search services available'}), 404

        # Use the first available search service
        search_service = search_services[0]

        # Create MCP model instance
        mcp_model = DedicatedMCPModel()

        # Prepare parameters for the search
        search_params = {
            "query": query,
            "count": top_k
        }

        # Call the MCP search service
        search_result = mcp_model._call_mcp_service(
            {
                'id': search_service.id,
                'host': search_service.host,
                'port': search_service.port,
                'type': search_service.type,
                'metadata': search_service.metadata
            },
            "search",
            search_params
        )

        # Extract results from the search
        if search_result.get('status') == 'success':
            # The structure might vary depending on the MCP service implementation
            result_data = search_result.get('result', {})

            # Try different possible structures for the results
            results = []
            if isinstance(result_data, dict):
                # Check if results are nested in a 'result' key
                if 'result' in result_data and 'results' in result_data['result']:
                    results = result_data['result']['results']
                # Or directly in a 'results' key
                elif 'results' in result_data:
                    results = result_data['results']
                # Or in a 'data' key
                elif 'data' in result_data:
                    results = result_data['data']
                # Or directly as the result_data if it's a list
                elif isinstance(result_data, list):
                    results = result_data
            elif isinstance(result_data, list):
                results = result_data

            # If enhanced processing is requested, use the RAG orchestrator's enhanced functionality
            if enhanced:
                try:
                    # Import the RAG orchestrator to use the enhanced search functionality
                    from rag_component.main import RAGOrchestrator
                    from models.response_generator import ResponseGenerator

                    # Initialize RAG orchestrator with an LLM
                    response_gen = ResponseGenerator()
                    llm = response_gen.llm
                    rag_orchestrator = RAGOrchestrator(llm=llm)

                    # Process the search results with download and summarization
                    processed_results = rag_orchestrator.process_search_results_with_download(
                        search_results=results,
                        user_query=query
                    )

                    # Format the processed results
                    formatted_results = []
                    for result in processed_results:
                        formatted_results.append({
                            'title': result.get('title', ''),
                            'content': result.get('summary', ''),
                            'url': result.get('url', ''),
                            'source': 'Enhanced MCP Search',
                            'score': result.get('relevance_score', 0.0)
                        })

                    return jsonify({'results': formatted_results}), 200
                except Exception as e:
                    logger.warning(f"Enhanced processing failed, falling back to basic search: {str(e)}")
                    # Fall back to basic processing if enhanced processing fails

            # Format results to match the expected structure (basic processing)
            formatted_results = []
            for idx, result in enumerate(results[:top_k]):  # Limit to top_k results
                if isinstance(result, dict):
                    # Get the basic result info
                    title = result.get('title', result.get('name', 'Untitled'))
                    url = result.get('url', result.get('link', ''))
                    source = result.get('source', result.get('url', result.get('link', 'Unknown source')))
                    score = result.get('score', result.get('relevance', 0.0))

                    # Get the initial content (description/snippet)
                    content = result.get('content', result.get('description', result.get('snippet', 'No content available')))

                    # For the first result, try to fetch full content using the MCP download service
                    if idx == 0 and url:  # Only for the first result
                        try:
                            # Attempt to fetch full content from the URL using the existing download service
                            # First, check if we have a download service available in the registry
                            from registry.registry_client import ServiceRegistryClient

                            registry_url = os.getenv('MCP_REGISTRY_URL', 'http://127.0.0.1:8080')
                            registry_client = ServiceRegistryClient(registry_url)

                            # Look for a download service
                            download_services = registry_client.discover_services(service_type="download")

                            if download_services:
                                # Use the first available download service
                                download_service = download_services[0]

                                # Prepare parameters for downloading the URL
                                download_params = {
                                    "url": url
                                }

                                # Create MCP model instance to call the service
                                from models.dedicated_mcp_model import DedicatedMCPModel
                                mcp_model = DedicatedMCPModel()

                                # Call the download service to get the full content
                                download_result = mcp_model._call_mcp_service(
                                    {
                                        'id': download_service.id,
                                        'host': download_service.host,
                                        'port': download_service.port,
                                        'type': download_service.type,
                                        'metadata': download_service.metadata
                                    },
                                    "download",
                                    download_params
                                )

                                # If successful, update the content with the full content
                                if download_result.get('status') == 'success':
                                    downloaded_content = download_result.get('result', {}).get('result', {}).get('content', '')
                                    # If no content found in nested 'result.result.content', try alternative paths
                                    if not downloaded_content:
                                        downloaded_content = download_result.get('result', {}).get('content', '')
                                    if not downloaded_content:
                                        downloaded_content = download_result.get('result', {}).get('data', '')

                                    if downloaded_content and len(downloaded_content) > len(content):
                                        content = downloaded_content
                        except Exception as e:
                            # If fetching full content fails, log the error and use the original content
                            logger.warning(f"Could not fetch full content for {url} using download service: {str(e)}")
                            pass

                    formatted_results.append({
                        'title': title,
                        'content': content,
                        'url': url,
                        'source': source,
                        'score': score
                    })
                else:
                    # If result is not a dict, create a basic entry
                    formatted_results.append({
                        'title': 'Search Result',
                        'content': str(result)[:500] + ('...' if len(str(result)) > 500 else ''),
                        'url': '',
                        'source': 'MCP Service',
                        'score': 0.0
                    })

            return jsonify({'results': formatted_results}), 200
        else:
            error_msg = search_result.get('error', 'Unknown error occurred during search')
            return jsonify({'error': f'MCP search failed: {error_msg}'}), 500

    except Exception as e:
        logger.error(f"MCP search error: {str(e)}")
        return jsonify({'error': f'MCP search failed: {str(e)}'}), 500


@app.route('/api/rag/upload', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_upload(current_user_id):
    """Convenience route for RAG upload"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/upload"

        # Handle multipart form data for file uploads

        # Prepare files for forwarding - properly handle multiple files with same key
        files = []
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                files.append(('files', (file_storage.filename, file_content, file_storage.content_type or 'application/octet-stream')))

        # Prepare headers (excluding Content-Type which will be set by requests for multipart)
        forwarded_headers = {}
        for key, value in request.headers:
            if key.lower() not in ['content-type', 'content-length']:
                forwarded_headers[key] = value

        # Add authorization header
        forwarded_headers['Authorization'] = request.headers.get('Authorization', '')

        resp = requests.post(url, files=files, headers=forwarded_headers, timeout=43200)  # 12 hour timeout for large uploads and processing
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG clear convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/upload_progress/<session_id>', methods=['GET'])
@require_permission(Permission.WRITE_RAG)
def rag_upload_progress(current_user_id, session_id):
    """Convenience route for getting RAG upload progress"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/upload_progress/{session_id}"
        headers = {
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.get(url, headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG upload progress convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/upload_with_progress', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_upload_with_progress(current_user_id):
    """Convenience route for RAG upload with progress"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/upload_with_progress"

        # Handle multipart form data for file uploads

        # Prepare files for forwarding - properly handle multiple files with same key
        files = []
        for i, file_storage in enumerate(request.files.getlist('files')):
            if file_storage and file_storage.filename != '':
                # Read the file content to avoid stream issues
                file_content = file_storage.read()
                # Ensure content_type is not None, use a default if needed
                content_type = file_storage.content_type or 'application/octet-stream'
                files.append(('files', (file_storage.filename, file_content, content_type)))

        # Prepare headers (excluding Content-Type which will be set by requests for multipart)
        forwarded_headers = {}
        for key, value in request.headers:
            if key.lower() not in ['content-type', 'content-length']:
                forwarded_headers[key] = value

        # Add authorization header
        forwarded_headers['Authorization'] = request.headers.get('Authorization', '')

        resp = requests.post(url, files=files, headers=forwarded_headers, timeout=43200)  # 12 hour timeout for large uploads and processing
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG upload with progress convenience route error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/ingest_from_session', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_ingest_from_session(current_user_id):
    """Convenience route for RAG ingestion from session"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/ingest_from_session"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': request.headers.get('Authorization', '')
        }

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG ingestion from session convenience route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/limits', methods=['GET'])
@require_permission(Permission.READ_RAG)
def rag_limits():
    """Convenience route for getting RAG upload limits"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/limits"

        # Prepare headers
        forwarded_headers = {}
        for key, value in request.headers:
            if key.lower() not in ['content-type', 'content-length']:
                forwarded_headers[key] = value

        # Add authorization header
        forwarded_headers['Authorization'] = request.headers.get('Authorization', '')

        resp = requests.get(url, headers=forwarded_headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"RAG limits convenience route error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/download/<path:path>', methods=['GET'])
def download_file(path):
    """Route for downloading files from RAG service"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/download/{path}"

        # Forward all headers except Host, ensuring Authorization header is preserved
        headers = {}
        for key, value in request.headers:
            if key.lower() != 'host':
                headers[key] = value

        # Explicitly ensure Authorization header is set if present in original request
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header

        headers['Host'] = RAG_SERVICE_URL.replace('http://', '').replace('https://', '')

        # Forward query parameters
        params = request.args.to_dict()

        resp = requests.get(url, headers=headers, params=params, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"Download file route error: {str(e)}")
        return jsonify({'error': 'RAG service unavailable'}), 503


@app.route('/api/rag/import_processed', methods=['POST'])
@require_permission(Permission.WRITE_RAG)
def rag_import_processed(current_user_id):
    """Convenience route for importing processed documents"""
    try:
        # Forward to RAG service
        url = f"{RAG_SERVICE_URL}/import_processed"

        # Prepare headers
        headers = {
            'Authorization': request.headers.get('Authorization', '')
        }

        # Handle multipart form data (file upload)
        files = []
        if 'file' in request.files:
            for file_storage in request.files.getlist('file'):
                if file_storage and file_storage.filename != '':
                    file_content = file_storage.read()
                    content_type = file_storage.content_type or 'application/octet-stream'
                    files.append(('file', (file_storage.filename, file_content, content_type)))

        # Make request to RAG service
        if files:
            # Use requests with files
            resp = requests.post(url, files=files, headers=headers, timeout=43200)  # Increased timeout to 12 hours
        else:
            # Forward without files if no files were provided
            resp = requests.post(url, headers=headers, data=request.get_data(), timeout=43200)

        # Return the response from the RAG service with its original status code
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response
    except Exception as e:
        logger.error(f"RAG import processed convenience route error: {str(e)}")
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

        resp = requests.post(url, json=request.get_json(), headers=headers, timeout=43200)  # Increased timeout to 12 hours for AI model responses
        return Response(resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Auth validation convenience route error: {str(e)}")
        return jsonify({'error': 'Auth service unavailable'}), 503


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
            {'name': 'MCP Search', 'endpoint': '/api/mcp/search', 'method': 'POST', 'permission': 'read:mcp'},
            {'name': 'Authentication', 'endpoint': '/auth/login', 'method': 'POST', 'permission': 'none'},
            {'name': 'Health Check', 'endpoint': '/health', 'method': 'GET', 'permission': 'none'},
            {'name': 'System Config', 'endpoint': '/api/config', 'method': 'GET', 'permission': 'read:system'}
        ],
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


if __name__ == '__main__':
    # Get port from environment variable or default to 5000
    port = int(os.getenv('GATEWAY_PORT', 5000))

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