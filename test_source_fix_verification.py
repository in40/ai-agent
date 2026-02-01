#!/usr/bin/env python3
"""
Simple verification test to confirm that the source information fix is working.
"""
import sys
import os
from dotenv import dotenv_values

# Load environment variables
env_vars = dotenv_values("/root/qwen/ai_agent/.env")
os.environ.update(env_vars)

# Add the project root to the path
project_root = "/root/qwen/ai_agent"
sys.path.insert(0, project_root)

from utils.result_normalizer import normalize_mcp_result


def test_source_preservation():
    """Test that the source information is properly preserved in the final output."""
    print("🔍 Testing Source Information Preservation Fix")
    print("="*60)
    
    # Test 1: Search result with nested structure (from the logs)
    print("Test 1: Search result with nested structure...")
    search_result = {
        "service_id": "search-server-127-0-0-1-8090",
        "action": "brave_search",
        "parameters": {"query": "требования к малым базам биометрических образов Чужой"},
        "status": "success",
        "result": {
            "success": True,
            "result": {
                "success": True,
                "query": "требования к малым базам биометрических образов Чужой",
                "results": [
                    {
                        "title": "ГОСТ Р 52633.1-2009 Защита информации...",
                        "url": "http://docs.cntd.ru/document/1200079555",
                        "description": "Requirements for small biometric image databases..."
                    },
                    {
                        "title": "Another search result",
                        "url": "https://cyberleninka.ru/article/n/example",
                        "description": "Another relevant document..."
                    }
                ],
                "error": None
            }
        },
        "timestamp": "2026-01-31T06:52:30.703403Z"
    }
    
    normalized_search = normalize_mcp_result(search_result, "search")
    print(f"  Original service_id: {search_result['service_id']}")
    print(f"  Normalized source: {normalized_search['source']}")
    print(f"  Normalized source type: {normalized_search['source_type']}")
    
    search_source_ok = "docs.cntd.ru" in normalized_search['source'] or "Search" in normalized_search['source']
    print(f"  ✅ Search source properly extracted: {search_source_ok}")
    
    # Test 2: RAG document with metadata source
    print("\nTest 2: RAG document with metadata source...")
    rag_document = {
        "content": "This is content from a RAG document about biometric requirements...",
        "metadata": {
            "source": "GOST_R_52633.3-2011",
            "chunk_id": 11,
            "section": "6.2.6_6.2.7",
            "title": "Medium DB Testing: Generation Forecasting",
            "upload_method": "Processed JSON Import"
        },
        "score": 0.8336984377511674
    }
    
    normalized_rag = normalize_mcp_result(rag_document, "rag")
    print(f"  Original metadata source: {rag_document['metadata']['source']}")
    print(f"  Normalized source: {normalized_rag['source']}")
    print(f"  Normalized source type: {normalized_rag['source_type']}")
    
    rag_source_ok = normalized_rag['source'] == "GOST_R_52633.3-2011"
    print(f"  ✅ RAG source properly preserved: {rag_source_ok}")
    
    # Test 3: Combined scenario - what happens when both are in the final output
    print("\nTest 3: Simulating final output with both search and RAG results...")
    
    # Simulate how documents would be formatted in the augment_context_node
    all_documents = [normalized_search, normalized_rag]
    
    formatted_output = []
    for i, doc in enumerate(all_documents):
        content = doc.get("content", doc.get("page_content", ""))[:200] + "..."  # Preview
        source = doc.get("source", "Unknown source")
        formatted_doc = f"Document {i+1} ({source}):\n{content}"
        formatted_output.append(formatted_doc)
        print(f"  {formatted_doc}")
    
    # Check that both sources are meaningful (not "Unknown source")
    all_sources_meaningful = all("Unknown source" not in doc.get("source", "Unknown source") for doc in all_documents)
    print(f"  ✅ All sources are meaningful (not 'Unknown source'): {all_sources_meaningful}")
    
    print(f"\n{'='*60}")
    print("📊 FINAL RESULTS:")
    print(f"  Search result source extraction: {'✅ PASS' if search_source_ok else '❌ FAIL'}")
    print(f"  RAG document source preservation: {'✅ PASS' if rag_source_ok else '❌ FAIL'}")
    print(f"  All sources meaningful in output: {'✅ PASS' if all_sources_meaningful else '❌ FAIL'}")
    
    overall_success = search_source_ok and rag_source_ok and all_sources_meaningful
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Source information is now properly preserved in final output")
        print(f"   Both search and RAG results show proper source information")
        print(f"   No more '(Unknown source)' labels in the final answer")
    else:
        print(f"\n💥 SOME TESTS FAILED!")
        print(f"   Source information preservation still has issues")
    
    return overall_success


if __name__ == "__main__":
    success = test_source_preservation()
    sys.exit(0 if success else 1)