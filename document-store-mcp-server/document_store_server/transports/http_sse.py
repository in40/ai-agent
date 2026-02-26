"""
HTTP/SSE Transport for MCP Server (Legacy)
Implements HTTP with Server-Sent Events transport as per MCP specification
This is the legacy transport method, maintained for backward compatibility.
"""
import json
import asyncio
import threading
import uuid
from typing import Callable, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from ..utils.json_rpc import JsonRpcHandler, JsonRpcMessage
from ..utils.json_rpc import get_monitor


class HttpSseTransport:
    """Transport mechanism using HTTP with Server-Sent Events as per MCP specification"""

    def __init__(self, rpc_handler: JsonRpcHandler, host: str = "127.0.0.1", port: int = 3030):
        self.rpc_handler = rpc_handler
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        self.message_callback: Optional[Callable[[JsonRpcMessage], None]] = None

        # Connection state
        self.active_connections: Dict[str, Any] = {}
        self.client_message_queues: Dict[str, asyncio.Queue] = {}
        # Track which SSE connection should receive responses for which request
        self.request_to_client_map: Dict[str, str] = {}
        # Track SSE connection sessions
        self.sse_sessions: Dict[str, Dict] = {}

        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes for HTTP/SSE transport"""
        # SSE endpoint for server messages
        @self.app.get("/sse")
        async def sse_endpoint(request: Request):
            # Generate a unique session ID for this SSE connection
            session_id = str(uuid.uuid4())
            return EventSourceResponse(
                self._event_generator(request, session_id),
                ping=10,  # Send ping every 10 seconds
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )

        # HTTP GET endpoint for monitoring and diagnostics
        @self.app.get("/metrics")
        async def get_metrics(request: Request):
            try:
                monitor = get_monitor()
                metrics = monitor.get_metrics()
                return metrics
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

        # HTTP POST endpoint for client messages (both /send and /message for compatibility)
        @self.app.post("/send")
        async def send_message_legacy(request: Request):
            return await self._handle_send_message(request)

        @self.app.post("/message")
        async def send_message_standard(request: Request):
            return await self._handle_send_message(request)

    async def _handle_send_message(self, request: Request):
        """Common handler for both /send and /message endpoints"""
        try:
            body = await request.json()
            message = self.rpc_handler.parse_message(json.dumps(body))

            # Process the message using the message callback
            # The response will be handled by the callback and sent via SSE
            if self.message_callback:
                # If this is a request (has an ID), track which client should receive the response
                if hasattr(message, 'get_id') and message.get_id():
                    # Check if the client provided a session ID in the request headers
                    client_session_id = request.headers.get('X-MCP-Session-ID')

                    # If no session ID provided, try to determine the most likely client
                    if not client_session_id and len(self.active_connections) == 1:
                        # If only one client is connected, assume it's that client
                        client_session_id = next(iter(self.active_connections.keys()))
                    elif not client_session_id and len(self.active_connections) > 1:
                        # If multiple clients are connected and no session ID provided,
                        # we'll send to all clients (current behavior)
                        # But let's try to use the most recently connected client as a heuristic
                        # Sort connections by connection time and pick the most recent
                        if self.sse_sessions:
                            # Get the most recently connected client
                            most_recent = max(self.sse_sessions.items(),
                                            key=lambda x: x[1].get('connected_at', 0))
                            client_session_id = most_recent[0]

                    # Map the request ID to the client session ID if we have one
                    if client_session_id and client_session_id in self.active_connections:
                        self.request_to_client_map[message.get_id()] = client_session_id

                # Handle async message callback if needed
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(message)
                else:
                    self.message_callback(message)

            return {"status": "received"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid message: {str(e)}")

    async def _event_generator(self, request: Request, session_id: str):
        """Generate Server-Sent Events for connected clients"""
        client_id = session_id  # Use the session ID as the client identifier

        # Add to active connections
        self.active_connections[client_id] = request
        self.client_message_queues[client_id] = asyncio.Queue()

        # Add session info to track this connection
        self.sse_sessions[client_id] = {
            "connected_at": asyncio.get_event_loop().time(),
            "request": request
        }

        # Send endpoint event as per MCP spec - this tells the client where to send messages
        yield {
            "event": "endpoint",
            "data": json.dumps({
                "uri": f"http://{self.host}:{self.port}/message",  # Standard legacy endpoint name
                "sessionId": client_id  # Include the session ID for client correlation
            })
        }

        try:
            # Keep connection alive and send messages as they arrive
            while self.running and client_id in self.active_connections:
                try:
                    # Wait for a message with timeout
                    message = await asyncio.wait_for(
                        self.client_message_queues[client_id].get(),
                        timeout=1.0
                    )

                    if isinstance(message, JsonRpcMessage):
                        yield {
                            "event": "message",
                            "data": message.to_json()
                        }
                except asyncio.TimeoutError:
                    # Send a ping to keep connection alive
                    yield ": ping\n"
                    continue
        except Exception:
            pass
        finally:
            # Clean up connection
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.client_message_queues:
                del self.client_message_queues[client_id]
            if client_id in self.sse_sessions:
                del self.sse_sessions[client_id]
            # Remove any request mappings for this client
            requests_to_remove = []
            for req_id, mapped_client_id in self.request_to_client_map.items():
                if mapped_client_id == client_id:
                    requests_to_remove.append(req_id)
            for req_id in requests_to_remove:
                del self.request_to_client_map[req_id]

    def start(self, message_callback: Callable[[JsonRpcMessage], None]):
        """Start the HTTP/SSE transport server"""
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
        """Stop the HTTP/SSE transport server"""
        self.running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)

    def send_message_to_client(self, message: JsonRpcMessage, client_id: Optional[str] = None):
        """Send a message to a specific client or all clients"""
        if not self.running:
            return

        if client_id and client_id in self.client_message_queues:
            # Send to specific client
            asyncio.create_task(self.client_message_queues[client_id].put(message))
        else:
            # Send to all connected clients
            for queue in self.client_message_queues.values():
                asyncio.create_task(queue.put(message))

    def send_message(self, message: JsonRpcMessage):
        """Send a message to all clients (for compatibility with base transport interface)"""
        self.send_message_to_client(message)

    def get_client_headers(self, client_id: str) -> Dict[str, str]:
        """Get headers that a client should include to identify itself"""
        return {
            "X-MCP-Session-ID": client_id,
            "Content-Type": "application/json"
        }

    def send_error(self, error_msg: str):
        """Log error message"""
        print(f"[HTTP/SSE Transport Error] {error_msg}")

    def _send_response(self, response):
        """Send response back to the appropriate client (for server compatibility)"""
        # Improved approach: try to send to the client that made the request
        # First, check if we have a mapping for this response's request ID
        if hasattr(response, 'id') and response.id:
            # Look for the client that should receive this response
            if response.id in self.request_to_client_map:
                client_id = self.request_to_client_map[response.id]
                if client_id in self.client_message_queues:
                    asyncio.create_task(self.client_message_queues[client_id].put(response))
                    # Remove the mapping after sending
                    del self.request_to_client_map[response.id]
                    return

        # If no specific client found, send to all connected clients
        for queue in self.client_message_queues.values():
            asyncio.create_task(queue.put(response))