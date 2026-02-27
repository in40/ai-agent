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

                body = await request.json()
                message = self.rpc_handler.parse_message(json.dumps(body))

                # Process the message and get response directly
                if self.message_callback:
                    # For Streamable HTTP, we handle the message and return the response directly
                    # Use sync handler for consistency
                    response = self.rpc_handler.handle_message_sync(message)
                    if response:
                        return Response(content=response.to_json(), media_type="application/json")
                    else:
                        return Response(content=json.dumps({"status": "processed"}), media_type="application/json")
                else:
                    return Response(content=json.dumps({"status": "no callback"}), media_type="application/json")

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
        """In Streamable HTTP, messages are sent as responses to requests, not separately"""
        # In true Streamable HTTP, server-initiated messages are not supported in the same way
        # as with SSE. Server messages are sent as responses to client requests.
        # This method exists for interface compatibility but doesn't actively send messages.
        print(f"[Streamable HTTP] Cannot send message to session {session_id} directly. "
              f"Messages must be sent as responses to client requests.")

    def send_message(self, message: JsonRpcMessage):
        """In Streamable HTTP, messages are sent as responses to requests, not separately"""
        # Same as above - for compatibility only
        print("[Streamable HTTP] Cannot send message directly. "
              "Messages must be sent as responses to client requests.")

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