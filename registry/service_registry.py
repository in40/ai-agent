#!/usr/bin/env python3
"""
MCP Service Registry - Central registry for MCP services to register and discover each other
"""

import json
import threading
import time
import logging
import socket
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver
import argparse


@dataclass
class ServiceInfo:
    """Data class representing information about a registered service"""
    id: str              # Unique service identifier
    host: str            # Service host address
    port: int            # Service port
    type: str = "mcp"    # Service type
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class HeartbeatFilter(logging.Filter):
    """Custom filter to suppress heartbeat messages"""

    def filter(self, record):
        # Suppress heartbeat-related messages
        message = record.getMessage()
        if "Heartbeat received for service" in message or "HTTP \"PUT /heartbeat" in message:
            return False
        return True


class ServiceRegistry:
    """Core class that manages the registry of services"""

    def __init__(self):
        self.services: Dict[str, Dict[str, Any]] = {}  # Dictionary to store service information
        self.lock = threading.RLock()  # Thread-safe lock for concurrent access
        self.cleanup_interval = 30  # Interval for cleaning up expired services (in seconds)

        # Start the cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_services, daemon=True)
        self.cleanup_thread.start()

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            # Add the heartbeat filter to suppress heartbeat messages
            handler.addFilter(HeartbeatFilter())
            self.logger.addHandler(handler)

    def register_service(self, service_info: ServiceInfo, ttl: int) -> bool:
        """Register a service with the registry"""
        with self.lock:
            try:
                # Calculate expiration time
                expiration_time = datetime.now() + timedelta(seconds=ttl)
                
                # Store service information
                self.services[service_info.id] = {
                    'id': service_info.id,
                    'host': service_info.host,
                    'port': service_info.port,
                    'type': service_info.type,
                    'metadata': service_info.metadata or {},
                    'expiration_time': expiration_time,
                    'registered_at': datetime.now()
                }
                
                self.logger.info(f"Service {service_info.id} registered successfully. Expires at {expiration_time}")
                return True
            except Exception as e:
                self.logger.error(f"Error registering service {service_info.id}: {str(e)}")
                return False

    def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from the registry"""
        with self.lock:
            try:
                if service_id in self.services:
                    del self.services[service_id]
                    self.logger.info(f"Service {service_id} unregistered successfully")
                    return True
                else:
                    self.logger.warning(f"Attempted to unregister non-existent service {service_id}")
                    return False
            except Exception as e:
                self.logger.error(f"Error unregistering service {service_id}: {str(e)}")
                return False

    def heartbeat(self, service_id: str, ttl: int) -> bool:
        """Update service heartbeat to extend expiration time"""
        with self.lock:
            try:
                if service_id in self.services:
                    # Extend expiration time
                    expiration_time = datetime.now() + timedelta(seconds=ttl)
                    self.services[service_id]['expiration_time'] = expiration_time
                    self.logger.info(f"Heartbeat received for service {service_id}. Expires at {expiration_time}")
                    return True
                else:
                    self.logger.warning(f"Heartbeat for non-existent service {service_id}")
                    return False
            except Exception as e:
                self.logger.error(f"Error processing heartbeat for service {service_id}: {str(e)}")
                return False

    def discover_services(self, service_type: Optional[str] = None, metadata_filters: Optional[Dict[str, Any]] = None) -> List[ServiceInfo]:
        """Discover services based on type and metadata filters"""
        with self.lock:
            try:
                current_time = datetime.now()
                active_services = []
                
                for service_id, service_data in self.services.items():
                    # Skip expired services
                    if service_data['expiration_time'] < current_time:
                        continue
                    
                    # Apply type filter if specified
                    if service_type and service_data['type'] != service_type:
                        continue
                    
                    # Apply metadata filters if specified
                    if metadata_filters:
                        match = True
                        for key, value in metadata_filters.items():
                            if key not in service_data['metadata'] or service_data['metadata'][key] != value:
                                match = False
                                break
                        if not match:
                            continue
                    
                    # Add matching service to results
                    service_info = ServiceInfo(
                        id=service_data['id'],
                        host=service_data['host'],
                        port=service_data['port'],
                        type=service_data['type'],
                        metadata=service_data['metadata']
                    )
                    active_services.append(service_info)
                
                self.logger.info(f"Discovered {len(active_services)} services matching criteria")
                return active_services
            except Exception as e:
                self.logger.error(f"Error discovering services: {str(e)}")
                return []

    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get specific service by ID"""
        with self.lock:
            try:
                if service_id in self.services:
                    service_data = self.services[service_id]
                    # Check if service is still active
                    if service_data['expiration_time'] >= datetime.now():
                        return ServiceInfo(
                            id=service_data['id'],
                            host=service_data['host'],
                            port=service_data['port'],
                            type=service_data['type'],
                            metadata=service_data['metadata']
                        )
                    else:
                        # Service has expired, remove it
                        del self.services[service_id]
                        self.logger.info(f"Expired service {service_id} removed from registry")
                        return None
                else:
                    return None
            except Exception as e:
                self.logger.error(f"Error getting service {service_id}: {str(e)}")
                return None

    def list_all_services(self) -> List[ServiceInfo]:
        """List all active services in the registry"""
        with self.lock:
            try:
                current_time = datetime.now()
                active_services = []
                
                for service_id, service_data in self.services.items():
                    # Skip expired services
                    if service_data['expiration_time'] < current_time:
                        continue
                    
                    service_info = ServiceInfo(
                        id=service_data['id'],
                        host=service_data['host'],
                        port=service_data['port'],
                        type=service_data['type'],
                        metadata=service_data['metadata']
                    )
                    active_services.append(service_info)
                
                self.logger.info(f"Listed {len(active_services)} active services")
                return active_services
            except Exception as e:
                self.logger.error(f"Error listing all services: {str(e)}")
                return []

    def _cleanup_expired_services(self):
        """Background thread to periodically remove expired services"""
        while True:
            try:
                current_time = datetime.now()
                expired_services = []
                
                with self.lock:
                    for service_id, service_data in self.services.items():
                        if service_data['expiration_time'] < current_time:
                            expired_services.append(service_id)
                    
                    for service_id in expired_services:
                        del self.services[service_id]
                        self.logger.info(f"Removed expired service {service_id}")
                
                # Sleep for cleanup interval
                time.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error during cleanup of expired services: {str(e)}")
                time.sleep(self.cleanup_interval)


class ServiceRegistryHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler that processes registry API requests"""

    def log_message(self, format, *args):
        """Override log_message to use our logger"""
        # Access the registry through the server instance
        registry = self.server.registry
        message = f"HTTP {format % args} from {self.client_address[0]}"
        # Only log if it's not a heartbeat message
        if not ("PUT /heartbeat" in message and "200" in message):
            registry.logger.info(message)

    def _send_response(self, status_code: int, data: Any):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_body = json.dumps(data, default=str)
        self.wfile.write(response_body.encode())

    def _parse_json_body(self):
        """Parse JSON request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode()
        return json.loads(body)

    def do_POST(self):
        """Handle registration requests"""
        if self.path == '/register':
            try:
                # Access the registry through the server instance
                registry = self.server.registry

                # Parse request body
                request_data = self._parse_json_body()

                # Validate required fields
                required_fields = ['id', 'host', 'port', 'type', 'ttl']
                for field in required_fields:
                    if field not in request_data:
                        self._send_response(400, {
                            'success': False,
                            'message': f'Missing required field: {field}'
                        })
                        return

                # Create ServiceInfo object
                service_info = ServiceInfo(
                    id=request_data['id'],
                    host=request_data['host'],
                    port=request_data['port'],
                    type=request_data['type'],
                    metadata=request_data.get('metadata')
                )

                # Register the service
                ttl = request_data['ttl']
                success = registry.register_service(service_info, ttl)

                if success:
                    self._send_response(200, {
                        'success': True,
                        'message': f'Service {service_info.id} registered successfully'
                    })
                else:
                    self._send_response(500, {
                        'success': False,
                        'message': f'Failed to register service {service_info.id}'
                    })
            except json.JSONDecodeError:
                self._send_response(400, {
                    'success': False,
                    'message': 'Invalid JSON in request body'
                })
            except Exception as e:
                registry.logger.error(f"Error handling registration: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        else:
            self._send_response(404, {
                'success': False,
                'message': 'Endpoint not found'
            })

    def do_DELETE(self):
        """Handle unregistration requests"""
        if self.path.startswith('/unregister/'):
            try:
                # Access the registry through the server instance
                registry = self.server.registry

                # Extract service ID from path
                service_id = self.path.split('/')[-1]

                # Unregister the service
                success = registry.unregister_service(service_id)

                if success:
                    self._send_response(200, {
                        'success': True,
                        'message': f'Service {service_id} unregistered successfully'
                    })
                else:
                    self._send_response(404, {
                        'success': False,
                        'message': f'Service {service_id} not found'
                    })
            except Exception as e:
                registry.logger.error(f"Error handling unregistration: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        else:
            self._send_response(404, {
                'success': False,
                'message': 'Endpoint not found'
            })

    def do_PUT(self):
        """Handle heartbeat requests"""
        if self.path == '/heartbeat':
            try:
                # Access the registry through the server instance
                registry = self.server.registry

                # Parse request body
                request_data = self._parse_json_body()

                # Validate required fields
                if 'id' not in request_data or 'ttl' not in request_data:
                    self._send_response(400, {
                        'success': False,
                        'message': 'Missing required fields: id, ttl'
                    })
                    return

                # Process heartbeat
                service_id = request_data['id']
                ttl = request_data['ttl']
                success = registry.heartbeat(service_id, ttl)

                if success:
                    self._send_response(200, {
                        'success': True,
                        'message': f'Heartbeat processed for service {service_id}'
                    })
                else:
                    self._send_response(404, {
                        'success': False,
                        'message': f'Service {service_id} not found'
                    })
            except json.JSONDecodeError:
                self._send_response(400, {
                    'success': False,
                    'message': 'Invalid JSON in request body'
                })
            except Exception as e:
                registry.logger.error(f"Error handling heartbeat: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        else:
            self._send_response(404, {
                'success': False,
                'message': 'Endpoint not found'
            })

    def do_GET(self):
        """Handle discovery and health check requests"""
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')

        # Access the registry through the server instance
        registry = self.server.registry

        if parsed_path.path == '/discover':
            # Handle service discovery
            try:
                # Parse query parameters
                query_params = parse_qs(parsed_path.query)

                # Extract service type filter
                service_type = query_params.get('type', [None])[0]

                # Extract metadata filters
                metadata_filters = {}
                for key, value_list in query_params.items():
                    if key.startswith('meta_'):
                        metadata_key = key[5:]  # Remove 'meta_' prefix
                        metadata_filters[metadata_key] = value_list[0] if value_list else None

                # Discover services
                services = registry.discover_services(service_type, metadata_filters)

                # Convert to dictionaries for JSON serialization
                services_dict = [asdict(service) for service in services]

                self._send_response(200, {
                    'success': True,
                    'services': services_dict
                })
            except Exception as e:
                registry.logger.error(f"Error handling discovery: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        elif parsed_path.path.startswith('/services/'):
            # Handle specific service retrieval
            try:
                service_id = path_parts[-1]
                service = registry.get_service(service_id)

                if service:
                    self._send_response(200, {
                        'success': True,
                        'service': asdict(service)
                    })
                else:
                    self._send_response(404, {
                        'success': False,
                        'message': f'Service {service_id} not found'
                    })
            except Exception as e:
                registry.logger.error(f"Error getting specific service: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        elif parsed_path.path == '/services':
            # Handle list all services
            try:
                services = registry.list_all_services()
                services_dict = [asdict(service) for service in services]

                self._send_response(200, {
                    'success': True,
                    'services': services_dict
                })
            except Exception as e:
                registry.logger.error(f"Error listing all services: {str(e)}")
                self._send_response(500, {
                    'success': False,
                    'message': f'Internal server error: {str(e)}'
                })
        elif parsed_path.path == '/health':
            # Handle health check
            try:
                self._send_response(200, {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'active_services': len(registry.list_all_services())
                })
            except Exception as e:
                registry.logger.error(f"Error handling health check: {str(e)}")
                self._send_response(500, {
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        else:
            self._send_response(404, {
                'success': False,
                'message': 'Endpoint not found'
            })


class ServiceRegistryServer:
    """HTTP server wrapper that binds the registry to a network interface"""

    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        self.host = host
        self.port = port
        self.registry = ServiceRegistry()
        self.httpd = None

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            # Add the heartbeat filter to suppress heartbeat messages
            handler.addFilter(HeartbeatFilter())
            self.logger.addHandler(handler)

    def start(self):
        """Start the HTTP server"""
        httpd = None
        try:
            # Create a custom handler class that has access to the registry
            class Handler(ServiceRegistryHTTPHandler):
                def setup(self):
                    # Call the parent setup method
                    super().setup()

                def log_message(self, format, *args):
                    # Access the registry through the server instance
                    registry = self.server.registry
                    registry.logger.info(f"HTTP {format % args} from {self.client_address[0]}")

            # Create the HTTP server with address reuse enabled
            # We need to ensure SO_REUSEADDR is set before binding
            class ReusableTCPServer(socketserver.ThreadingTCPServer):
                def server_bind(self):
                    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    super().server_bind()

            httpd = ReusableTCPServer((self.host, self.port), Handler)

            # Attach the registry to the server so handlers can access it
            httpd.registry = self.registry

            self.logger.info(f"Starting MCP Service Registry on {self.host}:{self.port}")
            self.logger.info(f"Registry server is running. Press Ctrl+C to stop.")

            # Serve forever
            httpd.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal. Shutting down...")
            if httpd:
                httpd.shutdown()  # Properly shutdown the server
                httpd.server_close()  # Close the server socket
        except Exception as e:
            self.logger.error(f"Error starting server: {str(e)}")
            if httpd:
                httpd.shutdown()  # Properly shutdown the server
                httpd.server_close()  # Close the server socket
            raise

    def stop(self):
        """Stop the HTTP server"""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()  # Ensure the socket is closed


def main():
    """Main function to start the service registry server"""
    parser = argparse.ArgumentParser(description='MCP Service Registry Server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--cleanup-interval', type=int, default=30, help='Cleanup interval in seconds (default: 30)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start the registry server
    server = ServiceRegistryServer(host=args.host, port=args.port)
    server.registry.cleanup_interval = args.cleanup_interval
    
    try:
        server.start()
    except Exception as e:
        print(f"Failed to start server: {e}")
        exit(1)


if __name__ == '__main__':
    main()