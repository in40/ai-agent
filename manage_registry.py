#!/usr/bin/env python3
"""
Utility script to manage the MCP Service Registry server
Provides functions to start, stop, and check the status of the registry server
"""

import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path


def check_registry_running(port=8080):
    """Check if registry server is running on the specified port"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False


def start_registry_server(host='127.0.0.1', port=8080, cleanup_interval=30, log_level='INFO', background=False):
    """Start the registry server"""
    if check_registry_running(port):
        print(f"Registry server is already running on {host}:{port}")
        return True
    
    cmd = [
        sys.executable, 'start_registry_server.py',
        '--host', host,
        '--port', str(port),
        '--cleanup-interval', str(cleanup_interval),
        '--log-level', log_level
    ]
    
    if background:
        # Start in background
        try:
            process = subprocess.Popen(cmd)
            print(f"Started registry server on {host}:{port} (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"Failed to start registry server: {e}")
            return False
    else:
        # Start in foreground
        try:
            subprocess.run(cmd)
            return True
        except KeyboardInterrupt:
            print("\nRegistry server stopped by user")
            return True


def stop_registry_server(port=8080):
    """Stop the registry server running on the specified port"""
    try:
        import psutil
        
        # Find processes using the port
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                connections = proc.connections(kind='inet')
                for conn in connections:
                    if conn.laddr.port == port:
                        proc.terminate()
                        proc.wait(timeout=5)
                        print(f"Stopped registry server (PID: {proc.pid})")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        print(f"No registry server found running on port {port}")
        return False
    except ImportError:
        print("psutil not available, trying alternative method...")
        
        # Alternative method using lsof (Unix-like systems)
        try:
            result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                pids = []
                for line in lines:
                    parts = line.split()
                    if len(parts) > 1:
                        pids.append(parts[1])
                
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"Sent termination signal to process {pid}")
                    except ProcessLookupError:
                        print(f"Process {pid} not found")
                    except PermissionError:
                        print(f"Permission denied to terminate process {pid}")
                
                return True
            else:
                print(f"No registry server found running on port {port}")
                return False
        except FileNotFoundError:
            print("lsof not available, cannot determine running processes")
            return False


def main():
    parser = argparse.ArgumentParser(description='Manage MCP Service Registry Server')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'], 
                        help='Action to perform on the registry server')
    parser.add_argument('--host', type=str, default='127.0.0.1', 
                        help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, 
                        help='Port to bind to (default: 8080)')
    parser.add_argument('--cleanup-interval', type=int, default=30, 
                        help='Cleanup interval in seconds (default: 30)')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--background', action='store_true', 
                        help='Run the server in the background (for start action)')

    args = parser.parse_args()

    if args.action == 'start':
        start_registry_server(
            host=args.host,
            port=args.port,
            cleanup_interval=args.cleanup_interval,
            log_level=args.log_level,
            background=args.background
        )
    elif args.action == 'stop':
        stop_registry_server(port=args.port)
    elif args.action == 'restart':
        print("Stopping registry server...")
        stop_registry_server(port=args.port)
        time.sleep(2)  # Wait for server to stop
        print("Starting registry server...")
        start_registry_server(
            host=args.host,
            port=args.port,
            cleanup_interval=args.cleanup_interval,
            log_level=args.log_level,
            background=args.background
        )
    elif args.action == 'status':
        if check_registry_running(port=args.port):
            print(f"Registry server is running on {args.host}:{args.port}")
        else:
            print(f"Registry server is NOT running on {args.host}:{args.port}")


if __name__ == '__main__':
    main()