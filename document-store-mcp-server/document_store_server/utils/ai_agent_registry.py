"""
AI Agent Registry Integration for Document Store MCP Server
Wraps the ai_agent registry client for use with Document Store
"""
import sys
import os
import threading
import time
from datetime import datetime

# Add ai_agent registry to path
AI_AGENT_ROOT = "/root/qwen/ai_agent"
sys.path.insert(0, AI_AGENT_ROOT)
sys.path.insert(0, os.path.join(AI_AGENT_ROOT, 'registry'))

try:
    from registry_client import ServiceInfo, ServiceRegistryClient
    REGISTRY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import ai_agent registry client: {e}")
    REGISTRY_AVAILABLE = False


class AIAgentRegistryIntegration:
    """Integrates Document Store with ai_agent service registry"""
    
    def __init__(self, registry_url: str = "http://127.0.0.1:8080"):
        self.registry_url = registry_url
        self.registry_client = None
        self.service_id = None
        self.heartbeat_thread = None
        self.running = False
        
        if REGISTRY_AVAILABLE:
            self.registry_client = ServiceRegistryClient(registry_url)
    
    def register(
        self,
        host: str = "127.0.0.1",
        port: int = 3070,
        ttl: int = 60
    ) -> bool:
        """
        Register Document Store with ai_agent registry.
        
        Args:
            host: Service host address
            port: Service port
            ttl: Time-to-live for registration (seconds)
            
        Returns:
            True if registration successful
        """
        if not REGISTRY_AVAILABLE or not self.registry_client:
            print("⚠️  Registry client not available, skipping registration")
            return False
        
        try:
            # Create service ID
            self.service_id = f"document-store-{host}:{port}"
            
            # Create service info
            service_info = ServiceInfo(
                id=self.service_id,
                host=host,
                port=port,
                type="mcp",
                metadata={
                    "name": "Document Store MCP Server",
                    "description": "Store and retrieve documents from ingestion jobs",
                    "tools": [
                        "list_ingestion_jobs",
                        "list_documents",
                        "get_document",
                        "get_document_batch",
                        "get_document_metadata",
                        "search_documents",
                        "delete_job_documents",
                        "store_document"
                    ],
                    "started_at": datetime.now().isoformat()
                }
            )
            
            # Register with registry
            print(f"📝 Registering with ai_agent registry at {self.registry_url}...")
            success = self.registry_client.register_service(service_info, ttl)
            
            if success:
                print(f"✅ Registered as '{self.service_id}'")
                # Start heartbeat thread
                self._start_heartbeat(ttl)
                return True
            else:
                print(f"❌ Registration failed")
                return False
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def _start_heartbeat(self, ttl: int):
        """Start heartbeat thread"""
        self.running = True
        
        def send_heartbeat():
            while self.running:
                try:
                    if self.service_id and self.registry_client:
                        self.registry_client.heartbeat(self.service_id, ttl)
                    time.sleep(ttl / 2)  # Send at half TTL interval
                except Exception as e:
                    print(f"⚠️  Heartbeat failed: {e}")
                    time.sleep(5)
        
        self.heartbeat_thread = threading.Thread(target=send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        print(f"💓 Heartbeat started (interval: {ttl/2}s)")
    
    def unregister(self):
        """Unregister from registry"""
        self.running = False
        
        if self.registry_client and self.service_id:
            try:
                print(f"📝 Unregistering {self.service_id}...")
                self.registry_client.unregister_service(self.service_id)
                print(f"✅ Unregistered successfully")
            except Exception as e:
                print(f"⚠️  Unregister error: {e}")
    
    def __del__(self):
        self.unregister()
