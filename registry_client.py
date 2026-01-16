#!/usr/bin/env python3
"""
MCP Registry Client - Library for MCP services to interact with the service registry
"""

import json
import threading
import time
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Any
import requests


@dataclass
class ServiceInfo:
    """Data class representing information about a registered service"""
    id: str              # Unique service identifier
    host: str            # Service host address
    port: int            # Service port
    type: str = "mcp"    # Service type
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class ServiceRegistryClient:
    """Client class for interacting with the service registry"""
    
    def __init__(self, registry_url: str):
        self.registry_url = registry_url.rstrip('/')
        self.session = requests.Session()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def register_service(self, service_info: ServiceInfo, ttl: int) -> bool:
        """Register a service with the registry"""
        try:
            url = f"{self.registry_url}/register"
            payload = {
                'id': service_info.id,
                'host': service_info.host,
                'port': service_info.port,
                'type': service_info.type,
                'ttl': ttl,
                'metadata': service_info.metadata or {}
            }
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info(f"Service {service_info.id} registered successfully")
                    return True
                else:
                    self.logger.error(f"Failed to register service {service_info.id}: {result.get('message')}")
                    return False
            else:
                self.logger.error(f"Failed to register service {service_info.id}: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error registering service {service_info.id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error registering service {service_info.id}: {str(e)}")
            return False

    def unregister_service(self, service_id: str) -> bool:
        """Unregister a service from the registry"""
        try:
            url = f"{self.registry_url}/unregister/{service_id}"
            
            response = self.session.delete(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info(f"Service {service_id} unregistered successfully")
                    return True
                else:
                    self.logger.error(f"Failed to unregister service {service_id}: {result.get('message')}")
                    return False
            else:
                self.logger.error(f"Failed to unregister service {service_id}: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error unregistering service {service_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error unregistering service {service_id}: {str(e)}")
            return False

    def heartbeat(self, service_id: str, ttl: int) -> bool:
        """Send a heartbeat to update service expiration time"""
        try:
            url = f"{self.registry_url}/heartbeat"
            payload = {
                'id': service_id,
                'ttl': ttl
            }
            
            response = self.session.put(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.logger.info(f"Heartbeat sent for service {service_id}")
                    return True
                else:
                    self.logger.error(f"Failed to send heartbeat for service {service_id}: {result.get('message')}")
                    return False
            else:
                self.logger.error(f"Failed to send heartbeat for service {service_id}: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error sending heartbeat for service {service_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending heartbeat for service {service_id}: {str(e)}")
            return False

    def discover_services(self, service_type: Optional[str] = None, metadata_filters: Optional[Dict[str, Any]] = None) -> List[ServiceInfo]:
        """Discover services by type and metadata filters"""
        try:
            # Build query parameters
            params = {}
            if service_type:
                params['type'] = service_type
            
            if metadata_filters:
                for key, value in metadata_filters.items():
                    params[f'meta_{key}'] = value
            
            url = f"{self.registry_url}/discover"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    services_data = result.get('services', [])
                    services = []
                    
                    for service_data in services_data:
                        service = ServiceInfo(
                            id=service_data['id'],
                            host=service_data['host'],
                            port=service_data['port'],
                            type=service_data['type'],
                            metadata=service_data.get('metadata')
                        )
                        services.append(service)
                    
                    self.logger.info(f"Discovered {len(services)} services")
                    return services
                else:
                    self.logger.error(f"Failed to discover services: {result.get('message')}")
                    return []
            else:
                self.logger.error(f"Failed to discover services: HTTP {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error discovering services: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error discovering services: {str(e)}")
            return []

    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get specific service by ID"""
        try:
            url = f"{self.registry_url}/services/{service_id}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    service_data = result.get('service')
                    if service_data:
                        service = ServiceInfo(
                            id=service_data['id'],
                            host=service_data['host'],
                            port=service_data['port'],
                            type=service_data['type'],
                            metadata=service_data.get('metadata')
                        )
                        return service
                    else:
                        self.logger.warning(f"Service {service_id} not found")
                        return None
                else:
                    self.logger.error(f"Failed to get service {service_id}: {result.get('message')}")
                    return None
            else:
                self.logger.error(f"Failed to get service {service_id}: HTTP {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error getting service {service_id}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting service {service_id}: {str(e)}")
            return None

    def list_all_services(self) -> List[ServiceInfo]:
        """List all services in the registry"""
        try:
            url = f"{self.registry_url}/services"
            response = self.session.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    services_data = result.get('services', [])
                    services = []
                    
                    for service_data in services_data:
                        service = ServiceInfo(
                            id=service_data['id'],
                            host=service_data['host'],
                            port=service_data['port'],
                            type=service_data['type'],
                            metadata=service_data.get('metadata')
                        )
                        services.append(service)
                    
                    self.logger.info(f"Listed {len(services)} services")
                    return services
                else:
                    self.logger.error(f"Failed to list services: {result.get('message')}")
                    return []
            else:
                self.logger.error(f"Failed to list services: HTTP {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error listing services: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error listing services: {str(e)}")
            return []

    def check_health(self) -> bool:
        """Check if the registry is healthy"""
        try:
            url = f"{self.registry_url}/health"
            response = self.session.get(url)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'healthy':
                    self.logger.info("Registry health check passed")
                    return True
                else:
                    self.logger.warning(f"Registry health check failed: {result.get('status')}")
                    return False
            else:
                self.logger.error(f"Registry health check failed: HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error during health check: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during health check: {str(e)}")
            return False


class MCPServiceWrapper:
    """Wrapper that automates service registration and heartbeating"""
    
    def __init__(self, service_info: ServiceInfo, registry_url: str, heartbeat_interval: int = 20, ttl: int = 45):
        self.service_info = service_info
        self.registry_url = registry_url
        self.heartbeat_interval = heartbeat_interval
        self.ttl = ttl
        self.registry_client = ServiceRegistryClient(registry_url)
        self.heartbeat_thread = None
        self.running = False
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def start(self) -> bool:
        """Start the service wrapper (registers and begins heartbeating)"""
        try:
            # Register the service
            if not self.registry_client.register_service(self.service_info, self.ttl):
                self.logger.error(f"Failed to register service {self.service_info.id}")
                return False
            
            # Start the heartbeat thread
            self.running = True
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            self.logger.info(f"Service wrapper for {self.service_info.id} started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error starting service wrapper: {str(e)}")
            return False

    def stop(self):
        """Stop the service wrapper (stops heartbeating and unregisters)"""
        try:
            self.running = False
            
            if self.heartbeat_thread:
                self.heartbeat_thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            
            # Unregister the service
            self.registry_client.unregister_service(self.service_info.id)
            
            self.logger.info(f"Service wrapper for {self.service_info.id} stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping service wrapper: {str(e)}")

    def _heartbeat_loop(self):
        """Background thread that sends periodic heartbeats"""
        while self.running:
            try:
                # Send heartbeat
                success = self.registry_client.heartbeat(self.service_info.id, self.ttl)
                
                if not success:
                    self.logger.warning(f"Heartbeat failed for service {self.service_info.id}, attempting to re-register")
                    # Try to re-register the service
                    self.registry_client.register_service(self.service_info, self.ttl)
                
                # Wait for the next heartbeat
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop for service {self.service_info.id}: {str(e)}")
                time.sleep(self.heartbeat_interval)  # Wait before trying again


def main():
    """Example usage of the registry client"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Registry Client Example')
    parser.add_argument('--registry-url', type=str, default='http://127.0.0.1:8080',
                        help='URL of the service registry (default: http://127.0.0.1:8080)')
    parser.add_argument('--action', type=str, choices=['register', 'discover', 'test-wrapper'],
                        help='Action to perform: register, discover, or test-wrapper')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    if args.action == 'register':
        # Example of registering a service
        client = ServiceRegistryClient(args.registry_url)
        service_info = ServiceInfo(
            id="test-service-1",
            host="127.0.0.1",
            port=8081,
            type="api",
            metadata={
                "version": "1.0.0",
                "capabilities": ["rest_api", "json_processing"]
            }
        )
        
        success = client.register_service(service_info, ttl=60)
        if success:
            print(f"Service {service_info.id} registered successfully")
        else:
            print(f"Failed to register service {service_info.id}")
    
    elif args.action == 'discover':
        # Example of discovering services
        client = ServiceRegistryClient(args.registry_url)
        services = client.discover_services(service_type="api")
        print(f"Found {len(services)} API services:")
        for service in services:
            print(f"  - {service.id} at {service.host}:{service.port}")
    
    elif args.action == 'test-wrapper':
        # Example of using the service wrapper
        import signal
        import sys
        
        service_info = ServiceInfo(
            id="wrapped-test-service-1",
            host="127.0.0.1",
            port=8082,
            type="api",
            metadata={
                "version": "1.0.0",
                "capabilities": ["rest_api", "json_processing"]
            }
        )
        
        wrapper = MCPServiceWrapper(
            service_info=service_info,
            registry_url=args.registry_url,
            heartbeat_interval=20,
            ttl=45
        )
        
        # Handle graceful shutdown
        def signal_handler(sig, frame):
            print("\nShutting down service gracefully...")
            wrapper.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the service wrapper
        if wrapper.start():
            print(f"Service {service_info.id} started and registered")
            
            # Simulate service doing work
            try:
                while True:
                    time.sleep(10)
                    print(f"Service {service_info.id} is running...")
            except KeyboardInterrupt:
                print("\nShutting down service gracefully...")
                wrapper.stop()
        else:
            print(f"Failed to start service {service_info.id}")


if __name__ == '__main__':
    main()