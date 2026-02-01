#!/usr/bin/env python3
"""
Debug script to check the actual structure of documents in rag_documents
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


def debug_document_structure():
    """Debug the structure of documents to understand source extraction."""
    print("🔍 Debugging Document Structure and Source Extraction")
    print("="*60)
    
    # Test with a typical RAG document structure (from the logs)
    rag_document = {
        'content': 'Размножение осуществляют до момента, пока размер базы синтетических образов-потомков второго поколения не совпадет с размерами исходной базы естественных биометрических образов исходного (нулевого) поколения.',
        'metadata': {
            'source': 'GOST_R_52633.3-2011',
            'chunk_id': 11,
            'section': '6.2.6_6.2.7',
            'title': 'Medium DB Testing: Generation Forecasting and Formula (2) (with overlap)',
            'chunk_type': 'formula_with_context',
            'token_count': 418,
            'contains_formula': True,
            'contains_table': False,
            'upload_method': 'Processed JSON Import',
            'user_id': '40in',
            'stored_file_path': './data/rag_uploaded_files/b741aabd-d069-4b7c-94fa-b5f684158dcd/GOST_R_52633.3-2011.json',
            'file_id': 'b741aabd-d069-4b7c-94fa-b5f684158dcd',
            'testing_scenario': 'medium_db',
            'formula_id': '2',
            'overlap_source': 'chunk_10_end',
            'overlap_tokens': 30,
            '_id': '4f931fd5-9aa0-4b25-b377-d29a4df4a151',
            '_collection_name': 'documents'
        },
        'score': 0.8336984377511674
    }
    
    # Test with a typical search result structure (from the logs)
    search_result = {
        "title": "ГОСТ Р 52633.1-2009 Защита информации...",
        "url": "http://docs.cntd.ru/document/1200079555",
        "summary": "Requirements for small biometric image databases...",
        "original_description": "Необходимые для ... баз легко осуществимо...",
        "relevance_score": 0.9869208057773704,
        "source": "docs.cntd.ru"  # This should be set by the processing pipeline
    }
    
    print("Testing RAG document structure:")
    print(f"  Original source in metadata: {rag_document['metadata']['source']}")
    print(f"  Has 'source' field at top level: {'source' in rag_document}")
    
    # Simulate the source extraction logic from augment_context_node
    source = "Unknown source"
    
    # 1. First, try to get source from the main document field
    if rag_document.get("source") and rag_document["source"].strip() != "":
        source = rag_document["source"]
        print(f"  ✓ Found source in main document field: {source}")
    # 2. Then try from metadata fields
    elif rag_document.get("metadata"):
        metadata = rag_document["metadata"]
        print(f"  - Checking metadata fields...")
        # Check various possible source fields in metadata
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                source = metadata[field_name]
                print(f"    ✓ Found source in metadata['{field_name}']: {source}")
                break
        # If still unknown and there's a source in metadata with specific naming convention
        if source == "Unknown source" and metadata.get("source"):
            source = metadata["source"]
            print(f"    ✓ Found source in metadata['source'] (fallback): {source}")
    # 3. If it's a processed search result, try to extract source from URL or title
    elif rag_document.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(rag_document["url"])
        if parsed_url.netloc:
            source = parsed_url.netloc
            print(f"  ✓ Found source from URL netloc: {source}")
        else:
            source = rag_document["url"][:50] + "..."  # Use first 50 chars of URL as source
            print(f"  ✓ Found source from URL: {source}")
    # 4. If it's a processed search result with title
    elif rag_document.get("title"):
        source = rag_document["title"]
        print(f"  ✓ Found source from title: {source}")
    
    print(f"  Final source determination: {source}")
    
    print(f"\nTesting search result structure:")
    print(f"  Original search result source: {search_result.get('source', 'NOT FOUND')}")
    print(f"  Has 'source' field at top level: {'source' in search_result}")
    
    # Simulate the source extraction logic for search result
    source2 = "Unknown source"
    
    # 1. First, try to get source from the main document field
    if search_result.get("source") and search_result["source"].strip() != "":
        source2 = search_result["source"]
        print(f"  ✓ Found source in main document field: {source2}")
    # 2. Then try from metadata fields
    elif search_result.get("metadata"):
        metadata = search_result["metadata"]
        print(f"  - Checking metadata fields...")
        # Check various possible source fields in metadata
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                source2 = metadata[field_name]
                print(f"    ✓ Found source in metadata['{field_name}']: {source2}")
                break
        # If still unknown and there's a source in metadata with specific naming convention
        if source2 == "Unknown source" and metadata.get("source"):
            source2 = metadata["source"]
            print(f"    ✓ Found source in metadata['source'] (fallback): {source2}")
    # 3. If it's a processed search result, try to extract source from URL or title
    elif search_result.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(search_result["url"])
        if parsed_url.netloc:
            source2 = parsed_url.netloc
            print(f"  ✓ Found source from URL netloc: {source2}")
        else:
            source2 = search_result["url"][:50] + "..."  # Use first 50 chars of URL as source
            print(f"  ✓ Found source from URL: {source2}")
    # 4. If it's a processed search result with title
    elif search_result.get("title"):
        source2 = search_result["title"]
        print(f"  ✓ Found source from title: {source2}")
    else:
        print(f"  ✗ No source found for search result")
    
    print(f"  Final source determination: {source2}")
    
    # Now test with the normalization function
    print(f"\nTesting with normalization function:")
    
    normalized_rag = normalize_mcp_result(rag_document, "rag")
    print(f"  Normalized RAG document source: {normalized_rag.get('source', 'NOT FOUND')}")
    
    normalized_search = normalize_mcp_result(search_result, "search")
    print(f"  Normalized search result source: {normalized_search.get('source', 'NOT FOUND')}")
    
    # Test the augment_context_node source extraction logic on normalized documents
    print(f"\nTesting augment_context_node source extraction on normalized documents:")
    
    # Test on normalized RAG document
    source_norm_rag = "Unknown source"
    doc = normalized_rag
    if doc.get("source") and doc["source"].strip() != "":
        source_norm_rag = doc["source"]
    elif doc.get("metadata"):
        metadata = doc["metadata"]
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                source_norm_rag = metadata[field_name]
                break
        if source_norm_rag == "Unknown source" and metadata.get("source"):
            source_norm_rag = metadata["source"]
    elif doc.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(doc["url"])
        if parsed_url.netloc:
            source_norm_rag = parsed_url.netloc
        else:
            source_norm_rag = doc["url"][:50] + "..."
    elif doc.get("title"):
        source_norm_rag = doc["title"]
    
    print(f"  RAG document source extraction result: {source_norm_rag}")
    
    # Test on normalized search document
    source_norm_search = "Unknown source"
    doc = normalized_search
    if doc.get("source") and doc["source"].strip() != "":
        source_norm_search = doc["source"]
    elif doc.get("metadata"):
        metadata = doc["metadata"]
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                source_norm_search = metadata[field_name]
                break
        if source_norm_search == "Unknown source" and metadata.get("source"):
            source_norm_search = metadata["source"]
    elif doc.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(doc["url"])
        if parsed_url.netloc:
            source_norm_search = parsed_url.netloc
        else:
            source_norm_search = doc["url"][:50] + "..."
    elif doc.get("title"):
        source_norm_search = doc["title"]
    
    print(f"  Search document source extraction result: {source_norm_search}")
    
    print(f"\n{'='*60}")
    print(f"🔍 ANALYSIS:")
    print(f"  - RAG document source properly extracted: {source_norm_rag != 'Unknown source'}")
    print(f"  - Search document source properly extracted: {source_norm_search != 'Unknown source'}")
    print(f"  - Both sources meaningful: {source_norm_rag != 'Unknown source' and source_norm_search != 'Unknown source'}")
    
    if source_norm_rag != 'Unknown source' and source_norm_search != 'Unknown source':
        print(f"\n✅ SUCCESS: Source extraction logic is working correctly!")
        return True
    else:
        print(f"\n❌ ISSUE: Source extraction logic is not working properly")
        return False


if __name__ == "__main__":
    success = debug_document_structure()
    sys.exit(0 if success else 1)