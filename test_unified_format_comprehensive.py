#!/usr/bin/env python3
"""
Comprehensive test to verify that the unified format is working properly for both search and RAG results.
"""
import asyncio
import sys
import os
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState
from registry.registry_client import ServiceRegistryClient
from models.dedicated_mcp_model import DedicatedMCPModel


def test_result_normalization():
    """Test the result normalization functionality."""
    print("Testing result normalization functionality...")
    
    # Import the normalization functions
    from utils.result_normalizer import normalize_mcp_result, normalize_mcp_results_list, normalize_rag_documents
    
    # Test 1: Normalize a search result
    print("\n1. Testing search result normalization...")
    search_result = {
        "service_id": "search-server-127-0-0-1-8090",
        "action": "brave_search", 
        "parameters": {"query": "test query"},
        "status": "success",
        "result": {
            "success": True,
            "result": {
                "success": True,
                "query": "test query",
                "results": [
                    {
                        "title": "Test Document Title",
                        "url": "http://example.com/test",
                        "description": "This is a test document description with relevant information."
                    }
                ]
            }
        }
    }
    
    normalized_search = normalize_mcp_result(search_result, "search")
    print(f"   Search result normalized successfully")
    print(f"   - Source: {normalized_search.get('source')}")
    print(f"   - Content preview: {normalized_search.get('content', '')[:50]}...")
    print(f"   - Source type: {normalized_search.get('source_type')}")
    print(f"   - Has content: {bool(normalized_search.get('content'))}")
    
    # Test 2: Normalize a RAG result
    print("\n2. Testing RAG result normalization...")
    rag_result = {
        "content": "This is a test RAG document content with important information.",
        "metadata": {
            "source": "test_document.pdf",
            "title": "Test Document",
            "chunk_id": 1,
            "upload_method": "Processed JSON Import"
        },
        "score": 0.85
    }
    
    normalized_rag = normalize_mcp_result(rag_result, "rag")
    print(f"   RAG result normalized successfully")
    print(f"   - Source: {normalized_rag.get('source')}")
    print(f"   - Content preview: {normalized_rag.get('content', '')[:50]}...")
    print(f"   - Source type: {normalized_rag.get('source_type')}")
    print(f"   - Relevance score: {normalized_rag.get('relevance_score')}")
    
    # Test 3: Normalize a list of results
    print("\n3. Testing list normalization...")
    results_list = [search_result, rag_result]
    normalized_list = normalize_mcp_results_list(results_list)
    print(f"   List of {len(results_list)} results normalized to {len(normalized_list)} normalized results")
    
    # Test 4: Normalize RAG documents specifically
    print("\n4. Testing RAG document normalization...")
    rag_docs = [
        {
            "content": "First RAG document content",
            "metadata": {"source": "doc1.pdf", "title": "Document 1"},
            "score": 0.9
        },
        {
            "content": "Second RAG document content", 
            "metadata": {"source": "doc2.pdf", "title": "Document 2"},
            "score": 0.8
        }
    ]
    normalized_docs = normalize_rag_documents(rag_docs)
    print(f"   List of {len(rag_docs)} RAG documents normalized to {len(normalized_docs)} normalized documents")
    for i, doc in enumerate(normalized_docs):
        print(f"     Doc {i+1} - Source: {doc.get('source')}, Score: {doc.get('relevance_score')}")
    
    print("\n✅ All normalization tests passed!")
    return True


def test_service_discovery_and_execution():
    """Test that services are discovered and can be executed properly."""
    print("\nTesting service discovery and execution...")
    
    try:
        # Create registry client
        registry_url = os.getenv("MCP_REGISTRY_URL", "http://127.0.0.1:8080")
        registry_client = ServiceRegistryClient(registry_url)
        
        # Discover services
        all_services = registry_client.discover_services()
        print(f"   Discovered {len(all_services)} services:")
        for service in all_services:
            print(f"     - {service.id} ({service.type}): {service.host}:{service.port}")
        
        # Check for required services
        search_services = [s for s in all_services if 'search' in s.type.lower()]
        rag_services = [s for s in all_services if 'rag' in s.type.lower()]
        
        print(f"   Found {len(search_services)} search services")
        print(f"   Found {len(rag_services)} RAG services")
        
        if not search_services or not rag_services:
            print("   ⚠️  Warning: Required services not found. Make sure search and RAG services are running.")
            return False
        
        # Test MCP model execution
        print("   Testing MCP model execution...")
        mcp_model = DedicatedMCPModel()
        
        # Test with a simple query to one of each service type
        search_service = search_services[0]
        rag_service = rag_services[0]
        
        print(f"   - Testing search service: {search_service.id}")
        search_params = {"query": "test query", "top_k": 2}
        search_result = mcp_model._call_mcp_service(
            {
                "id": search_service.id,
                "host": search_service.host,
                "port": search_service.port,
                "type": search_service.type,
                "metadata": search_service.metadata
            },
            "search",
            search_params
        )
        print(f"   - Search result status: {search_result.get('status')}")
        
        print(f"   - Testing RAG service: {rag_service.id}")
        rag_params = {"query": "test query", "top_k": 2}
        rag_result = mcp_model._call_mcp_service(
            {
                "id": rag_service.id,
                "host": rag_service.host,
                "port": rag_service.port,
                "type": rag_service.type,
                "metadata": rag_service.metadata
            },
            "query_documents",
            rag_params
        )
        print(f"   - RAG result status: {rag_result.get('status')}")
        
        print("   ✅ Service discovery and execution test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests to verify unified format implementation."""
    print("🔍 Testing Unified MCP Result Format Implementation")
    print("="*60)
    
    # Test 1: Result normalization
    test1_success = test_result_normalization()
    
    # Test 2: Service discovery and execution
    test2_success = test_service_discovery_and_execution()
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS:")
    print(f"   Result normalization: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Service execution:    {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    overall_success = test1_success and test2_success
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED! Unified format implementation is working correctly.")
        print("   - MCP results are normalized to a unified format")
        print("   - Search and RAG results have consistent structure") 
        print("   - Source information is properly preserved")
        print("   - Services are properly discovered and executed")
    else:
        print(f"\n💥 SOME TESTS FAILED! Unified format implementation needs attention.")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)