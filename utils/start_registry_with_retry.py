#!/usr/bin/env python3
"""
Utility script to start the MCP Service Registry with retry logic and better error handling
"""

import subprocess
import sys
import time
import requests
import logging
import argparse
import os
from pathlib import Path


def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0


def start_registry_with_retry(host='127.0.0.1', port=8080, max_retries=3, retry_delay=5):
    """Start the registry server with retry logic"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Check if port is available
    if not check_port_available(port):
        logger.error(f"Port {port} is already in use")
        return False

    # Find the project root and activate virtual environment if needed
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "ai_agent_env"
    
    if venv_path.exists():
        # On Linux/Mac, the Python executable is in bin/python
        python_executable = venv_path / "bin" / "python"
        if not python_executable.exists():
            # On Windows, it would be Scripts/python.exe
            python_executable = venv_path / "Scripts" / "python.exe"
        
        if python_executable.exists():
            python_cmd = str(python_executable)
        else:
            logger.warning(f"Python executable not found in virtual environment, using system Python")
            python_cmd = sys.executable
    else:
        logger.warning(f"Virtual environment not found at {venv_path}, using system Python")
        python_cmd = sys.executable

    # Command to start the registry
    cmd = [
        python_cmd,
        "-m", "registry.start_registry_server",
        "--host", host,
        "--port", str(port)
    ]

    for attempt in range(max_retries):
        logger.info(f"Starting MCP Service Registry on {host}:{port} (attempt {attempt + 1}/{max_retries})")
        
        try:
            # Start the registry server
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )
            
            # Wait a bit for the server to start
            time.sleep(3)
            
            # Check if the process is still running
            if process.poll() is not None:
                # Process has already exited, get the error output
                _, stderr = process.communicate()
                logger.error(f"Registry server failed to start: {stderr.decode()}")
                
                # Try the next attempt
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error("Max retries reached. Registry server failed to start.")
                    return False
            
            # Test if the server is responding to health checks
            health_url = f"http://{host}:{port}/health"
            success = False
            
            # Try to connect to the health endpoint
            for i in range(10):  # Try for up to 10 times with 1 sec intervals
                try:
                    response = requests.get(health_url, timeout=5)
                    if response.status_code == 200:
                        health_data = response.json()
                        if health_data.get('status') == 'healthy':
                            logger.info(f"MCP Service Registry is running and healthy on {host}:{port}")
                            logger.info(f"Process PID: {process.pid}")
                            return process
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(1)
            
            # If we reach here, the server didn't respond properly
            logger.warning(f"Registry server started but is not responding properly to health checks")
            
            # Terminate the process before retrying
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Registry server is not responding properly.")
                return False
        
        except FileNotFoundError:
            logger.error(f"Python command not found: {python_cmd}")
            return False
        except Exception as e:
            logger.error(f"Error starting registry server: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached.")
                return False
    
    return False


def main():
    parser = argparse.ArgumentParser(description='Start MCP Service Registry with retry logic')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to (default: 8080)')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of restart attempts (default: 3)')
    parser.add_argument('--retry-delay', type=int, default=5, help='Delay between retries in seconds (default: 5)')
    
    args = parser.parse_args()
    
    process = start_registry_with_retry(
        host=args.host,
        port=args.port,
        max_retries=args.max_retries,
        retry_delay=args.retry_delay
    )
    
    if process and hasattr(process, 'wait'):
        try:
            # Wait for the process to complete (this keeps it running)
            process.wait()
        except KeyboardInterrupt:
            logger = logging.getLogger(__name__)
            logger.info("Received interrupt signal. Shutting down registry server...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info("Registry server shut down.")


if __name__ == "__main__":
    main()