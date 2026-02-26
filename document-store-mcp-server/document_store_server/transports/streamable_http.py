"""
Streamable HTTP Transport for MCP Server
Implements the modern Streamable HTTP transport with a single /mcp endpoint
that handles both POST and GET methods for bidirectional communication.
"""
import json
import asyncio
import threading
import uuid
from typing import Callable, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from ..utils.json_rpc import JsonRpcHandler, JsonRpcMessage


class StreamableHttpTransport:
    """Transport mechanism using Streamable HTTP as per MCP specification"""

    def __init__(self, rpc_handler: JsonRpcHandler, host: str = "127.0.0.1", port: int = 3030):
        self.rpc_handler = rpc_handler
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        self.message_callback: Optional[Callable[[JsonRpcMessage], None]] = None

        # For Streamable HTTP, we don't maintain persistent connections like SSE
        # Instead, each POST request gets a direct response
        self.session_states: Dict[str, Dict] = {}  # Track session-specific state
        
        # For handling notifications in Streamable HTTP, we queue them to be sent
        # as part of the next response to a client request
        self.notification_queues: Dict[str, asyncio.Queue] = {}

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes for Streamable HTTP transport"""
        # Single endpoint that supports both POST and GET methods
        @self.app.post("/mcp")
        async def handle_post_request(request: Request):
            """Handle client-to-server communication via POST"""
            try:
                # Verify origin header for security (prevent DNS rebinding attacks)
                origin = request.headers.get("Origin")
                if origin:
                    # Basic origin validation - in production, this should be more robust
                    if not origin.startswith(("http://", "https://")):
                        raise HTTPException(status_code=403, detail="Invalid Origin header")

                # Get session ID from header
                session_id = request.headers.get("MCP-Session-Id") or request.headers.get("X-MCP-Session-ID")
                if not session_id:
                    # Generate a new session ID if none provided
                    session_id = str(uuid.uuid4())

                # Create notification queue for this session if it doesn't exist
                if session_id not in self.notification_queues:
                    self.notification_queues[session_id] = asyncio.Queue()

                body = await request.json()
                message = self.rpc_handler.parse_message(json.dumps(body))

                # Process the message and get response directly
                # Since we're in an async context, use async handler
                response = None
                if self.message_callback:
                    response = await self.rpc_handler.handle_message_async(message)

                # Check if there are any queued notifications for this session
                notifications = []
                notification_queue = self.notification_queues.get(session_id, [])
                
                # Get all available notifications from the queue
                import threading
                with threading.Lock():
                    if isinstance(notification_queue, list):
                        # For list-based queue, get all items and clear the list
                        notifications = notification_queue[:]
                        self.notification_queues[session_id] = []  # Clear the list
                    else:
                        # For asyncio queue, get all available notifications
                        try:
                            while True:
                                notification = notification_queue.get_nowait()
                                notifications.append(notification)
                        except:
                            pass  # No more notifications in queue

                # Prepare response
                if response:
                    response_content = response.to_json()
                else:
                    response_content = json.dumps({"status": "processed"})

                # If there are notifications, we need to send them along with the response
                if notifications:
                    # For Streamable HTTP, we can return multiple responses or embed notifications
                    # The proper way is to return the primary response, but also include any pending notifications
                    # In practice, we'll return the main response and client should make additional requests for notifications
                    response_obj = json.loads(response_content)
                    
                    # Add notifications to the response if there are any
                    if notifications:
                        response_obj["notifications"] = [n.to_json() for n in notifications]
                    
                    return Response(content=json.dumps(response_obj), media_type="application/json")
                else:
                    return Response(content=response_content, media_type="application/json")

            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid message: {str(e)}")

        @self.app.get("/mcp")
        async def handle_get_request(request: Request):
            """Handle server-to-client communication - return connection info for Streamable HTTP"""
            # For Streamable HTTP, GET requests should return connection/metadata information
            # not an SSE stream. This is a key difference from legacy HTTP/SSE transport.
            
            # Get session ID from header or query parameter
            session_id = (request.headers.get("MCP-Session-Id") or
                         request.headers.get("X-MCP-Session-ID") or
                         request.query_params.get("session_id"))

            if not session_id:
                # Generate a new session ID if none provided
                session_id = str(uuid.uuid4())

            # Store session information
            import time
            self.session_states[session_id] = {
                "connected_at": time.time(),
                "request": request
            }

            # For true Streamable HTTP, GET should return connection metadata, not an event stream
            # This allows clients to understand the endpoint capabilities
            return {
                "endpoint": "/mcp",
                "supported_methods": ["POST", "GET"],
                "transport": "streamable-http",
                "session_id": session_id,
                "capabilities": {
                    "bidirectional": True,
                    "json_rpc_2.0": True,
                    "session_support": True
                }
            }

        # Metrics endpoint for monitoring
        @self.app.get("/metrics")
        async def get_metrics(request: Request):
            try:
                from ..utils.json_rpc import get_monitor
                monitor = get_monitor()
                metrics = monitor.get_metrics()
                return metrics
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

        # Health check endpoint
        @self.app.get("/health")
        async def health_check(request: Request):
            try:
                # Check if the server is running
                if not self.running:
                    return {"status": "error", "server": "stopped"}
                
                # Check if we can reach the LLM (LM Studio)
                import httpx
                # Import settings from the config module
                import importlib.util
                import os
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.py')
                spec = importlib.util.spec_from_file_location("config", config_path)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)
                settings = config_module.settings
                
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        response = await client.get(f"{settings.llm_base_url}/models")
                        if response.status_code == 200:
                            return {"status": "ok", "llm": "reachable", "server": "running"}
                        else:
                            return {"status": "degraded", "llm": "unreachable", "server": "running"}
                except Exception:
                    return {"status": "degraded", "llm": "unreachable", "server": "running"}
                    
            except Exception as e:
                return {"status": "error", "error": str(e)}


    def start(self, message_callback: Callable[[JsonRpcMessage], None]):
        """Start the Streamable HTTP transport server"""
        self.message_callback = message_callback
        self.running = True

        def run_server():
            import uvicorn
            uvicorn.run(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def stop(self):
        """Stop the Streamable HTTP transport server"""
        self.running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)

    def send_message_to_session(self, message: JsonRpcMessage, session_id: str):
        """Queue notification to be sent to a specific session when it makes its next request"""
        # Create a simple queue-like structure using a list for thread safety
        if session_id not in self.notification_queues:
            # Use a simple list as a queue for thread safety
            self.notification_queues[session_id] = []
        
        # Append the message to the session's queue
        import threading
        with threading.Lock():  # Use lock for thread safety
            if isinstance(self.notification_queues[session_id], list):
                self.notification_queues[session_id].append(message)
            else:
                # If it's an asyncio queue, try to add to it
                try:
                    self.notification_queues[session_id].put_nowait(message)
                except:
                    # Fallback to list
                    self.notification_queues[session_id] = [message]

    def send_message(self, message: JsonRpcMessage):
        """Queue notification to be sent to all sessions when they make their next request"""
        # Add the message to all active session queues
        import threading
        for session_id in list(self.notification_queues.keys()):  # Use list to avoid modification during iteration
            with threading.Lock():
                if isinstance(self.notification_queues[session_id], list):
                    self.notification_queues[session_id].append(message)
                else:
                    # If it's an asyncio queue, try to add to it
                    try:
                        self.notification_queues[session_id].put_nowait(message)
                    except:
                        # Fallback to list
                        self.notification_queues[session_id] = [message]

    def get_session_headers(self, session_id: str) -> Dict[str, str]:
        """Get headers that a client should include to identify itself"""
        return {
            "MCP-Session-Id": session_id,
            "Content-Type": "application/json"
        }

    def send_error(self, error_msg: str):
        """Log error message"""
        print(f"[Streamable HTTP Transport Error] {error_msg}")

    def _send_response(self, response):
        """In Streamable HTTP, responses are sent directly as HTTP responses to requests"""
        # This method is not used in the traditional sense for Streamable HTTP
        # since responses are returned directly from the POST handler
        # This is kept for compatibility with the server interface
        print("[Streamable HTTP] Response should be sent directly from request handler.")