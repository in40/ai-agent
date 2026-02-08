"""
Agent Service for AI Agent System
Handles AI agent requests and processing
"""
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import time

# Import the LangGraph agent
from langgraph_agent.langgraph_agent import run_enhanced_agent

# Import security components
from backend.security import require_permission, validate_input, Permission

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.DEBUG)  # Changed from INFO to DEBUG to capture debug messages
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'agent',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


@app.route('/query', methods=['POST'])
@require_permission(Permission.WRITE_AGENT)
def agent_query(current_user_id):
    """Endpoint for the main AI agent functionality"""
    try:
        data = request.get_json()
        
        # Validate input
        schema = {
            'user_request': {
                'type': str,
                'required': True,
                'min_length': 1,
                'max_length': 2000,
                'sanitize': True
            },
            'disable_sql_blocking': {
                'type': bool,
                'required': False
            },
            'disable_databases': {
                'type': bool,
                'required': False
            },
            'custom_system_prompt': {
                'type': str,
                'required': False,
                'max_length': 5000,
                'sanitize': True
            },
            'skip_final_response_generation': {
                'type': bool,
                'required': False
            }
        }
        
        validation_errors = validate_input(data, schema)
        if validation_errors:
            return jsonify({'error': f'Validation error: {validation_errors}'}), 400
        
        user_request = data.get('user_request')
        logger.info(f"[AGENT_SERVICE] Received user_request: '{user_request}' (length: {len(user_request) if user_request else 0})")

        # Extract optional parameters
        disable_sql_blocking = data.get('disable_sql_blocking', False)
        disable_databases = data.get('disable_databases', False)
        custom_system_prompt = data.get('custom_system_prompt', None)
        skip_final_response_generation = data.get('skip_final_response_generation', False)

        # DEBUG logging for received parameters
        logger.debug(f"DEBUG: Agent service received custom_system_prompt: {custom_system_prompt}")
        logger.debug(f"DEBUG: Agent service received skip_final_response_generation: {skip_final_response_generation}")

        start_time = time.time()

        # Get registry URL from environment or data
        registry_url = data.get('registry_url', os.getenv('MCP_REGISTRY_URL', 'http://127.0.0.1:8080'))

        # Run the agent with all parameters
        result = run_enhanced_agent(
            user_request=user_request,
            mcp_servers=[],  # Pass empty list of MCP servers for now
            disable_sql_blocking=disable_sql_blocking,
            disable_databases=disable_databases,
            custom_system_prompt=custom_system_prompt,
            skip_final_response_generation=skip_final_response_generation,
            registry_url=registry_url
        )
        
        # Add execution time to result
        result['execution_time'] = time.time() - start_time
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Agent query error: {str(e)}")
        return jsonify({'error': f'Agent query failed: {str(e)}'}), 500


@app.route('/status', methods=['GET'])
@require_permission(Permission.READ_AGENT)
def agent_status():
    """Get the status of the AI agent"""
    return jsonify({
        'status': 'running',
        'service': 'agent',
        'message': 'AI Agent is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '0.5.0'
    }), 200


if __name__ == '__main__':
    # Get port from environment variable or default to 5002
    port = int(os.getenv('AGENT_SERVICE_PORT', 5002))

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