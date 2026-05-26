#!/usr/bin/env python3
"""
MCP Search Server — dual-mode server that supports both:
  1. Legacy custom HTTP API: POST /search with {"query": "..."}
  2. Standard MCP protocol (JSON-RPC 2.0): initialize, list_tools, call_tool

Both endpoints run on the same port. The MCP protocol enables Qwen Code
to auto-discover the 'internet_search' tool natively.

Service registry registration and heartbeats are preserved.
Brave Search logic with retry/backoff is preserved.

Usage:
    export BRAVE_SEARCH_API_KEY=your_key_here
    python3 mcp_search_server.py --host 127.0.0.1 --port 8090
"""

import json
import sys
import os
import threading
import logging
import argparse
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Add the project root directory and registry directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'registry'))

from registry_client import ServiceInfo, MCPServiceWrapper, HeartbeatFilter
from socketserver import ThreadingMixIn
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True

# Import settings to check if screen logging is enabled
sys.path.insert(0, os.path.join(project_root, 'config'))
from settings import ENABLE_SCREEN_LOGGING


# ===================================================================
# Brave Search client (preserved from original)
# ===================================================================
class BraveSearchClient:
    """Performs searches via the Brave Search API with retry/backoff."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.brave_api_key = os.getenv('BRAVE_SEARCH_API_KEY')
        self.max_retries = max_retries
        self.base_delay = base_delay

        if not self.brave_api_key:
            logging.getLogger(__name__).warning(
                "BRAVE_SEARCH_API_KEY environment variable not set. "
                "Search functionality will not work properly."
            )

    def search(self, query: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """
        Perform search using Brave Search API.
        Returns: (success, search_results, error_message)
        """
        try:
            if not self.brave_api_key:
                error_msg = "BRAVE_SEARCH_API_KEY environment variable not set"
                logging.getLogger(__name__).error(error_msg)
                return False, [], error_msg

            headers = {
                'X-Subscription-Token': self.brave_api_key,
                'Content-Type': 'application/json'
            }
            params = {
                'q': query,
                'text_decorations': 0,
                'spellcheck': 1
            }

            for attempt in range(self.max_retries):
                try:
                    response = requests.get(
                        'https://api.search.brave.com/res/v1/web/search',
                        headers=headers,
                        params=params
                    )

                    if response.status_code == 200:
                        data = response.json()
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
                        logging.getLogger(__name__).info(
                            f"Successfully performed search for '{query}', got {len(results)} results"
                        )
                        return True, results, None

                    elif response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            delay = self.base_delay * (2 ** attempt) + (time.time() % 1)
                            logging.getLogger(__name__).warning(
                                f"Rate limited by Brave Search API. Retrying in {delay:.2f}s "
                                f"(attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            error_msg = (
                                f"Brave Search API returned status code {response.status_code} "
                                f"after {self.max_retries} attempts: {response.text}"
                            )
                            logging.getLogger(__name__).error(error_msg)
                            return False, [], error_msg
                    else:
                        error_msg = (
                            f"Brave Search API returned status code {response.status_code}: {response.text}"
                        )
                        logging.getLogger(__name__).error(error_msg)
                        return False, [], error_msg

                except requests.exceptions.RequestException as e:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt) + (time.time() % 1)
                        logging.getLogger(__name__).warning(
                            f"Network error during search attempt {attempt + 1}/{self.max_retries}. "
                            f"Retrying in {delay:.2f}s... Error: {str(e)}"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        error_msg = (
                            f"Network error performing search for '{query}' "
                            f"after {self.max_retries} attempts: {str(e)}"
                        )
                        logging.getLogger(__name__).error(error_msg)
                        return False, [], error_msg

        except Exception as e:
            error_msg = f"Unexpected error performing search for '{query}': {str(e)}"
            logging.getLogger(__name__).error(error_msg)
            return False, [], error_msg


# ===================================================================
# MCP protocol helpers
# ===================================================================
def _format_search_results(results: List[Dict]) -> str:
    """Format search results into a readable text block for MCP tool output."""
    if not results:
        return "No results found."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', 'Untitled')}")
        lines.append(f"   URL: {r.get('url', 'N/A')}")
        desc = r.get('description', '')
        if desc:
            lines.append(f"   {desc}")
        date = r.get('date', '')
        if date:
            lines.append(f"   Date: {date}")
        lines.append("")
    return "\n".join(lines)


# ===================================================================
# Unified HTTP Request Handler — legacy + MCP
# ===================================================================
class SearchRequestHandler(BaseHTTPRequestHandler):
    """
    Handles both:
      - Legacy: POST /search  →  custom JSON format
      - MCP:    POST /        →  JSON-RPC 2.0 (initialize, list_tools, call_tool)
    """

    search_func = None  # bound to MCPSearchServer.perform_search

    @classmethod
    def set_search_func(cls, func):
        cls.search_func = func

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'

        try:
            request_data = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError as e:
            self.logger_error(f"Invalid JSON in request: {str(e)}")
            self._send_json_response(400, {"error": "Invalid JSON", "jsonrpc": "2.0", "id": None})
            return

        # --- MCP JSON-RPC 2.0 path ---
        if isinstance(request_data, dict) and 'jsonrpc' in request_data:
            self._handle_mcp(request_data)
            return

        # --- Legacy POST /search path ---
        if self.path == '/search':
            self._handle_legacy_search(request_data)
            return

        # Unknown endpoint
        self._send_json_response(404, {"error": f"Unknown endpoint: {self.path}"})

    # ------------------------------------------------------------------
    # Legacy endpoint: POST /search
    # ------------------------------------------------------------------
    def _handle_legacy_search(self, request_data: dict):
        """Handle legacy POST /search requests (backward compatible)."""
        try:
            if 'query' in request_data:
                search_query = request_data['query']
            elif 'parameters' in request_data:
                params = request_data['parameters']
                if 'query' in params:
                    search_query = params['query']
                else:
                    self.logger_error("Missing 'query' in request parameters")
                    self._send_json_response(400, {
                        "success": False,
                        "result": {"success": False, "query": "", "results": [],
                                   "error": "Missing 'query' in request parameters"}
                    })
                    return
            else:
                self.logger_error("Missing 'query' or 'parameters' in request")
                self._send_json_response(400, {
                    "success": False,
                    "result": {"success": False, "query": "", "results": [],
                               "error": "Missing 'query' or 'parameters' in request"}
                })
                return

            self.logger_info(f"Performing search query: {search_query}")

            if SearchRequestHandler.search_func is None:
                self.logger_error("Search function not set")
                self._send_json_response(500, {
                    "success": False,
                    "result": {"success": False, "query": search_query, "results": [],
                               "error": "Server configuration error"}
                })
                return

            success, search_results, error_msg = SearchRequestHandler.search_func(search_query)

            response = {
                "success": True,
                "result": {
                    "success": success,
                    "query": search_query,
                    "results": search_results,
                    "error": error_msg
                }
            }
            self._send_json_response(200, response)

        except Exception as e:
            self.logger_error(f"Error handling request: {str(e)}")
            self._send_json_response(500, {
                "success": False,
                "result": {"success": False, "query": "", "results": [],
                           "error": f"Internal server error: {str(e)}"}
            })

    # ------------------------------------------------------------------
    # MCP JSON-RPC 2.0 handlers
    # ------------------------------------------------------------------
    def _handle_mcp(self, request_data: dict):
        """Handle MCP JSON-RPC 2.0 requests."""
        method = request_data.get('method', '')
        request_id = request_data.get('id')

        if method == 'initialize':
            self._handle_initialize(request_id)
        elif method == 'tools/list':
            self._handle_tools_list(request_id)
        elif method == 'tools/call':
            self._handle_tools_call(request_data, request_id)
        elif method == 'notifications/initialized':
            # Qwen Code sends this after initialize — just acknowledge
            self._send_json_response(200, {"jsonrpc": "2.0", "result": None, "id": request_id})
        else:
            self._send_json_response(400, {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": request_id
            })

    def _handle_initialize(self, request_id: Any):
        """Respond to MCP initialize request."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "mcp-search-server",
                    "version": "1.0.0"
                }
            }
        }
        self._send_json_response(200, response)

    def _handle_tools_list(self, request_id: Any):
        """Return the list of available MCP tools."""
        tools = [
            {
                "name": "internet_search",
                "description": (
                    "Search the internet using Brave Search. Returns titles, URLs, "
                    "descriptions, dates, and languages for each result. Use this when "
                    "you need current information from the web."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (e.g. 'latest AI news 2026')"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of results to return (default: 10, max: 20)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
        self._send_json_response(200, response)

    def _handle_tools_call(self, request_data: dict, request_id: Any):
        """Call an MCP tool (internet_search)."""
        params = request_data.get('params', {})
        tool_name = params.get('name', '')

        if tool_name != 'internet_search':
            self._send_json_response(200, {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                "id": request_id
            })
            return

        arguments = params.get('arguments', {})
        query = arguments.get('query', '')
        count = min(arguments.get('count', 10), 20)

        self.logger_info(f"MCP call_tool internet_search: query='{query}', count={count}")

        if not query:
            self._send_json_response(200, {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Missing required parameter: query"},
                "id": request_id
            })
            return

        if SearchRequestHandler.search_func is None:
            self._send_json_response(200, {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Server configuration error"},
                "id": request_id
            })
            return

        success, search_results, error_msg = SearchRequestHandler.search_func(query)

        if success:
            # Filter to requested count
            search_results = search_results[:count]
            formatted = _format_search_results(search_results)
            content = [{"type": "text", "text": formatted}]
        else:
            content = [{"type": "text", "text": f"Search failed: {error_msg}"}]

        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": content}
        }
        self._send_json_response(200, response)

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------
    def _send_json_response(self, status_code: int, data: dict):
        """Send a JSON response with appropriate headers."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def logger_info(self, msg):
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.info(f"HTTP - {msg}")

    def logger_error(self, msg):
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.error(f"HTTP - {msg}")

    def log_message(self, format, *args):
        logger = logging.getLogger('MCPServer.SearchRequestHandler')
        logger.info(f"HTTP - {format % args}")


# ===================================================================
# Main server class (preserved from original, with MCP added)
# ===================================================================
class MCPSearchServer:
    """Main server class — handles search requests and service registry."""

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

        self.max_retries = int(os.getenv('SEARCH_MAX_RETRIES', str(max_retries)))
        self.base_delay = float(os.getenv('SEARCH_BASE_DELAY', str(base_delay)))

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            handler.addFilter(HeartbeatFilter())
            self.logger.addHandler(handler)

        self.brave_client = BraveSearchClient(
            max_retries=self.max_retries,
            base_delay=self.base_delay
        )

    def perform_search(self, query: str) -> Tuple[bool, List[Dict], Optional[str]]:
        """Delegate to BraveSearchClient (preserved from original)."""
        return self.brave_client.search(query)

    def start(self):
        """Start the search server with service registry + HTTP."""
        try:
            # Register with the service registry
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
                heartbeat_interval=20,
                ttl=self.service_ttl
            )

            if self.service_wrapper.start():
                self.logger.info(f"Search server registered with service registry as {service_id}")
            else:
                self.logger.error("Failed to register search server with service registry")
                raise Exception("Service registration failed")

            # Bind search function to the request handler
            SearchRequestHandler.set_search_func(self.perform_search)

            # Create threaded HTTP server
            self.httpd = ThreadedHTTPServer((self.host, self.port), SearchRequestHandler)

            self.running = True
            self.logger.info(f"MCP Search Server listening on {self.host}:{self.port}")
            self.logger.info(f"  Legacy endpoint: POST /search")
            self.logger.info(f"  MCP endpoint:    POST / (JSON-RPC 2.0)")

            self.httpd.serve_forever()

        except Exception as e:
            self.logger.error(f"Error starting search server: {str(e)}")
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
        """Stop the search server."""
        self.running = False
        if self.httpd:
            self.httpd.shutdown()
        self.logger.info("Stopping MCP Search Server...")


def main():
    """Main function to start the search server."""
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

    log_level = getattr(logging, args.log_level.upper()) if ENABLE_SCREEN_LOGGING else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().addFilter(HeartbeatFilter())

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
