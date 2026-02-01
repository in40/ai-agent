#!/usr/bin/env python3
"""
Simple test to verify that source information is properly preserved in the final output.
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
    """Test that source information is properly preserved in the normalization process."""
    print("Testing source information preservation...")
    
    # Create a sample document with proper source information in metadata
    sample_doc_with_source = {
        "content": "This is a sample document content about biometric requirements...",
        "metadata": {
            "source": "GOST_R_52633.3-2011",  # This should be preserved as the source
            "chunk_id": 11,
            "section": "6.2.6_6.2.7",
            "title": "Medium DB Testing: Generation Forecasting and Formula (2)",
            "chunk_type": "formula_with_context",
            "token_count": 418,
            "contains_formula": True,
            "upload_method": "Processed JSON Import",
            "user_id": "40in",
            "stored_file_path": "./data/rag_uploaded_files/b741aabd-d069-4b7c-94fa-b5f684158dcd/GOST_R_52633.3-2011.json",
            "file_id": "b741aabd-d069-4b7c-94fa-b5f684158dcd"
        },
        "score": 0.8336984377511674
    }
    
    # Create a sample search result with URL
    sample_search_result = {
        "title": "ГОСТ Р 52633.1-2009 Защита информации...",
        "url": "http://docs.cntd.ru/document/1200079555",
        "description": "Requirements for small biometric image databases...",
        "summary": "This document specifies requirements for small biometric image databases used in testing high-reliability biometric authentication systems.",
        "original_description": "Необходимые для ... баз легко осуществимо, а для образов \"Чужой\" велики (1012 образов и больше)....",
        "relevance_score": 0.9869208057773704
    }
    
    # Test normalization of document with source in metadata
    normalized_doc = normalize_mcp_result(sample_doc_with_source, "rag")
    print(f"Original source in metadata: {sample_doc_with_source['metadata']['source']}")
    print(f"Normalized source field: {normalized_doc['source']}")
    print(f"Normalized source type: {normalized_doc['source_type']}")

    # Test normalization of search result with URL
    normalized_search = normalize_mcp_result(sample_search_result, "search")
    print(f"\nSearch result URL: {sample_search_result['url']}")
    print(f"Normalized search source: {normalized_search['source']}")
    print(f"Normalized search source type: {normalized_search['source_type']}")
    
    # Verify that source information is properly preserved
    doc_source_preserved = normalized_doc['source'] == "GOST_R_52633.3-2011"
    search_source_extracted = "docs.cntd.ru" in normalized_search['source']  # Should extract domain from URL
    
    print(f"\nDocument source properly preserved: {doc_source_preserved}")
    print(f"Search source properly extracted from URL: {search_source_extracted}")
    
    if doc_source_preserved and search_source_extracted:
        print("\n✅ SUCCESS: Source information is properly preserved in normalized results!")
        print("   - Document source from metadata is preserved")
        print("   - Search result source is extracted from URL")
        return True
    else:
        print("\n❌ FAILURE: Source information is not properly preserved")
        if not doc_source_preserved:
            print("   - Document source from metadata not preserved")
        if not search_source_extracted:
            print("   - Search result source not properly extracted from URL")
        return False


def test_formatting_logic():
    """Test the document formatting logic that creates the final output."""
    print("\nTesting document formatting logic...")
    
    # Simulate documents with different source formats
    test_docs = [
        {
            "content": "First document content...",
            "source": "GOST_R_52633.3-2011",  # Direct source field
            "metadata": {"source": "GOST_R_52633.3-2011", "title": "Test Document 1"}
        },
        {
            "content": "Second document content...",
            "metadata": {"source": "GOST_R_52633.1-2009"},  # Source in metadata
            "title": "Test Document 2"
        },
        {
            "content": "Third document content...",
            "url": "http://example.com/doc3",  # Source should be extracted from URL
            "title": "Test Document 3"
        },
        {
            "content": "Fourth document content...",
            "metadata": {},  # No source information
            "title": "Test Document 4"
        }
    ]
    
    # Apply the same formatting logic as in augment_context_node
    formatted_docs = []
    for i, doc in enumerate(test_docs):
        content = doc.get("content", doc.get("page_content", ""))
        
        # Extract source information with priority hierarchy
        source = "Unknown source"
        
        # 1. First, try to get source from the main document field
        if doc.get("source") and doc["source"].strip() != "":
            source = doc["source"]
        # 2. Then try from metadata fields
        elif doc.get("metadata"):
            metadata = doc["metadata"]
            # Check various possible source fields in metadata
            for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
                if metadata.get(field_name) and metadata[field_name].strip() != "":
                    source = metadata[field_name]
                    break
            # If still unknown and there's a source in metadata with specific naming convention
            if source == "Unknown source" and metadata.get("source"):
                source = metadata["source"]
        # 3. If it's a processed search result, try to extract source from URL or title
        elif doc.get("url"):
            import urllib.parse
            parsed_url = urllib.parse.urlparse(doc["url"])
            if parsed_url.netloc:
                source = parsed_url.netloc
            else:
                source = doc["url"][:50] + "..."  # Use first 50 chars of URL as source
        # 4. If it's a processed search result with title
        elif doc.get("title"):
            source = doc["title"]
        
        formatted_doc = f"Document {i+1} ({source}):\n{content}\n"
        formatted_docs.append(formatted_doc)
        
        print(f"  Document {i+1}: source='{source}'")
    
    # Check that sources were properly extracted
    sources = [doc.split('(')[1].split(')')[0] for doc in formatted_docs]
    expected_sources = ["GOST_R_52633.3-2011", "GOST_R_52633.1-2009", "example.com", "Test Document 4"]
    
    all_correct = True
    for i, (actual, expected) in enumerate(zip(sources, expected_sources)):
        if expected in actual or actual == expected:
            print(f"    ✓ Document {i+1} source correctly identified: {actual}")
        else:
            print(f"    ✗ Document {i+1} source incorrect. Expected: {expected}, Got: {actual}")
            all_correct = False
    
    if all_correct:
        print("\n✅ SUCCESS: Document formatting logic properly extracts source information!")
        return True
    else:
        print("\n❌ FAILURE: Document formatting logic has issues with source extraction")
        return False


if __name__ == "__main__":
    print("🔍 Testing Source Information Preservation")
    print("="*60)
    
    test1_success = test_source_preservation()
    test2_success = test_formatting_logic()
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS:")
    print(f"  Source normalization test:  {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  Formatting logic test:      {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    overall_success = test1_success and test2_success
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Source information will be properly preserved in final output")
        print(f"   Documents will show correct source names instead of 'Unknown source'")
    else:
        print(f"\n💥 SOME TESTS FAILED!")
        print(f"   Source information preservation needs attention")
    
    sys.exit(0 if overall_success else 1)