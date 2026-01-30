#!/usr/bin/env python3
"""
MCP Search Server - An MCP server that performs search queries via Brave Search and registers itself with the service registry
"""

import json
import sys
import os
import threading
import logging
import argparse
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Add the project root directory and registry directory to the Python path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'registry'))

from registry_client import ServiceInfo, MCPServiceWrapper, HeartbeatFilter
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import requests


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

# Import settings to check if screen logging is enabled
sys.path.insert(0, os.path.join(project_root, 'config'))
from settings import ENABLE_SCREEN_LOGGING


class SearchRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for search requests"""

    # Class variable to hold the search function
    search_func = None

    @classmethod
    def set_search_func(cls, func):
        cls.search_func = func

    def do_POST(self):
        """Handle POST requests for search queries"""
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

            # Extract query from request - the parameters might be at the top level
            # or nested inside a 'parameters' field depending on how the client sends it
            if 'query' in request_data:
                search_query = request_data['query']
            elif 'parameters' in request_data:
                # If parameters are nested, check inside that object
                params = request_data['parameters']
                if 'query' in params:
                    search_query = params['query']
                else:
                    self.logger_error("Missing 'query' in request parameters")
                    self._send_error_response(400, "Missing 'query' in request parameters", "unknown")
                    return
            else:
                self.logger_error("Missing 'query' or 'parameters' in request")
                self._send_error_response(400, "Missing 'query' or 'parameters' in request", "unknown")
                return

            self.logger_info(f"Performing search query: {search_query}")

            # Perform search using the bound function
            if SearchRequestHandler.search_func is None:
                self.logger_error("Search function not set")
                self._send_error_response(500, "Server configuration error", "unknown")
                return

            success, search_results, error_msg = SearchRequestHandler.search_func(search_query)

            # Create response
            response = {
                "success": True,
                "result": {
                    "success": success,
                    "query": search_query,
                    "results": search_results,
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

    def _send_error_response(self, status_code: int, error_msg: str, query: str):
        """Send an error response"""
        error_response = {
            "success": False,
            "result": {
                "success": False,
                "query": query,
                "results": [],
                "error": error_msg
            }
        }
        self._send_json_response(status_code, error_response)

    def logger_info(self, msg):
        """Log an info message"""
        import logging
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.info(f"HTTP - {msg}")

    def logger_error(self, msg):
        """Log an error message"""
        import logging
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.error(f"HTTP - {msg}")

    def log_message(self, format, *args):
        """Override to use our logger"""
        import logging
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.info(f"HTTP - {format % args}")


class MCPSearchServer:
    """Main server class that handles search requests"""

    def __init__(self, host: str = '127.0.0.1', port: int = 8090, registry_url: str = 'http://127.0.0.1:8080',
                 service_id: Optional[str] = None, service_ttl: int = 60, log_level: str = 'INFO',
                 max_retries: int = 3, base_delay: float = 1.0):
        self.host = host
        self.port = port
        self.registry_url = registry_url
        self.service_ttl = service_ttl
        self.service_wrapper: Optional[MCPServiceWrapper] = None
        self.httpd: Optional[ThreadedHTTPServer] = None
        self.running = False

        # Set up rate limiting configuration
        self.max_retries = int(os.getenv('SEARCH_MAX_RETRIES', str(max_retries)))
        self.base_delay = float(os.getenv('SEARCH_BASE_DELAY', str(base_delay)))

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

        # Get Brave Search API key from environment
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        if not self.brave_api_key:
            self.logger.warning("BRAVE_SEARCH_API_KEY environment variable not set. Search functionality will not work properly.")

    def perform_search(self, query: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Perform search using Brave Search API
        Returns: (success, search_results, error_message)
        """
        try:
            if not self.brave_api_key:
                error_msg = "BRAVE_SEARCH_API_KEY environment variable not set"
                self.logger.error(error_msg)
                return False, [], error_msg

            # Prepare the request to Brave Search API
            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Content-Type': 'application/json'
            }

            # Prepare the search parameters
            params = {
                'q': query,
                'text_decorations': 0,  # Don't include text decorations
                'spellcheck': 1         # Enable spellcheck
            }

            # Use configured retry settings
            max_retries = self.max_retries
            base_delay = self.base_delay

            for attempt in range(max_retries):
                try:
                    # Make the request to Brave Search API
                    response = requests.get(
                        'https://api.search.brave.com/res/v1/web/search',
                        headers=headers,
                        params=params
                    )

                    if response.status_code == 200:
                        # Parse the response
                        data = response.json()

                        # Extract search results
                        results = []
                        if 'web' in data and 'results' in data['web']:
                            for result in data['web']['results']:
                                results.append({
                                    'title': result.get('title', ''),
                                    'url': result.get('url', ''),
                                    'description': result.get('description', ''),
                                    'date': result.get('date', ''),
                                    'language': result.get('language', ''),
                                    'thumbnail': result.get('thumbnail', {}).get('src', '') if result.get('thumbnail') else ''
                                })

                        self.logger.info(f"Successfully performed search for '{query}', got {len(results)} results")
                        return True, results, None
                    elif response.status_code == 429:  # Rate limited
                        if attempt < max_retries - 1:  # If not the last attempt
                            # Calculate delay with exponential backoff and jitter
                            delay = base_delay * (2 ** attempt) + (time.time() % 1)  # Add jitter
                            self.logger.warning(f"Rate limited by Brave Search API. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            continue  # Retry
                        else:
                            error_msg = f"Brave Search API returned status code {response.status_code} after {max_retries} attempts: {response.text}"
                            self.logger.error(error_msg)
                            return False, [], error_msg
                    else:
                        error_msg = f"Brave Search API returned status code {response.status_code}: {response.text}"
                        self.logger.error(error_msg)
                        return False, [], error_msg

                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:  # If not the last attempt
                        # Calculate delay with exponential backoff and jitter
                        delay = base_delay * (2 ** attempt) + (time.time() % 1)  # Add jitter
                        self.logger.warning(f"Network error during search attempt {attempt + 1}/{max_retries}. Retrying in {delay:.2f} seconds... Error: {str(e)}")
                        time.sleep(delay)
                        continue  # Retry
                    else:
                        error_msg = f"Network error performing search for '{query}' after {max_retries} attempts: {str(e)}"
                        self.logger.error(error_msg)
                        return False, [], error_msg

        except Exception as e:
            error_msg = f"Unexpected error performing search for '{query}': {str(e)}"
            self.logger.error(error_msg)
            return False, [], error_msg

    def start(self):
        """Start the search server"""
        try:
            # Register with the service registry
            # Use 127.0.0.1 instead of 0.0.0.0 for service registration since 0.0.0.0 is not a valid call address
            registration_host = "127.0.0.1" if self.host == "0.0.0.0" else self.host
            service_id = f"search-server-{registration_host}-{self.port}".replace('.', '-').replace(':', '-')
            service_info = ServiceInfo(
                id=service_id,
                host=registration_host,
                port=self.port,
                type="mcp_search",
                metadata={
                    "service_type": "search_engine",
                    "capabilities": ["web_search", "brave_search"],
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
                self.logger.info(f"Search server registered with service registry as {service_id}")
            else:
                self.logger.error(f"Failed to register search server with service registry")
                # Stop the server if registration fails
                raise Exception("Service registration failed")

            # Set the search function for the SearchRequestHandler class
            SearchRequestHandler.set_search_func(self.perform_search)

            # Create threaded HTTP server with our custom request handler
            self.httpd = ThreadedHTTPServer((self.host, self.port), SearchRequestHandler)

            self.running = True
            self.logger.info(f"MCP Search Server listening on {self.host}:{self.port}")

            # Start serving requests in separate threads
            self.httpd.serve_forever()

        except Exception as e:
            self.logger.error(f"Error starting search server: {str(e)}")
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
            self.logger.info("MCP Search Server stopped")
            raise

    def stop(self):
        """Stop the search server"""
        self.running = False
        if self.httpd:
            self.httpd.shutdown()
        self.logger.info("Stopping MCP Search Server...")


def main():
    """Main function to start the search server"""
    parser = argparse.ArgumentParser(description='MCP Search Server using Brave Search API')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8090, help='Port to bind to (default: 8090)')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080',
                        help='Service registry URL (default: http://127.0.0.1:8080)')
    parser.add_argument('--service-id', type=str, help='Service ID for registry (auto-generated by default)')
    parser.add_argument('--service-ttl', type=int, default=60, help='Service TTL in seconds (default: 60)')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')

    args = parser.parse_args()

    # Set up logging based on global setting
    log_level = getattr(logging, args.log_level.upper()) if ENABLE_SCREEN_LOGGING else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Add the heartbeat filter to the root logger to suppress heartbeat messages
    logging.getLogger().addFilter(HeartbeatFilter())

    # Create and start the search server
    server = MCPSearchServer(
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
        if ENABLE_SCREEN_LOGGING:
            print("\nReceived interrupt signal. Shutting down...")
        server.stop()
    except Exception as e:
        if ENABLE_SCREEN_LOGGING:
            print(f"Failed to start server: {e}")
        exit(1)


if __name__ == '__main__':
    main()