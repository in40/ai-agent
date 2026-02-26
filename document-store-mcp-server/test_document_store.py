#!/usr/bin/env python3
"""Test Document Store MCP Server"""
import requests
import json

SERVER_URL = "http://localhost:3070/mcp"


def test_list_tools():
    """Test listing available tools"""
    print("📋 Testing list_tools...")
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/list",
            "params": {}
        }
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if "result" in result:
        tools = result["result"]["tools"]
        print(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"      - {tool['name']}")
    else:
        print(f"   ❌ Error: {result}")
    print()


def test_list_ingestion_jobs():
    """Test listing ingestion jobs"""
    print("📋 Testing list_ingestion_jobs...")
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/call",
            "params": {
                "name": "list_ingestion_jobs",
                "arguments": {}
            }
        }
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if "result" in result:
        tool_result = result["result"]["content"][0]["text"]
        print(f"   ✅ Result: {tool_result[:200]}...")
    else:
        print(f"   ❌ Error: {result}")
    print()


def test_store_and_retrieve():
    """Test storing and retrieving a document"""
    print("📋 Testing store_document...")
    
    # Store a test document
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "3",
            "method": "tools/call",
            "params": {
                "name": "store_document",
                "arguments": {
                    "job_id": "test_job_001",
                    "doc_id": "test_doc_001",
                    "content": "This is a test document content for testing purposes.",
                    "format": "txt",
                    "metadata": {
                        "source": "test",
                        "pages": 1,
                        "size": 56
                    }
                }
            }
        }
    )
    print(f"   Store Status: {response.status_code}")
    store_result = response.json()
    print(f"   Store Result: {store_result}")
    print()
    
    # Retrieve the document
    print("📋 Testing get_document...")
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "4",
            "method": "tools/call",
            "params": {
                "name": "get_document",
                "arguments": {
                    "job_id": "test_job_001",
                    "doc_id": "test_doc_001",
                    "format": "txt"
                }
            }
        }
    )
    print(f"   Get Status: {response.status_code}")
    get_result = response.json()
    print(f"   Get Result: {get_result}")
    print()
    
    # List documents
    print("📋 Testing list_documents...")
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "5",
            "method": "tools/call",
            "params": {
                "name": "list_documents",
                "arguments": {
                    "job_id": "test_job_001"
                }
            }
        }
    )
    print(f"   List Status: {response.status_code}")
    list_result = response.json()
    print(f"   List Result: {list_result}")
    print()


def test_search():
    """Test searching documents"""
    print("📋 Testing search_documents...")
    response = requests.post(
        SERVER_URL,
        json={
            "jsonrpc": "2.0",
            "id": "6",
            "method": "tools/call",
            "params": {
                "name": "search_documents",
                "arguments": {
                    "job_id": "test_job_001",
                    "query": "test",
                    "limit": 10
                }
            }
        }
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    print(f"   Result: {result}")
    print()


def main():
    print("=" * 60)
    print("Document Store MCP Server - Test Suite")
    print("=" * 60)
    print()
    
    # Check if server is running
    try:
        print("🔍 Checking server connectivity...")
        response = requests.post(
            SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": "0",
                "method": "tools/list",
                "params": {}
            },
            timeout=5
        )
        print(f"   ✅ Server is running on {SERVER_URL}")
        print()
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Server is not running on {SERVER_URL}")
        print(f"   💡 Start server: ./start_server.sh")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Run tests
    test_list_tools()
    test_list_ingestion_jobs()
    test_store_and_retrieve()
    test_search()
    
    print("=" * 60)
    print("✅ Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
