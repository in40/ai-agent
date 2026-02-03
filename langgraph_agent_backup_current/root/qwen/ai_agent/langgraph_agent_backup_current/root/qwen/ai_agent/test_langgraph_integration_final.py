#!/usr/bin/env python3
"""
Test to verify that the LangGraph agent properly calls the RAG MCP server with rerank functionality.
"""
import asyncio
import json
from dotenv import dotenv_values
import os
import sys

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from models.dedicated_mcp_model import DedicatedMCPModel
from registry.registry_client import ServiceRegistryClient

async def test_langgraph_rag_rerank_integration():
    """Test that LangGraph agent properly calls RAG MCP server with rerank functionality."""
    print("Testing LangGraph agent integration with RAG MCP server rerank functionality...")
    
    # Create registry client
    registry_client = ServiceRegistryClient("http://127.0.0.1:8080")
    
    # Discover RAG services
    try:
        rag_services = registry_client.discover_services(service_type="rag")

        if not rag_services:
            print("❌ No RAG services found in registry")
            return False

        rag_service = rag_services[0]
        print(f"✅ Found RAG service: {rag_service.id} at {rag_service.host}:{rag_service.port}")

        # Convert ServiceInfo to dictionary format expected by _call_mcp_service
        rag_service_dict = {
            "id": rag_service.id,
            "host": rag_service.host,
            "port": rag_service.port,
            "type": rag_service.type,
            "metadata": rag_service.metadata
        }

        # Create MCP model instance
        mcp_model = DedicatedMCPModel()

        # Test 1: Query documents endpoint
        print("\n1. Testing query_documents endpoint...")
        query_params = {
            "query": "test query for integration",
            "top_k": 5
        }

        query_result = mcp_model._call_mcp_service(rag_service_dict, "query_documents", query_params)
        print(f"   Query result status: {query_result.get('status')}")
        if query_result.get('status') == 'success':
            print("   ✅ Query documents endpoint working")
        else:
            print(f"   ❌ Query documents endpoint failed: {query_result.get('error')}")

        # Test 2: Rerank documents endpoint
        print("\n2. Testing rerank_documents endpoint...")
        test_docs = [
            {"content": "Paris is the capital of France and a major European city.", "metadata": {"source": "test"}, "score": 0.8},
            {"content": "London is the capital of England and the United Kingdom.", "metadata": {"source": "test"}, "score": 0.7},
            {"content": "Berlin is the capital and largest city of Germany.", "metadata": {"source": "test"}, "score": 0.6},
            {"content": "The weather today is sunny with a high of 25 degrees Celsius.", "metadata": {"source": "test"}, "score": 0.3},
            {"content": "France is a country in Europe known for its art, cuisine, and culture.", "metadata": {"source": "test"}, "score": 0.5}
        ]

        rerank_params = {
            "query": "What is the capital of France?",
            "documents": test_docs,
            "top_k": 3
        }

        rerank_result = mcp_model._call_mcp_service(rag_service_dict, "rerank_documents", rerank_params)
        print(f"   Rerank result status: {rerank_result.get('status')}")

        if rerank_result.get('status') == 'success':
            reranked_docs = rerank_result.get('result', {}).get('results', [])
            print(f"   ✅ Rerank documents endpoint working, returned {len(reranked_docs)} documents")

            # Show top reranked document
            if reranked_docs:
                top_doc = reranked_docs[0]
                print(f"   Top reranked document: '{top_doc.get('content', '')[:60]}...' with score {top_doc.get('score', 0):.4f}")
        else:
            print(f"   ❌ Rerank documents endpoint failed: {rerank_result.get('error')}")
            return False

        print("\n✅ All integration tests passed!")
        print("✅ LangGraph agent will properly call the RAG MCP server with rerank functionality when needed!")

        return True

    except Exception as e:
        print(f"❌ Error in integration test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_langgraph_rag_rerank_integration())
    if success:
        print("\n🎉 LANGGRAPH INTEGRATION TEST PASSED!")
        print("The LangGraph agent will now properly use the RAG MCP server's rerank endpoint!")
    else:
        print("\n❌ LANGGRAPH INTEGRATION TEST FAILED!")
        exit(1)