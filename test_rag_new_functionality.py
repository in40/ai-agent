#!/usr/bin/env python3
"""
Test script to verify the new RAG functionality with download and summarization.
This script tests the enhanced RAG functionality where search results are processed 
with download and summarization before being reranked.
"""

import sys
import os
import asyncio
from pprint import pprint

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_rag_search_with_download():
    """Test the new RAG search functionality with download and summarization."""
    print("Testing new RAG search functionality with download and summarization...")
    
    try:
        from rag_component.main import RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize RAG orchestrator with an LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        print("✓ Successfully created RAG orchestrator")
        
        # Create mock search results
        mock_search_results = [
            {
                "title": "Example Article 1",
                "url": "https://example.com/article1",
                "description": "This is an example article about technology."
            },
            {
                "title": "Example Article 2", 
                "url": "https://example.com/article2",
                "description": "This is another example article about science."
            }
        ]
        
        user_query = "What are the latest developments in AI?"
        
        print(f"Processing {len(mock_search_results)} search results with download and summarization...")
        
        # Call the new method
        processed_results = rag_orchestrator.process_search_results_with_download(
            search_results=mock_search_results,
            user_query=user_query
        )
        
        print(f"✓ Processed {len(processed_results)} results")
        
        if processed_results:
            print("\nTop processed results:")
            for i, result in enumerate(processed_results):
                print(f"  {i+1}. Title: {result['title']}")
                print(f"     URL: {result['url']}")
                print(f"     Relevance Score: {result['relevance_score']}")
                print(f"     Summary Length: {len(result['summary'])}")
                print(f"     Summary Preview: {result['summary'][:100]}...")
                print()
        
        print("✓ RAG search with download and summarization test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error during RAG test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_mcp_server():
    """Test the RAG MCP server with the new functionality."""
    print("\nTesting RAG MCP server with new functionality...")
    
    try:
        from rag_component.rag_mcp_server import RAGRequestHandler, RAGOrchestrator
        from models.response_generator import ResponseGenerator
        
        # Initialize RAG orchestrator with an LLM
        response_gen = ResponseGenerator()
        llm = response_gen.llm
        rag_orchestrator = RAGOrchestrator(llm=llm)
        
        # Create request handler
        handler = RAGRequestHandler(rag_orchestrator)
        
        print("✓ Created RAG request handler")
        
        # Create a test request for the new functionality
        test_request = {
            "action": "process_search_results_with_download",
            "parameters": {
                "search_results": [
                    {
                        "title": "Example Article 1",
                        "url": "https://example.com/article1", 
                        "description": "This is an example article about technology."
                    },
                    {
                        "title": "Example Article 2",
                        "url": "https://example.com/article2",
                        "description": "This is another example article about science."
                    }
                ],
                "user_query": "What are the latest developments in AI?"
            }
        }
        
        print("Processing request with new functionality...")
        
        # Handle the request
        result = await handler.handle_request(test_request)
        
        print("✓ RAG MCP server processed request")
        print(f"Response status: {result.get('status', 'unknown')}")
        print(f"Results count: {result.get('count', 0)}")
        
        if result.get('results'):
            print("\nSample processed result:")
            sample_result = result['results'][0]
            print(f"  Title: {sample_result.get('title', 'N/A')}")
            print(f"  URL: {sample_result.get('url', 'N/A')}")
            print(f"  Relevance Score: {sample_result.get('relevance_score', 'N/A')}")
            print(f"  Summary preview: {sample_result.get('summary', '')[:100]}...")
        
        print("✓ RAG MCP server test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error during RAG MCP server test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running tests for new RAG functionality with download and summarization")
    print("="*80)
    
    success1 = test_rag_search_with_download()
    success2 = asyncio.run(test_rag_mcp_server())
    
    print("\n" + "="*80)
    if success1 and success2:
        print("✓ All RAG tests passed!")
    else:
        print("✗ Some RAG tests failed")
        sys.exit(1)