#!/usr/bin/env python3
"""
Script to start the MCP Service Registry server separately
"""

import sys
import os
import argparse
import logging
from service_registry import ServiceRegistryServer


def main():
    """Main function to start the service registry server"""
    parser = argparse.ArgumentParser(description='MCP Service Registry Server - Standalone Startup Script')
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

    print(f"Starting MCP Service Registry on {args.host}:{args.port}")
    print(f"Cleanup interval: {args.cleanup_interval} seconds")
    print(f"Press Ctrl+C to stop.")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down service registry server...")
        server.stop()
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()