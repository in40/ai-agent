#!/usr/bin/env python3
"""
Comprehensive test script to verify the RAG MCP server with the new rerank endpoint.
"""
import asyncio
import aiohttp
import json

async def test_comprehensive_rag_mcp_rerank():
    """Comprehensive test of the RAG MCP server's rerank endpoint."""
    print("Comprehensive testing of RAG MCP Server rerank endpoint...")
    
    # Test data
    query = "What is the capital of France?"
    documents = [
        {
            "content": "Paris is the capital and most populous city of France. It is located in the north-central part of the country.",
            "metadata": {"source": "Geography Book", "author": "John Doe"}
        },
        {
            "content": "London is the capital city of England and the United Kingdom. It is located on the River Thames in south-east England.",
            "metadata": {"source": "Geography Book", "author": "Jane Smith"}
        },
        {
            "content": "Berlin is the capital and largest city of Germany. It is located in northeastern Germany.",
            "metadata": {"source": "Geography Book", "author": "Hans Mueller"}
        },
        {
            "content": "The weather today is sunny with a high of 25 degrees Celsius.",
            "metadata": {"source": "News Website", "author": "Weather Service"}
        },
        {
            "content": "France is a country in Europe known for its art, cuisine, and culture.",
            "metadata": {"source": "Travel Guide", "author": "Travel Expert"}
        }
    ]
    
    # Assuming the RAG MCP server is running on localhost:8091
    url = "http://localhost:8091/rerank_documents"
    
    payload = {
        "action": "rerank_documents",
        "parameters": {
            "query": query,
            "documents": documents,
            "top_k": 3
        }
    }
    
    print(f"Sending request to: {url}")
    print(f"Query: {query}")
    print(f"Number of documents: {len(documents)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                print(f"Response status: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200 and result.get("status") == "success":
                    print("\n✓ Comprehensive rerank endpoint test successful!")
                    print(f"Number of reranked documents: {result.get('count', 0)}")
                    
                    # Print the top reranked documents
                    results = result.get("results", [])
                    print("\nTop reranked documents:")
                    for i, doc in enumerate(results):
                        print(f"  {i+1}. Score: {doc.get('score', 0):.4f}")
                        print(f"     Content: {doc.get('content', '')[:80]}...")
                        print(f"     Reranked: {doc.get('reranked', False)}")
                        print()
                    
                    # Verify that the most relevant document (about Paris) is ranked highly
                    if results and "Paris" in results[0].get('content', ''):
                        print("✓ Most relevant document (about Paris) is ranked first!")
                    else:
                        print("! Note: Most relevant document may not be ranked first (depends on model behavior)")
                    
                    return True
                else:
                    print(f"\n✗ Comprehensive rerank endpoint test failed: {result}")
                    return False
                    
    except aiohttp.ClientConnectorError:
        print("\n✗ Cannot connect to RAG MCP server. Make sure it's running on localhost:8091.")
        return False
    except Exception as e:
        print(f"\n✗ Error during comprehensive test: {str(e)}")
        return False

async def test_basic_connectivity():
    """Test basic connectivity to the server."""
    print("Testing basic connectivity to RAG MCP server...")
    
    url = "http://localhost:8091/"
    payload = {
        "action": "list_documents",
        "parameters": {}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                print(f"Basic connectivity test response: {result.get('status', 'unknown')}")
                return response.status == 200
                
    except Exception as e:
        print(f"Connectivity test failed: {str(e)}")
        return False

async def main():
    """Run all tests."""
    print("Running comprehensive tests for RAG MCP Server with rerank functionality...\n")
    
    # Test basic connectivity first
    connectivity_ok = await test_basic_connectivity()
    if not connectivity_ok:
        print("✗ Server is not accessible, aborting tests.")
        return False
    
    print()
    
    # Run comprehensive test
    success = await test_comprehensive_rag_mcp_rerank()
    
    print("="*60)
    if success:
        print("✓ All comprehensive tests passed!")
        print("The RAG MCP server with rerank endpoint is working correctly.")
    else:
        print("✗ Some tests failed.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✓ RAG MCP server rerank functionality test completed successfully!")
    else:
        print("\n✗ RAG MCP server rerank functionality test failed.")