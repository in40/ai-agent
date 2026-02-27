"""
NLP Data Scientist MCP Server
Main server implementation with NLP entity extraction tools
"""
import signal
import sys
import time
import argparse
from typing import Optional

from .utils.json_rpc import JsonRpcHandler, JsonRpcMessage, MessageType
from .transports.streamable_http import StreamableHttpTransport
from .handlers.nlp_handlers import NlpServerHandlers
from .utils.notifications import NotificationManager


class NlpMcpServer:
    """NLP Data Scientist MCP Server"""
    
    def __init__(self, 
                 host: str = "127.0.0.1",
                 port: int = 3065,
                 registry_host: str = "127.0.0.1",
                 registry_port: int = 3031,
                 register_with_registry: bool = True,
                 enable_registry: bool = False,
                 max_concurrent_requests: int = 10):
        
        self.host = host
        self.port = port
        self.running = False
        
        # Registry configuration
        self.enable_registry = enable_registry
        self.register_with_registry = register_with_registry
        self.registry_host = registry_host
        self.registry_port = registry_port
        
        # Initialize RPC handler
        self.rpc_handler = JsonRpcHandler(max_concurrent_requests=max_concurrent_requests)
        
        # Initialize NLP handlers
        self.nlp_handlers = NlpServerHandlers()
        
        # Initialize notification manager
        self.notification_manager = NotificationManager(self.rpc_handler)
        
        # Initialize transport (Streamable HTTP)
        self.transport = StreamableHttpTransport(self.rpc_handler, host, port)
        
        # Register handlers
        self._register_handlers()
        
        # Setup signal handling
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except ValueError:
            pass  # Running in thread
    
    def _register_handlers(self):
        """Register all handlers"""
        # Register NLP handlers
        self.nlp_handlers.register_handlers(self.rpc_handler)
        
        # Register standard MCP methods
        self.rpc_handler.register_request_handler('initialize', self._handle_initialize)
        self.rpc_handler.register_request_handler('shutdown', self._handle_shutdown)
        self.rpc_handler.register_request_handler('ping', self._handle_ping)
    
    def _handle_initialize(self, params, request_id):
        """Handle initialize request"""
        client_info = params.get("clientInfo", {})
        print(f"Initializing NLP server with client: {client_info.get('name', 'Unknown')}")
        
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "nlp-data-scientist-server",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"listChanged": True},
                "prompts": {"listChanged": True}
            }
        }
    
    def _handle_shutdown(self, params, request_id):
        """Handle shutdown request"""
        print("Shutdown requested")
        self.running = False
        return {}
    
    def _handle_ping(self, params, request_id):
        """Handle ping request"""
        import time
        return {
            "timestamp": time.time(),
            "status": "ok",
            "server": "nlp-data-scientist"
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)
    
    def run(self):
        """Run the server"""
        print(f"Starting NLP Data Scientist MCP Server on {self.host}:{self.port}")
        print(f"Transport: Streamable HTTP")
        print(f"Registry: {'Enabled' if self.enable_registry else 'Disabled'}")
        if self.register_with_registry:
            print(f"Registering with registry at {self.registry_host}:{self.registry_port}")
        
        self.running = True
        
        # Register with registry if configured
        if self.register_with_registry:
            self._register_with_registry()
        
        # Start transport (uses uvicorn internally)
        self.transport.start(self._message_callback)
        
        # Keep server running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        self.transport.stop()
    
    def _message_callback(self, message):
        """Callback to handle incoming messages"""
        # Check if this is a response to a server-initiated request
        if message.message_type == MessageType.RESPONSE and message.id is not None:
            self.rpc_handler.handle_client_response(message)
            return
        
        # Use synchronous version of handle_message
        try:
            response = self.rpc_handler.handle_message_sync(message)
            if response:
                self._send_response(response)
        except Exception as e:
            print(f"Error handling message: {e}")
            if message.message_type == MessageType.REQUEST:
                error_response = JsonRpcMessage.create_error_response(
                    message.id,
                    {"code": -32603, "message": f"Internal error: {str(e)}"}
                )
                self._send_response(error_response)
    
    def _send_response(self, response):
        """Send response via transport"""
        # In Streamable HTTP, responses are sent directly from request handlers
        # This method exists for interface compatibility
        print(f"[NLP Server] Response would be sent: {response.get('id', 'unknown')}")
    
    def _register_with_registry(self):
        """Register this server with the registry"""
        import requests
        
        service_info = {
            "id": f"nlp-data-scientist-{self.host}:{self.port}",
            "name": "NLP Data Scientist",
            "description": "Entity extraction and NLP analysis using spaCy, NLTK, and LLM",
            "endpoint": f"http://{self.host}:{self.port}",
            "capabilities": {
                "tools": [
                    "extract_entities",
                    "extract_entities_llm",
                    "analyze_document",
                    "filter_entities",
                    "get_entity_types",
                    "compare_extraction_methods",
                    "extract_standards",
                    "get_entity_statistics"
                ],
                "resources": ["nlp://entity-types", "nlp://extraction-methods"],
                "prompts": ["entity_extraction_prompt", "document_analysis_prompt"]
            },
            "metadata": {
                "llm_provider": "LM Studio",
                "llm_model": "qwen3-4b",
                "nlp_libraries": ["spaCy", "NLTK"]
            }
        }
        
        try:
            registry_url = f"http://{self.registry_host}:{self.registry_port}/mcp"
            
            # Send registration request
            payload = {
                "jsonrpc": "2.0",
                "id": "register-1",
                "method": "registry/register",
                "params": service_info
            }
            
            response = requests.post(registry_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if "error" not in result:
                    print(f"✓ Successfully registered with registry at {self.registry_host}:{self.registry_port}")
                else:
                    print(f"✗ Registry registration error: {result.get('error')}")
            else:
                print(f"✗ Registry registration failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"✗ Failed to register with registry: {e}")


def create_nlp_server():
    """Create and run NLP server with command-line arguments"""
    parser = argparse.ArgumentParser(description="NLP Data Scientist MCP Server")
    
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3065, help="Port to listen on")
    parser.add_argument("--registry-host", default="127.0.0.1", help="Registry server host")
    parser.add_argument("--registry-port", type=int, default=3031, help="Registry server port")
    parser.add_argument("--register-with-registry", action="store_true", default=True, help="Register with registry")
    parser.add_argument("--no-register", action="store_false", dest="register_with_registry", help="Don't register with registry")
    parser.add_argument("--enable-registry", action="store_true", help="Enable registry functionality")
    parser.add_argument("--max-concurrent-requests", type=int, default=10, help="Max concurrent requests")
    
    args = parser.parse_args()
    
    server = NlpMcpServer(
        host=args.host,
        port=args.port,
        registry_host=args.registry_host,
        registry_port=args.registry_port,
        register_with_registry=args.register_with_registry,
        enable_registry=args.enable_registry,
        max_concurrent_requests=args.max_concurrent_requests
    )
    
    server.run()


if __name__ == "__main__":
    create_nlp_server()
