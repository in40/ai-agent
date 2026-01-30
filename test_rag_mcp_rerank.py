#!/usr/bin/env python3
"""
Test script to verify the RAG MCP server with the new rerank endpoint.
"""
import asyncio
import aiohttp
import json

async def test_rag_mcp_rerank():
    """Test the RAG MCP server's rerank endpoint."""
    print("Testing RAG MCP Server rerank endpoint...")
    
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
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                print(f"Response status: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if response.status == 200 and result.get("status") == "success":
                    print("\n✓ Rerank endpoint test successful!")
                    print(f"Number of reranked documents: {result.get('count', 0)}")
                    
                    # Print the top reranked documents
                    results = result.get("results", [])
                    for i, doc in enumerate(results[:3]):
                        print(f"  {i+1}. Score: {doc.get('score', 0):.4f}, Content: {doc.get('content', '')[:60]}...")
                    
                    return True
                else:
                    print(f"\n✗ Rerank endpoint test failed: {result}")
                    return False
                    
    except aiohttp.ClientConnectorError:
        print("\n✗ Cannot connect to RAG MCP server. Make sure it's running on localhost:8091.")
        return False
    except Exception as e:
        print(f"\n✗ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_rag_mcp_rerank())
    if success:
        print("\n✓ RAG MCP server rerank endpoint test completed successfully!")
    else:
        print("\n✗ RAG MCP server rerank endpoint test failed.")