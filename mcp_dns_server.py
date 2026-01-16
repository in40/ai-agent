#!/usr/bin/env python3
"""
MCP DNS Server - An MCP server that resolves FQDNs to IPv4 addresses and registers itself with the service registry
"""

import json
import socket
import threading
import logging
import argparse
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from registry_client import ServiceInfo, MCPServiceWrapper
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse


class DNSRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for DNS resolution requests"""

    # Class variable to hold the resolve function
    resolve_func = None

    @classmethod
    def set_resolve_func(cls, func):
        cls.resolve_func = func

    def do_POST(self):
        """Handle POST requests for DNS resolution"""
        try:
            # Get content length and read the request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Parse the request data
            try:
                request_data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.logger_error(f"Invalid JSON in request: {str(e)}")
                self._send_error_response(400, "Invalid JSON", "unknown")
                return

            # Extract FQDN from request - the parameters might be at the top level
            # or nested inside a 'parameters' field depending on how the client sends it
            if 'fqdn' in request_data:
                fqdn = request_data['fqdn']
            elif 'domain' in request_data:
                fqdn = request_data['domain']
            elif 'parameters' in request_data:
                # If parameters are nested, check inside that object
                params = request_data['parameters']
                if 'fqdn' in params:
                    fqdn = params['fqdn']
                elif 'domain' in params:
                    fqdn = params['domain']
                else:
                    self.logger_error("Missing 'fqdn' or 'domain' in request parameters")
                    self._send_error_response(400, "Missing 'fqdn' or 'domain' in request parameters", "unknown")
                    return
            else:
                self.logger_error("Missing 'fqdn', 'domain', or 'parameters' in request")
                self._send_error_response(400, "Missing 'fqdn', 'domain', or 'parameters' in request", "unknown")
                return

            self.logger_info(f"Resolving FQDN: {fqdn}")

            # Perform DNS resolution using the bound function
            if DNSRequestHandler.resolve_func is None:
                self.logger_error("Resolve function not set")
                self._send_error_response(500, "Server configuration error", "unknown")
                return

            success, ipv4_addresses, error_msg = DNSRequestHandler.resolve_func(fqdn)

            # Create response
            response = {
                "success": True,
                "result": {
                    "success": success,
                    "fqdn": fqdn,
                    "ipv4_addresses": ipv4_addresses,
                    "error": error_msg
                }
            }

            # Send successful response
            self._send_json_response(200, response)

        except Exception as e:
            self.logger_error(f"Error handling request: {str(e)}")
            self._send_error_response(500, f"Internal server error: {str(e)}", "unknown")

    def _send_json_response(self, status_code: int, data: dict):
        """Send a JSON response with appropriate headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        response_json = json.dumps(data)
        self.wfile.write(response_json.encode('utf-8'))

    def _send_error_response(self, status_code: int, error_msg: str, fqdn: str):
        """Send an error response"""
        error_response = {
            "success": False,
            "result": {
                "success": False,
                "fqdn": fqdn,
                "ipv4_addresses": [],
                "error": error_msg
            }
        }
        self._send_json_response(status_code, error_response)

    def logger_info(self, msg):
        """Log an info message"""
        import logging
        logger = logging.getLogger('MCPServer.DNSRequestHandler')
        logger.info(f"HTTP - {msg}")

    def logger_error(self, msg):
        """Log an error message"""
        import logging
        logger = logging.getLogger('MCPServer.DNSRequestHandler')
        logger.error(f"HTTP - {msg}")

    def log_message(self, format, *args):
        """Override to use our logger"""
        import logging
        logger = logging.getLogger('MCPServer.DNSRequestHandler')
        logger.info(f"HTTP - {format % args}")


class MCPServer:
    """Main server class that handles DNS resolution requests"""

    def __init__(self, host: str = '127.0.0.1', port: int = 8089, registry_url: str = 'http://127.0.0.1:8080',
                 service_id: Optional[str] = None, service_ttl: int = 60, log_level: str = 'INFO'):
        self.host = host
        self.port = port
        self.registry_url = registry_url
        self.service_ttl = service_ttl
        self.service_wrapper: Optional[MCPServiceWrapper] = None
        self.httpd: Optional[HTTPServer] = None
        self.running = False

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def resolve_ipv4(self, fqdn: str) -> Tuple[bool, List[str], Optional[str]]:
        """
        Resolve FQDN to IPv4 addresses only
        Returns: (success, ipv4_addresses, error_message)
        """
        try:
            # Use getaddrinfo to get all addresses for the FQDN
            # AF_INET ensures we only get IPv4 addresses
            addr_info = socket.getaddrinfo(fqdn, None, family=socket.AF_INET)
            
            # Extract IPv4 addresses
            ipv4_addresses = []
            for res in addr_info:
                addr = res[4][0]  # Extract IP address from sockaddr tuple
                if addr not in ipv4_addresses:  # Avoid duplicates
                    ipv4_addresses.append(addr)
            
            if ipv4_addresses:
                self.logger.info(f"Resolved {fqdn} to IPv4 addresses: {ipv4_addresses}")
                return True, ipv4_addresses, None
            else:
                error_msg = f"No IPv4 addresses found for {fqdn}"
                self.logger.warning(error_msg)
                return False, [], error_msg
        except socket.gaierror as e:
            error_msg = f"DNS resolution failed for {fqdn}: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg
        except Exception as e:
            error_msg = f"Unexpected error resolving {fqdn}: {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg


    def start(self):
        """Start the DNS server"""
        try:
            # Register with the service registry
            service_id = f"dns-server-{self.host}-{self.port}".replace('.', '-').replace(':', '-')
            service_info = ServiceInfo(
                id=service_id,
                host=self.host,
                port=self.port,
                type="mcp_dns",
                metadata={
                    "service_type": "dns_resolver",
                    "capabilities": ["ipv4_resolution"],
                    "started_at": datetime.now().isoformat()
                }
            )

            self.service_wrapper = MCPServiceWrapper(
                service_info=service_info,
                registry_url=self.registry_url,
                heartbeat_interval=20,  # Send heartbeat every 20 seconds
                ttl=self.service_ttl  # TTL of 60 seconds
            )

            if self.service_wrapper.start():
                self.logger.info(f"DNS server registered with service registry as {service_id}")
            else:
                self.logger.error(f"Failed to register DNS server with service registry")

            # Set the resolve function for the DNSRequestHandler class
            DNSRequestHandler.set_resolve_func(self.resolve_ipv4)

            # Create HTTP server with our custom request handler
            self.httpd = HTTPServer((self.host, self.port), DNSRequestHandler)

            self.running = True
            self.logger.info(f"MCP DNS Server listening on {self.host}:{self.port}")

            # Start serving requests
            while self.running:
                # Handle a single request (this will block until a request comes in)
                self.httpd.handle_request()

        except Exception as e:
            self.logger.error(f"Error starting DNS server: {str(e)}")
            raise
        finally:
            # Clean up resources
            if self.service_wrapper:
                self.service_wrapper.stop()
            if self.httpd:
                self.httpd.server_close()
            self.logger.info("MCP DNS Server stopped")

    def stop(self):
        """Stop the DNS server"""
        self.running = False
        self.logger.info("Stopping MCP DNS Server...")


def main():
    """Main function to start the DNS server"""
    parser = argparse.ArgumentParser(description='MCP DNS Resolution Server')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8089, help='Port to bind to (default: 8089)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080',
                        help='Service registry URL (default: http://127.0.0.1:8080)')
    parser.add_argument('--service-id', type=str, help='Service ID for registry (auto-generated by default)')
    parser.add_argument('--service-ttl', type=int, default=60, help='Service TTL in seconds (default: 60)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start the DNS server
    server = MCPServer(
        host=args.host,
        port=args.port,
        registry_url=args.registry_url,
        service_id=args.service_id,
        service_ttl=args.service_ttl,
        log_level=args.log_level
    )
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Shutting down...")
        server.stop()
    except Exception as e:
        print(f"Failed to start server: {e}")
        exit(1)


if __name__ == '__main__':
    main()