#!/usr/bin/env python3
"""
Test script to verify MCP registry integration with the AI agent
"""

import subprocess
import time
import threading
import requests
import json
import signal
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from registry_client import ServiceRegistryClient, ServiceInfo, MCPServiceWrapper
from core.ai_agent import AIAgent


def start_registry_server(port=8085):
    """Start the service registry server in a separate process"""
    cmd = ["python", "service_registry.py", "--host", "127.0.0.1", "--port", str(port), "--log-level", "INFO"]
    process = subprocess.Popen(cmd)
    return process


def start_dns_server(registry_port=8086, dns_port=8090):
    """Start the DNS server in a separate process"""
    cmd = ["python", "mcp_dns_server.py", "--host", "127.0.0.1", "--port", str(dns_port), "--registry-url", f"http://127.0.0.1:{registry_port}", "--log-level", "INFO"]
    process = subprocess.Popen(cmd)
    return process


def test_registry_integration():
    """Test the MCP registry integration"""
    print("Starting MCP registry integration test...")

    # Start the registry server
    print("Starting service registry server...")
    registry_process = start_registry_server(port=8087)

    # Give the server time to start
    time.sleep(3)

    # Test registry client functionality
    print("Testing registry client functionality...")
    client = ServiceRegistryClient("http://127.0.0.1:8087")

    # Check if registry is healthy
    if client.check_health():
        print("✓ Registry health check passed")
    else:
        print("✗ Registry health check failed")
        registry_process.terminate()
        return False
    
    # Register a test service
    test_service = ServiceInfo(
        id="test-service-python",
        host="127.0.0.1",
        port=8081,
        type="test",
        metadata={
            "version": "1.0.0",
            "test_property": "test_value"
        }
    )
    
    if client.register_service(test_service, ttl=60):
        print(f"✓ Test service {test_service.id} registered successfully")
    else:
        print(f"✗ Failed to register test service {test_service.id}")
        registry_process.terminate()
        return False
    
    # Discover services
    services = client.discover_services(service_type="test")
    if len(services) > 0:
        print(f"✓ Discovered {len(services)} test services")
    else:
        print("✗ Failed to discover test services")
        registry_process.terminate()
        return False
    
    # Test AI agent registration with registry
    print("Testing AI agent registration with registry...")
    ai_agent = AIAgent(
        database_url=None,  # No database needed for this test
        registry_url="http://127.0.0.1:8087",
        register_with_registry=True
    )
    
    # Wait a bit for the registration to happen
    time.sleep(2)
    
    # Discover AI agent services
    ai_agent_services = client.discover_services(service_type="ai_agent")
    if len(ai_agent_services) > 0:
        print(f"✓ Discovered {len(ai_agent_services)} AI agent services")
    else:
        print("✗ Failed to discover AI agent services")
        registry_process.terminate()
        return False
    
    # Test service discovery in the AI agent
    discovered = ai_agent._discover_mcp_services()
    if len(discovered) > 0:
        print(f"✓ AI agent discovered {len(discovered)} services from registry")
    else:
        print("✗ AI agent failed to discover services from registry")
        registry_process.terminate()
        return False
    
    # Stop the AI agent's registry wrapper
    if ai_agent.service_wrapper:
        ai_agent.service_wrapper.stop()
    
    # Unregister the test service
    if client.unregister_service(test_service.id):
        print(f"✓ Test service {test_service.id} unregistered successfully")
    else:
        print(f"✗ Failed to unregister test service {test_service.id}")
    
    # Terminate the registry server
    registry_process.terminate()
    registry_process.wait()
    
    print("✓ MCP registry integration test completed successfully!")
    return True


def test_full_integration():
    """Test the full integration including DNS server"""
    print("\nStarting full MCP integration test (with DNS server)...")

    # Start the registry server
    print("Starting service registry server...")
    registry_process = start_registry_server(port=8088)

    # Give the server time to start
    time.sleep(3)

    # Start the DNS server
    print("Starting DNS server...")
    dns_process = start_dns_server(registry_port=8088, dns_port=8091)

    # Give the DNS server time to start and register
    time.sleep(5)

    # Test registry client functionality
    client = ServiceRegistryClient("http://127.0.0.1:8088")

    # Check if registry is healthy
    if client.check_health():
        print("✓ Registry health check passed")
    else:
        print("✗ Registry health check failed")
        registry_process.terminate()
        dns_process.terminate()
        return False
    
    # Discover DNS server service
    dns_services = client.discover_services(service_type="mcp_dns")
    if len(dns_services) > 0:
        print(f"✓ Discovered {len(dns_services)} DNS server services")
        for service in dns_services:
            print(f"  - {service.id} at {service.host}:{service.port}")
    else:
        print("✗ Failed to discover DNS server services")
        registry_process.terminate()
        dns_process.terminate()
        return False
    
    # Test DNS resolution through the server
    import socket
    import json
    
    # Create a request
    request = {
        "fqdn": "google.com"
    }
    
    # Convert request to JSON
    request_json = json.dumps(request)
    
    try:
        # Connect to the DNS server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 8089))
        
        # Send the request
        client_socket.sendall(request_json.encode('utf-8'))
        
        # Receive the response
        response_data = client_socket.recv(4096)
        
        # Decode and parse the response
        response = json.loads(response_data.decode('utf-8'))
        
        print(f"✓ DNS resolution request successful: {json.dumps(response, indent=2)}")
        
        client_socket.close()
    except Exception as e:
        print(f"✗ DNS resolution request failed: {str(e)}")
        registry_process.terminate()
        dns_process.terminate()
        return False
    
    # Terminate the processes
    dns_process.terminate()
    dns_process.wait()
    registry_process.terminate()
    registry_process.wait()
    
    print("✓ Full MCP integration test completed successfully!")
    return True


if __name__ == "__main__":
    print("Running MCP Registry Integration Tests...\n")
    
    success1 = test_registry_integration()
    success2 = test_full_integration()
    
    if success1 and success2:
        print("\n🎉 All MCP registry integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP registry integration tests failed!")
        sys.exit(1)