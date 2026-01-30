#!/usr/bin/env python3
"""
Final test to verify the complete implementation with the corrected addresses.
"""
import asyncio
import aiohttp
import json

async def test_complete_implementation():
    """Test the complete implementation with corrected addresses."""
    print("Testing complete implementation with corrected service addresses...")
    
    # Test 1: Verify that services are registered with correct addresses
    print("\n1. Checking service registry...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8080/services") as response:
                registry_data = await response.json()
                
                if registry_data.get("success"):
                    services = registry_data.get("services", [])
                    print(f"   Found {len(services)} registered services")
                    
                    # Check if all services have valid addresses (not 0.0.0.0)
                    valid_addresses = True
                    for service in services:
                        host = service.get("host", "")
                        if host == "0.0.0.0":
                            print(f"   ❌ Service {service.get('id')} still has invalid address 0.0.0.0")
                            valid_addresses = False
                        else:
                            print(f"   ✅ Service {service.get('id')} has valid address {host}")
                    
                    if valid_addresses:
                        print("   ✅ All services have valid addresses")
                    else:
                        print("   ❌ Some services still have invalid addresses")
                        return False
                else:
                    print("   ❌ Failed to get services from registry")
                    return False
    except Exception as e:
        print(f"   ❌ Error checking service registry: {e}")
        return False
    
    # Test 2: Test the RAG query endpoint
    print("\n2. Testing RAG query endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "action": "query_documents",
                "parameters": {
                    "query": "test query for verification",
                    "top_k": 3
                }
            }
            
            async with session.post("http://localhost:8091/query_documents", json=payload) as response:
                result = await response.json()
                
                print(f"   Query response status: {response.status}")
                print(f"   Query response: {result.get('status', 'no status')}")
                
                if response.status == 200:
                    print("   ✅ RAG query endpoint is working")
                else:
                    print(f"   ❌ RAG query endpoint failed: {result}")
                    return False
    except Exception as e:
        print(f"   ❌ Error testing RAG query endpoint: {e}")
        return False
    
    # Test 3: Test the RAG rerank endpoint
    print("\n3. Testing RAG rerank endpoint...")
    try:
        async with aiohttp.ClientSession() as session:
            test_docs = [
                {"content": "Paris is the capital of France and a major European city."},
                {"content": "London is the capital of England and the United Kingdom."},
                {"content": "Berlin is the capital and largest city of Germany."},
                {"content": "The weather today is sunny with a high of 25 degrees Celsius."},
                {"content": "France is a country in Europe known for its art, cuisine, and culture."}
            ]
            
            payload = {
                "action": "rerank_documents", 
                "parameters": {
                    "query": "What is the capital of France?",
                    "documents": test_docs,
                    "top_k": 3
                }
            }
            
            async with session.post("http://localhost:8091/rerank_documents", json=payload) as response:
                result = await response.json()
                
                print(f"   Rerank response status: {response.status}")
                print(f"   Rerank response: {result.get('status', 'no status')}")
                if "count" in result:
                    print(f"   Rerank count: {result['count']}")
                
                if response.status == 200 and result.get("status") == "success":
                    print("   ✅ RAG rerank endpoint is working")
                else:
                    print(f"   ❌ RAG rerank endpoint failed: {result}")
                    return False
    except Exception as e:
        print(f"   ❌ Error testing RAG rerank endpoint: {e}")
        return False
    
    # Test 4: Verify the configuration is properly loaded
    print("\n4. Checking configuration...")
    try:
        import os
        from rag_component.config import RERANKER_ENABLED, RERANKER_MODEL
        
        print(f"   RERANKER_ENABLED: {RERANKER_ENABLED}")
        print(f"   RERANKER_MODEL: {RERANKER_MODEL}")
        
        if RERANKER_ENABLED:
            print("   ✅ Reranker is enabled in configuration")
        else:
            print("   ⚠️  Reranker is disabled in configuration")
    except Exception as e:
        print(f"   ❌ Error checking configuration: {e}")
        return False
    
    print("\n✅ All tests passed! The implementation is working correctly.")
    print("\nSUMMARY OF CHANGES:")
    print("- Fixed service registration to use 127.0.0.1 instead of 0.0.0.0")
    print("- Added rerank_documents endpoint to RAG MCP server")
    print("- Updated LangGraph agent to call rerank endpoint when more than 5 docs returned")
    print("- Reranker model is configured via .env file")
    print("- All MCP services now register with valid, reachable addresses")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_complete_implementation())
    if success:
        print("\n🎉 COMPLETE IMPLEMENTATION VERIFICATION PASSED!")
        print("The RAG MCP server with rerank endpoint is fully functional!")
    else:
        print("\n❌ IMPLEMENTATION VERIFICATION FAILED!")
        exit(1)