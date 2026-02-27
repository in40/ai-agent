"""
JSON-RPC 2.0 Handler for MCP Server
Implements the core JSON-RPC 2.0 message handling with concurrency control
"""
import json
import asyncio
import threading
from typing import Dict, Any, Callable, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time
import uuid


class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"


@dataclass
class JsonRpcMessage:
    """Represents a JSON-RPC 2.0 message"""
    message_type: MessageType
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

    def to_json(self) -> str:
        """Convert the message to JSON string"""
        obj = {"jsonrpc": self.jsonrpc}
        
        if self.message_type == MessageType.REQUEST:
            obj["id"] = self.id
            obj["method"] = self.method
            if self.params is not None:
                obj["params"] = self.params
        elif self.message_type == MessageType.RESPONSE:
            obj["id"] = self.id
            if self.result is not None:
                obj["result"] = self.result
            elif self.error is not None:
                obj["error"] = self.error
        elif self.message_type == MessageType.NOTIFICATION:
            obj["method"] = self.method
            if self.params is not None:
                obj["params"] = self.params
        
        return json.dumps(obj, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JsonRpcMessage':
        """Create a JsonRpcMessage from a dictionary"""
        message_type = MessageType.REQUEST  # Default to request
        
        if "id" in data:
            if "result" in data or "error" in data:
                message_type = MessageType.RESPONSE
            else:
                message_type = MessageType.REQUEST
        else:
            message_type = MessageType.NOTIFICATION
            
        return cls(
            message_type=message_type,
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )

    def get_id(self) -> Optional[Union[str, int]]:
        """Get the message ID"""
        return self.id


class ConcurrencyMonitor:
    """Monitor and control concurrent requests"""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.current_requests = 0
        self.total_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
        self.lock = threading.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
    
    async def acquire_request_slot(self):
        """Acquire a slot for a new request"""
        await self.semaphore.acquire()
        with self.lock:
            self.current_requests += 1
            self.total_requests += 1
    
    def release_request_slot(self):
        """Release a slot after request completion"""
        with self.lock:
            self.current_requests -= 1
        self.semaphore.release()
    
    def record_failure(self):
        """Record a failed request"""
        with self.lock:
            self.failed_requests += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self.lock:
            return {
                "current_requests": self.current_requests,
                "max_concurrent_requests": self.max_concurrent_requests,
                "total_requests": self.total_requests,
                "failed_requests": self.failed_requests,
                "uptime_seconds": time.time() - self.start_time
            }


# Global monitor instance
_monitor: Optional[ConcurrencyMonitor] = None


def get_monitor() -> ConcurrencyMonitor:
    """Get the global concurrency monitor"""
    global _monitor
    if _monitor is None:
        _monitor = ConcurrencyMonitor()
    return _monitor


def set_monitor(monitor: ConcurrencyMonitor):
    """Set the global concurrency monitor"""
    global _monitor
    _monitor = monitor


class JsonRpcHandler:
    """Handles JSON-RPC 2.0 messages with concurrency control"""

    def __init__(self, max_concurrent_requests: int = 10):
        self.request_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.max_concurrent_requests = max_concurrent_requests
        self.monitor = ConcurrencyMonitor(max_concurrent_requests)
        set_monitor(self.monitor)
        
        # For server-initiated requests to clients
        self.pending_client_requests: Dict[str, asyncio.Future] = {}
        self.transport_layer = None  # Will be set by the server
    
    def register_request_handler(self, method: str, handler: Callable):
        """Register a handler for a specific request method"""
        self.request_handlers[method] = handler
    
    def register_notification_handler(self, method: str, handler: Callable):
        """Register a handler for a specific notification method"""
        self.notification_handlers[method] = handler
    
    def parse_message(self, json_str: str) -> JsonRpcMessage:
        """Parse a JSON string into a JsonRpcMessage"""
        try:
            data = json.loads(json_str)
            return JsonRpcMessage.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Invalid JSON-RPC message: {e}")
    
    async def handle_message_async(self, message: JsonRpcMessage) -> Optional[JsonRpcMessage]:
        """Asynchronously handle a JSON-RPC message"""
        try:
            await self.monitor.acquire_request_slot()
            
            if message.message_type == MessageType.REQUEST:
                return await self._handle_request_async(message)
            elif message.message_type == MessageType.NOTIFICATION:
                await self._handle_notification_async(message)
                return None
            else:
                raise ValueError(f"Cannot handle message type: {message.message_type}")
        except Exception as e:
            self.monitor.record_failure()
            raise
        finally:
            self.monitor.release_request_slot()
    
    def handle_message_sync(self, message: JsonRpcMessage) -> Optional[JsonRpcMessage]:
        """Synchronously handle a JSON-RPC message"""
        try:
            # For sync handling, we'll run the async version in a new event loop
            # or handle it directly without concurrency control for stdio
            if message.message_type == MessageType.REQUEST:
                return self._handle_request_sync(message)
            elif message.message_type == MessageType.NOTIFICATION:
                self._handle_notification_sync(message)
                return None
            else:
                raise ValueError(f"Cannot handle message type: {message.message_type}")
        except Exception as e:
            self.monitor.record_failure()
            raise
    
    async def _handle_request_async(self, message: JsonRpcMessage) -> JsonRpcMessage:
        """Handle a request message asynchronously"""
        method = message.method
        if not method:
            return self._create_error_response(message.id, -32600, "Invalid Request: Missing method")
        
        if method not in self.request_handlers:
            return self._create_error_response(message.id, -32601, f"Method not found: {method}")
        
        try:
            handler = self.request_handlers[method]
            if asyncio.iscoroutinefunction(handler):
                result = await handler(message.params, message.id)
            else:
                result = handler(message.params, message.id)
            
            return JsonRpcMessage(
                message_type=MessageType.RESPONSE,
                id=message.id,
                result=result
            )
        except Exception as e:
            return self._create_error_response(message.id, -32603, f"Internal error: {str(e)}")
    
    def _handle_request_sync(self, message: JsonRpcMessage) -> JsonRpcMessage:
        """Handle a request message synchronously"""
        method = message.method
        if not method:
            return self._create_error_response(message.id, -32600, "Invalid Request: Missing method")
        
        if method not in self.request_handlers:
            return self._create_error_response(message.id, -32601, f"Method not found: {method}")
        
        try:
            handler = self.request_handlers[method]
            if asyncio.iscoroutinefunction(handler):
                # For sync handling of async functions, we need to run them in an event loop
                # However, this can cause issues in some contexts. For now, we'll raise an error
                # to indicate that async handlers should not be used with sync processing
                raise ValueError(f"Async handler not supported in sync context: {method}")
            else:
                result = handler(message.params, message.id)
            
            return JsonRpcMessage(
                message_type=MessageType.RESPONSE,
                id=message.id,
                result=result
            )
        except Exception as e:
            return self._create_error_response(message.id, -32603, f"Internal error: {str(e)}")
    
    async def _handle_notification_async(self, message: JsonRpcMessage):
        """Handle a notification message asynchronously"""
        method = message.method
        if not method:
            # Invalid notification, just ignore
            return
        
        if method in self.notification_handlers:
            handler = self.notification_handlers[method]
            if asyncio.iscoroutinefunction(handler):
                await handler(message.params)
            else:
                handler(message.params)
    
    def _handle_notification_sync(self, message: JsonRpcMessage):
        """Handle a notification message synchronously"""
        method = message.method
        if not method:
            # Invalid notification, just ignore
            return
        
        if method in self.notification_handlers:
            handler = self.notification_handlers[method]
            handler(message.params)
    
    def _create_error_response(self, request_id: Optional[Union[str, int]],
                              code: int, message: str) -> JsonRpcMessage:
        """Create an error response message"""
        return JsonRpcMessage(
            message_type=MessageType.RESPONSE,
            id=request_id,
            error={
                "code": code,
                "message": message
            }
        )

    def set_transport_layer(self, transport_layer):
        """Set the transport layer for sending messages to clients"""
        self.transport_layer = transport_layer

    async def send_request_to_client(self, method: str, params: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
        """
        Send a request to the client and wait for a response.
        This is for server-initiated requests to the client.
        """
        if not self.transport_layer:
            raise RuntimeError("Transport layer not set. Cannot send request to client.")
            
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        
        # Create the request message
        request_message = JsonRpcMessage(
            message_type=MessageType.REQUEST,
            id=request_id,
            method=method,
            params=params
        )
        
        # Create a Future to wait for the response
        future = asyncio.Future()
        self.pending_client_requests[request_id] = future
        
        try:
            # Send the request to the client via the transport layer
            # Check if transport is available before sending
            if hasattr(self.transport_layer, 'running') and not self.transport_layer.running:
                raise RuntimeError("Transport layer is not running. Cannot send request to client.")
            
            self.transport_layer.send_message(request_message)
            
            # Wait for the response with timeout
            response_data = await asyncio.wait_for(future, timeout=timeout)
            return response_data
        except asyncio.TimeoutError:
            # Clean up the pending request
            if request_id in self.pending_client_requests:
                del self.pending_client_requests[request_id]
            raise TimeoutError(f"Timeout waiting for response to {method} request")
        except Exception as e:
            # Clean up the pending request
            if request_id in self.pending_client_requests:
                del self.pending_client_requests[request_id]
            raise e

    def handle_client_response(self, response_message: JsonRpcMessage):
        """
        Handle a response from the client to a server-initiated request.
        """
        request_id = response_message.id
        if request_id in self.pending_client_requests:
            future = self.pending_client_requests[request_id]
            
            if response_message.error:
                # Complete the future with an error
                future.set_exception(Exception(f"Client error: {response_message.error}"))
            else:
                # Complete the future with the result
                future.set_result(response_message.result)
                
            # Remove the pending request
            del self.pending_client_requests[request_id]


# Standard error codes from JSON-RPC 2.0 specification
ERROR_CODES = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,
}