#!/usr/bin/env python3
"""
Test script to verify that the registry server starts reliably
"""

import subprocess
import time
import requests
import signal
import sys
import os
from pathlib import Path


def test_registry_reliability():
    """Test the registry server startup reliability"""
    print("Testing registry server reliability...")
    
    # Find the project root
    project_root = Path(__file__).parent
    registry_module = "registry.start_registry_server"
    
    # Virtual environment path
    venv_path = project_root / "ai_agent_env"
    python_executable = venv_path / "bin" / "python"
    
    if not python_executable.exists():
        print("Virtual environment Python not found, using system Python")
        python_executable = sys.executable
    
    # Test multiple startups
    for i in range(3):
        print(f"\nTest {i+1}: Starting registry server...")
        
        # Start the registry server
        cmd = [
            str(python_executable),
            "-m", registry_module,
            "--host", "127.0.0.1",
            "--port", "8080"
        ]
        
        # Start the process
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
            # Process has already exited
            stdout, stderr = process.communicate()
            print(f"  Process exited early with code {process.returncode}")
            print(f"  Stdout: {stdout.decode()}")
            print(f"  Stderr: {stderr.decode()}")
            print("  FAILED")
            continue
        
        # Test if the server is responding to health checks
        try:
            response = requests.get("http://127.0.0.1:8080/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') == 'healthy':
                    print("  SUCCESS: Registry is running and healthy")
                else:
                    print(f"  WARNING: Registry responded but status is not healthy: {health_data.get('status')}")
            else:
                print(f"  FAILED: Registry responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  FAILED: Could not connect to registry: {e}")
        
        # Terminate the process
        print(f"  Terminating process with PID {process.pid}...")
        process.send_signal(signal.SIGTERM)
        
        try:
            # Wait for the process to terminate gracefully
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("  Process didn't terminate gracefully, killing it...")
            process.kill()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("  Process still didn't terminate after kill")
        
        # Wait a bit before the next test
        time.sleep(2)
    
    print("\nRegistry reliability test completed.")


if __name__ == "__main__":
    test_registry_reliability()