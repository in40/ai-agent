#!/usr/bin/env python3
"""
MCP Download Server - An MCP server that handles file download operations and registers itself with the service registry
"""

import json
import sys
import os
import threading
import logging
import argparse
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

# Add the project root directory and registry directory to the Python path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'registry'))

from registry_client import ServiceInfo, MCPServiceWrapper, HeartbeatFilter
from http.server import BaseHTTPRequestHandler, HTTPServer

# Import settings to check if screen logging is enabled
sys.path.insert(0, os.path.join(project_root, 'config'))
from settings import ENABLE_SCREEN_LOGGING


class DownloadRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for download requests"""

    # Class variable to hold the download function
    download_func = None

    @classmethod
    def set_download_func(cls, func):
        cls.download_func = func

    def do_POST(self):
        """Handle POST requests for download operations"""
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

            # Extract URL from request - the parameters might be at the top level
            # or nested inside a 'parameters' field depending on how the client sends it
            if 'url' in request_data:
                download_url = request_data['url']
            elif 'parameters' in request_data:
                # If parameters are nested, check inside that object
                params = request_data['parameters']
                if 'url' in params:
                    download_url = params['url']
                else:
                    self.logger_error("Missing 'url' in request parameters")
                    self._send_error_response(400, "Missing 'url' in request parameters", "unknown")
                    return
            else:
                self.logger_error("Missing 'url' or 'parameters' in request")
                self._send_error_response(400, "Missing 'url' or 'parameters' in request", "unknown")
                return

            self.logger_info(f"Downloading from URL: {download_url}")

            # Perform download using the bound function
            if DownloadRequestHandler.download_func is None:
                self.logger_error("Download function not set")
                self._send_error_response(500, "Server configuration error", "unknown")
                return

            success, file_path, error_msg = DownloadRequestHandler.download_func(download_url)

            # Create response
            response = {
                "success": True,
                "result": {
                    "success": success,
                    "url": download_url,
                    "file_path": file_path,
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

    def _send_error_response(self, status_code: int, error_msg: str, url: str):
        """Send an error response"""
        error_response = {
            "success": False,
            "result": {
                "success": False,
                "url": url,
                "file_path": "",
                "error": error_msg
            }
        }
        self._send_json_response(status_code, error_response)

    def logger_info(self, msg):
        """Log an info message"""
        import logging
        logger = logging.getLogger('MCPServer.DownloadRequestHandler')
        logger.info(f"HTTP - {msg}")

    def logger_error(self, msg):
        """Log an error message"""
        import logging
        logger = logging.getLogger('MCPServer.DownloadRequestHandler')
        logger.error(f"HTTP - {msg}")

    def log_message(self, format, *args):
        """Override to use our logger"""
        import logging
        logger = logging.getLogger('MCPServer.DownloadRequestHandler')
        logger.info(f"HTTP - {format % args}")


class MCPDownloadServer:
    """Main server class that handles download requests"""

    def __init__(self, host: str = '127.0.0.1', port: int = 8093, registry_url: str = 'http://127.0.0.1:8080',
                 service_id: Optional[str] = None, service_ttl: int = 60, log_level: str = 'INFO',
                 download_dir: str = './downloads'):
        self.host = host
        self.port = port
        self.registry_url = registry_url
        self.service_ttl = service_ttl
        self.service_wrapper: Optional[MCPServiceWrapper] = None
        self.httpd: Optional[HTTPServer] = None
        self.running = False
        self.download_dir = download_dir

        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)

        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            # Add the heartbeat filter to suppress heartbeat messages
            handler.addFilter(HeartbeatFilter())
            self.logger.addHandler(handler)

    def download_file(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Download a file from the given URL
        Returns: (success, file_path, error_message)
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                error_msg = f"Invalid URL: {url}"
                self.logger.error(error_msg)
                return False, "", error_msg

            # Create a safe filename from the URL
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                # If no filename in URL, try to extract from Content-Disposition header or use a default
                filename = f"download_{int(datetime.now().timestamp())}.dat"
            
            file_path = os.path.join(self.download_dir, filename)

            # Download the file
            self.logger.info(f"Starting download from {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Write the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Successfully downloaded file to {file_path}")
            return True, file_path, None

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error downloading {url}: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Unexpected error downloading {url}: {str(e)}"
            self.logger.error(error_msg)
            return False, "", error_msg

    def start(self):
        """Start the download server"""
        try:
            # Register with the service registry
            service_id = f"download-server-{self.host}-{self.port}".replace('.', '-').replace(':', '-')
            # Use 127.0.0.1 instead of 0.0.0.0 for service registration since 0.0.0.0 is not a valid call address
            registration_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            service_id = f"download-server-{registration_host}-{self.port}".replace('.', '-').replace(':', '-')
            service_info = ServiceInfo(
                id=service_id,
                host=registration_host,
                port=self.port,
                type="mcp_download",
                metadata={
                    "service_type": "file_downloader",
                    "capabilities": ["url_download", "file_transfer"],
                    "download_dir": self.download_dir,
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
                self.logger.info(f"Download server registered with service registry as {service_id}")
            else:
                self.logger.error(f"Failed to register download server with service registry")
                # Stop the server if registration fails
                raise Exception("Service registration failed")

            # Set the download function for the DownloadRequestHandler class
            DownloadRequestHandler.set_download_func(self.download_file)

            # Create HTTP server with our custom request handler
            self.httpd = HTTPServer((self.host, self.port), DownloadRequestHandler)

            self.running = True
            self.logger.info(f"MCP Download Server listening on {self.host}:{self.port}")

            # Start serving requests
            while self.running:
                # Handle a single request (this will block until a request comes in)
                self.httpd.handle_request()

        except Exception as e:
            self.logger.error(f"Error starting download server: {str(e)}")
            # Clean up resources in case of error during startup
            if self.service_wrapper:
                try:
                    self.service_wrapper.stop()
                except Exception as cleanup_error:
                    self.logger.error(f"Error during cleanup: {cleanup_error}")
            if self.httpd:
                try:
                    self.httpd.server_close()
                except Exception as cleanup_error:
                    self.logger.error(f"Error closing HTTP server: {cleanup_error}")
            self.logger.info("MCP Download Server stopped")
            raise

    def stop(self):
        """Stop the download server"""
        self.running = False
        self.logger.info("Stopping MCP Download Server...")


def main():
    """Main function to start the download server"""
    parser = argparse.ArgumentParser(description='MCP Download Server - Handles file download operations')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8093, help='Port to bind to (default: 8093)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080',
                        help='Service registry URL (default: http://127.0.0.1:8080)')
    parser.add_argument('--service-id', type=str, help='Service ID for registry (auto-generated by default)')
    parser.add_argument('--service-ttl', type=int, default=60, help='Service TTL in seconds (default: 60)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--download-dir', type=str, default='./downloads',
                        help='Directory to save downloaded files (default: ./downloads)')

    args = parser.parse_args()

    # Set up logging based on global setting
    log_level = getattr(logging, args.log_level.upper()) if ENABLE_SCREEN_LOGGING else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Add the heartbeat filter to the root logger to suppress heartbeat messages
    logging.getLogger().addFilter(HeartbeatFilter())

    # Create and start the download server
    server = MCPDownloadServer(
        host=args.host,
        port=args.port,
        registry_url=args.registry_url,
        service_id=args.service_id,
        service_ttl=args.service_ttl,
        log_level=args.log_level,
        download_dir=args.download_dir
    )

    try:
        server.start()
    except KeyboardInterrupt:
        if ENABLE_SCREEN_LOGGING:
            print("\nReceived interrupt signal. Shutting down...")
        server.stop()
    except Exception as e:
        if ENABLE_SCREEN_LOGGING:
            print(f"Failed to start server: {e}")
        exit(1)


if __name__ == '__main__':
    main()