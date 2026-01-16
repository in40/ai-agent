#!/usr/bin/env python3
"""
Script to start the MCP Service Registry server separately
"""

import sys
import os
import argparse
import logging

# Add the current directory to the Python path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service_registry import ServiceRegistryServer

# Import settings to check if screen logging is enabled
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'config'))
from settings import ENABLE_SCREEN_LOGGING

# Import the heartbeat filter
sys.path.insert(0, os.path.join(project_root, 'registry'))
from service_registry import HeartbeatFilter


def main():
    """Main function to start the service registry server"""
    parser = argparse.ArgumentParser(description='MCP Service Registry Server - Standalone Startup Script')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--cleanup-interval', type=int, default=30, help='Cleanup interval in seconds (default: 30)')
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

    # Create and start the registry server
    server = ServiceRegistryServer(host=args.host, port=args.port)
    server.registry.cleanup_interval = args.cleanup_interval

    if ENABLE_SCREEN_LOGGING:
        print(f"Starting MCP Service Registry on {args.host}:{args.port}")
        print(f"Cleanup interval: {args.cleanup_interval} seconds")
        print(f"Press Ctrl+C to stop.")
    
    try:
        server.start()
    except KeyboardInterrupt:
        if ENABLE_SCREEN_LOGGING:
            print("\nShutting down service registry server...")
        server.stop()
    except Exception as e:
        if ENABLE_SCREEN_LOGGING:
            print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()