"""Document Store MCP Server Implementation"""
import signal
import sys
import json
from typing import Optional
import argparse
import atexit

from document_store_server.utils.json_rpc import JsonRpcHandler
from document_store_server.transports.stdio import StdioTransport
from document_store_server.transports.http_sse import HttpSseTransport
from document_store_server.transports.streamable_http import StreamableHttpTransport
from document_store_server.handlers.server_handlers import DocumentStoreServerHandlers
from document_store_server.handlers.client_handlers import ClientMethodsHandlers
from document_store_server.utils.notifications import NotificationManager
from document_store_server.utils.ai_agent_registry import AIAgentRegistryIntegration

import config
from config import SERVER_HOST, SERVER_PORT, TRANSPORT_TYPE, REGISTER_WITH_REGISTRY, REGISTRY_HOST, REGISTRY_PORT


class DocumentStoreMcpServer:
    """Document Store MCP Server"""

    def __init__(self, transport_type: str = "streamable-http"):
        self.transport_type = transport_type
        self.host = config.SERVER_HOST
        self.port = config.SERVER_PORT
        self.running = False
        
        # Initialize components
        self.rpc_handler = JsonRpcHandler()
        self.notification_manager = NotificationManager(self.rpc_handler)

        # Initialize handlers
        self.client_handlers = ClientMethodsHandlers(self.rpc_handler)
        self.server_handlers = DocumentStoreServerHandlers(
            enable_registry=config.ENABLE_REGISTRY,
            notification_manager=self.notification_manager
        )
        
        # Register MCP request handlers
        async def handle_list_tools(params, request_id):
            return {"tools": self.server_handlers.get_tools()}
        
        async def handle_call_tool(params, request_id):
            name = params.get("name")
            arguments = params.get("arguments", {})
            result = await self.server_handlers.handle_tool(name, arguments)
            return {
                "content": [{"type": "text", "text": json.dumps(result)}]
            }
        
        self.rpc_handler.register_request_handler("tools/list", handle_list_tools)
        self.rpc_handler.register_request_handler("tools/call", handle_call_tool)

        # Initialize ai_agent registry integration
        self.registry_integration = None
        if config.ENABLE_REGISTRY:
            registry_url = f"http://{config.REGISTRY_HOST}:{config.REGISTRY_PORT}"
            self.registry_integration = AIAgentRegistryIntegration(registry_url)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
        
        print(f"📦 Document Store MCP Server initialized")
        print(f"   Storage: {config.STORAGE_BASE}")
        print(f"   Max document size: {config.MAX_DOCUMENT_SIZE_MB}MB")
        print(f"   Max batch size: {config.MAX_BATCH_SIZE}")
        if config.ENABLE_REGISTRY:
            print(f"   Registry: {registry_url}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down Document Store Server...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup resources on shutdown"""
        if self.registry_integration:
            self.registry_integration.unregister()

    def send_notification(self, notification):
        """Send a notification to clients"""
        # For now, just log it - notifications are handled by the transport
        pass

    def start(self):
        """Start the server"""
        print(f"\n🚀 Starting Document Store MCP Server...")
        print(f"   Host: {self.host}")
        print(f"   Port: {self.port}")
        print(f"   Transport: {self.transport_type}")
        print(f"   Registry: {'Enabled' if config.ENABLE_REGISTRY else 'Disabled'}")
        print(f"\n📋 Available Tools:")
        for tool in self.server_handlers.get_tools():
            print(f"   - {tool['name']}")
        
        # Register with ai_agent registry
        if config.ENABLE_REGISTRY and self.registry_integration:
            self.registry_integration.register(
                host=self.host,
                port=self.port,
                ttl=60
            )
        
        print(f"\n✅ Server ready to accept connections\n")
        
        # Create transport
        if self.transport_type == "stdio":
            transport = StdioTransport(self.rpc_handler)
        elif self.transport_type == "http":
            transport = HttpSseTransport(
                host=self.host,
                port=self.port,
                rpc_handler=self.rpc_handler
            )
        else:  # streamable-http
            transport = StreamableHttpTransport(
                host=self.host,
                port=self.port,
                rpc_handler=self.rpc_handler
            )

        # Start server
        self.running = True
        transport.start(self.send_notification)


def main():
    parser = argparse.ArgumentParser(description="Document Store MCP Server")
    parser.add_argument(
        "--transport", 
        default=config.TRANSPORT_TYPE,
        choices=["stdio", "http", "streamable-http"],
        help="Transport type"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.SERVER_PORT,
        help="Server port"
    )
    parser.add_argument(
        "--host",
        default=config.SERVER_HOST,
        help="Server host"
    )
    parser.add_argument(
        "--registry-host",
        default=config.REGISTRY_HOST,
        help="Registry host"
    )
    parser.add_argument(
        "--registry-port",
        type=int,
        default=config.REGISTRY_PORT,
        help="Registry port"
    )
    
    args = parser.parse_args()

    # Override config if provided
    if args.port:
        config.SERVER_PORT = args.port
    if args.host:
        config.SERVER_HOST = args.host
    if args.registry_host:
        config.REGISTRY_HOST = args.registry_host
    if args.registry_port:
        config.REGISTRY_PORT = args.registry_port

    server = DocumentStoreMcpServer(transport_type=args.transport)
    server.start()
    
    # Keep the server running
    import time
    try:
        while server.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Received keyboard interrupt, shutting down...")
        server.running = False
        server.cleanup()


if __name__ == "__main__":
    main()
