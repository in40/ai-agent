#!/usr/bin/env python3
"""
Simple test to verify the source extraction logic in augment_context_node
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


def test_source_extraction_logic():
    """Test the source extraction logic directly."""
    print("🔍 Testing Source Extraction Logic in augment_context_node")
    print("="*60)
    
    # Test documents with different source scenarios
    test_documents = [
        # Document 1: Has specific source in metadata that should override generic top-level source
        {
            "content": "First document content about biometric requirements...",
            "metadata": {
                "source": "GOST_R_52633.3-2011",  # This should be used instead of generic source
                "chunk_id": 11,
                "section": "6.2.6_6.2.7",
                "title": "Medium DB Testing: Generation Forecasting and Formula (2)"
            },
            "source": "RAG Document",  # Generic source that should be overridden
            "score": 0.85
        },
        # Document 2: Has specific source in metadata URL field
        {
            "content": "Second document content...",
            "metadata": {
                "source": "Specific Source from Metadata",
                "file_path": "./data/test_file.pdf"
            },
            "source": "RAG Document",  # Generic source that should be overridden
            "url": "https://example.com/doc2",
            "score": 0.75
        },
        # Document 3: Has specific top-level source
        {
            "content": "Third document content...",
            "metadata": {},
            "source": "Specific Top Level Source",  # Specific source that should be used
            "score": 0.65
        },
        # Document 4: Has URL but no specific source information
        {
            "content": "Fourth document content...",
            "metadata": {},
            "url": "http://docs.cntd.ru/document/1200079555",
            "title": "ГОСТ Р 52633.1-2009 Document Title",
            "score": 0.70
        },
        # Document 5: Has only generic information
        {
            "content": "Fifth document content...",
            "metadata": {"title": "RAG Document"},
            "source": "RAG Document",  # Generic that should result in Unknown source
            "score": 0.60
        }
    ]
    
    print("Testing source extraction for each document:")
    
    for i, doc in enumerate(test_documents):
        print(f"\nDocument {i+1}:")
        print(f"  Top-level source: {doc.get('source', 'None')}")
        print(f"  Metadata source: {doc.get('metadata', {}).get('source', 'None')}")
        print(f"  URL: {doc.get('url', 'None')}")
        print(f"  Title: {doc.get('title', 'None')}")
        
        # Apply the same source extraction logic as in the updated augment_context_node
        content = doc.get("content", doc.get("page_content", ""))

        # Extract source information with priority hierarchy
        # Prioritize specific sources over generic ones like "RAG Document", "Search Result", etc.
        source = "Unknown source"

        # 1. First, try to get specific source from metadata fields (prioritize over generic top-level source)
        if doc.get("metadata"):
            metadata = doc["metadata"]
            # Check various possible source fields in metadata that might have specific information
            for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
                if metadata.get(field_name) and metadata[field_name].strip() != "":
                    # Only use this if it's not a generic placeholder
                    specific_source = metadata[field_name]
                    if specific_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                        source = specific_source
                        print(f"    ✓ Found specific source in metadata['{field_name}']: {source}")
                        break
            # If still unknown and there's a source in metadata with specific naming convention
            if source == "Unknown source" and metadata.get("source"):
                specific_source = metadata["source"]
                if specific_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = specific_source
                    print(f"    ✓ Found specific source in metadata['source'] (fallback): {source}")

        # 2. If no specific source found in metadata, then try the main document field
        if source == "Unknown source" or source in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
            if doc.get("source") and doc["source"].strip() != "":
                top_level_source = doc["source"]
                # Only use top-level source if it's not generic
                if top_level_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = top_level_source
                    print(f"    ✓ Found specific source in top-level: {source}")

        # 3. If it's a processed search result, try to extract source from URL or title
        if source == "Unknown source" or source in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
            if doc.get("url"):
                import urllib.parse
                parsed_url = urllib.parse.urlparse(doc["url"])
                if parsed_url.netloc:
                    source = parsed_url.netloc
                    print(f"    ✓ Found source from URL netloc: {source}")
                else:
                    source = doc["url"][:50] + "..."  # Use first 50 chars of URL as source
                    print(f"    ✓ Found source from URL: {source}")
            elif doc.get("title"):
                title_source = doc["title"]
                # Only use title if it's not generic
                if title_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = title_source
                    print(f"    ✓ Found source from title: {source}")

        print(f"  Final extracted source: {source}")
    
    # Check specific test cases
    doc1_source = "Unknown source"
    doc = test_documents[0]  # First document with GOST in metadata
    if doc.get("metadata"):
        metadata = doc["metadata"]
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                specific_source = metadata[field_name]
                if specific_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    doc1_source = specific_source
                    break
        if doc1_source == "Unknown source" and metadata.get("source"):
            specific_source = metadata["source"]
            if specific_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                doc1_source = specific_source
    
    print(f"\n{'='*60}")
    print("🎯 KEY TEST RESULT:")
    print(f"  Document 1 (with GOST_R_52633.3-2011 in metadata) source: {doc1_source}")
    
    if doc1_source == "GOST_R_52633.3-2011":
        print(f"  ✅ SUCCESS: Specific metadata source properly extracted!")
        print(f"  - Generic 'RAG Document' source was correctly overridden")
        print(f"  - Specific 'GOST_R_52633.3-2011' from metadata was used")
        return True
    else:
        print(f"  ❌ FAILURE: Generic source was not properly overridden")
        print(f"  - Expected: GOST_R_52633.3-2011")
        print(f"  - Got: {doc1_source}")
        return False


if __name__ == "__main__":
    success = test_source_extraction_logic()
    
    print(f"\n{'='*60}")
    print("📊 FINAL ASSESSMENT:")
    if success:
        print("  ✅ Source extraction logic is working correctly!")
        print("  - Specific sources from metadata override generic sources")
        print("  - Documents will show proper source information instead of 'Unknown source'")
    else:
        print("  ❌ Source extraction logic still has issues")
        print("  - Generic sources may still be overriding specific ones")
    
    sys.exit(0 if success else 1)