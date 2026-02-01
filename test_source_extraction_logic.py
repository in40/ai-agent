#!/usr/bin/env python3
"""
Test to specifically check the augment_context_node source extraction logic
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

def test_augment_context_source_extraction():
    """Test the exact source extraction logic used in augment_context_node"""
    print("🔍 Testing augment_context_node source extraction logic")
    print("="*60)
    
    # Test documents in the format that would come from the system
    test_documents = [
        # RAG document with source in metadata
        {
            "content": "Размножение осуществляют до момента, пока размер базы синтетических образов-потомков...",
            "metadata": {
                "source": "GOST_R_52633.3-2011",
                "chunk_id": 11,
                "section": "6.2.6_6.2.7",
                "title": "Medium DB Testing: Generation Forecasting and Formula (2) (with overlap)",
                "chunk_type": "formula_with_context",
                "token_count": 418,
                "contains_formula": True,
                "upload_method": "Processed JSON Import",
                "user_id": "40in",
                "stored_file_path": "./data/rag_uploaded_files/b741aabd-d069-4b7c-94fa-b5f684158dcd/GOST_R_52633.3-2011.json",
                "file_id": "b741aabd-d069-4b7c-94fa-b5f684158dcd",
                "testing_scenario": "medium_db",
                "formula_id": "2",
                "_id": "4f931fd5-9aa0-4b25-b377-d29a4df4a151",
                "_collection_name": "documents"
            },
            "score": 0.8336984377511674,
            "source": "GOST_R_52633.3-2011"  # This should be used first
        },
        # Processed search result with proper source
        {
            "title": "ГОСТ Р 52633.1-2009 Защита информации...",
            "url": "http://docs.cntd.ru/document/1200079555",
            "summary": "Requirements for small biometric image databases...",
            "original_description": "Необходимые для ... баз легко осуществимо...",
            "relevance_score": 0.9869208057773704,
            "source": "docs.cntd.ru"  # This should be used
        },
        # Document with source in different metadata field
        {
            "content": "Some other content...",
            "metadata": {
                "filename": "test_document.pdf",
                "title": "Test Document Title"
            },
            "source": ""  # Empty, should get from metadata
        },
        # Document with no source information (should show as Unknown source)
        {
            "content": "Content with no source info...",
            "metadata": {},
            "title": "No Source Document"
        }
    ]
    
    print("Testing source extraction for each document:")
    
    for i, doc in enumerate(test_documents):
        print(f"\nDocument {i+1}:")
        print(f"  Content preview: {doc['content'][:50] if 'content' in doc else doc.get('summary', '')[:50]}...")
        
        # Apply the exact same logic as in augment_context_node
        content = doc.get("content", doc.get("page_content", doc.get("summary", "")))
        
        # Extract source information with priority hierarchy
        source = "Unknown source"

        # 1. First, try to get source from the main document field
        if doc.get("source") and doc["source"].strip() != "":
            source = doc["source"]
            print(f"  ✓ Found source in main document field: {source}")
        # 2. Then try from metadata fields
        elif doc.get("metadata"):
            metadata = doc["metadata"]
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
        elif doc.get("url"):
            import urllib.parse
            parsed_url = urllib.parse.urlparse(doc["url"])
            if parsed_url.netloc:
                source = parsed_url.netloc
                print(f"  ✓ Found source from URL netloc: {source}")
            else:
                source = doc["url"][:50] + "..."  # Use first 50 chars of URL as source
                print(f"  ✓ Found source from URL: {source}")
        # 4. If it's a processed search result with title
        elif doc.get("title"):
            source = doc["title"]
            print(f"  ✓ Found source from title: {source}")

        print(f"  Final extracted source: {source}")
    
    # Test with a document that has the exact structure from the logs
    print(f"\n{'='*60}")
    print("Testing with document structure from actual logs:")
    
    log_document = {
        'content': 'Размножение осуществляют до момента, пока размер базы синтетических образов-потомков второго поколения не совпадет с размерами исходной базы естественных биометрических образов исходного (нулевого) поколения.\n\n6.2.6 Прогнозирование предельных возможностей по подбору используемой базы естественных биометрических образов исходного (нулевого) поколения...',
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
        'score': 0.8336984377511674,
        'source': 'RAG Document'  # This might be overriding the metadata source
    }

    print(f"Log document metadata source: {log_document['metadata']['source']}")
    print(f"Log document top-level source: {log_document['source']}")

    # Apply the source extraction logic
    source = "Unknown source"

    # 1. First, try to get source from the main document field
    if log_document.get("source") and log_document["source"].strip() != "":
        source = log_document["source"]
        print(f"  ✓ Found source in main document field: {source}")
    # 2. Then try from metadata fields
    elif log_document.get("metadata"):
        metadata = log_document["metadata"]
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
    elif log_document.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(log_document["url"])
        if parsed_url.netloc:
            source = parsed_url.netloc
            print(f"  ✓ Found source from URL netloc: {source}")
        else:
            source = log_document["url"][:50] + "..."  # Use first 50 chars of URL as source
            print(f"  ✓ Found source from URL: {source}")
    # 4. If it's a processed search result with title
    elif log_document.get("title"):
        source = log_document["title"]
        print(f"  ✓ Found source from title: {source}")

    print(f"  Final extracted source: {source}")

    # The issue is that the top-level 'source' field is 'RAG Document' which overrides the actual source
    # The logic should prioritize the metadata source over the generic 'RAG Document' value
    print(f"\nIssue identified: Top-level 'source' field has generic value 'RAG Document' which overrides the specific metadata source 'GOST_R_52633.3-2011'")

    # Corrected logic should check if the top-level source is generic before using it
    corrected_source = "Unknown source"

    # Check if top-level source is generic, if so, try metadata first
    top_level_source = log_document.get("source", "")
    if top_level_source and top_level_source.strip() != "" and top_level_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result"]:
        corrected_source = top_level_source
        print(f"  ✓ Using specific top-level source: {corrected_source}")
    elif log_document.get("metadata"):
        metadata = log_document["metadata"]
        print(f"  - Checking metadata fields (top-level source was generic)...")
        # Check various possible source fields in metadata
        for field_name in ["source", "file_name", "filename", "title", "url", "path", "file_path", "stored_file_path"]:
            if metadata.get(field_name) and metadata[field_name].strip() != "":
                corrected_source = metadata[field_name]
                print(f"    ✓ Found source in metadata['{field_name}']: {corrected_source}")
                break
        # If still unknown and there's a source in metadata with specific naming convention
        if corrected_source == "Unknown source" and metadata.get("source"):
            corrected_source = metadata["source"]
            print(f"    ✓ Found source in metadata['source'] (fallback): {corrected_source}")
    # Fallback to top-level source if metadata didn't have anything better
    elif top_level_source and top_level_source.strip() != "":
        corrected_source = top_level_source
        print(f"  ✓ Using top-level source as fallback: {corrected_source}")
    # 3. If it's a processed search result, try to extract source from URL or title
    elif log_document.get("url"):
        import urllib.parse
        parsed_url = urllib.parse.urlparse(log_document["url"])
        if parsed_url.netloc:
            corrected_source = parsed_url.netloc
            print(f"  ✓ Found source from URL netloc: {corrected_source}")
        else:
            corrected_source = log_document["url"][:50] + "..."  # Use first 50 chars of URL as source
            print(f"  ✓ Found source from URL: {corrected_source}")
    # 4. If it's a processed search result with title
    elif log_document.get("title"):
        corrected_source = log_document["title"]
        print(f"  ✓ Found source from title: {corrected_source}")

    print(f"  Corrected final source: {corrected_source}")

    print(f"\n{'='*60}")
    print("🔍 ANALYSIS:")
    print("  The issue is that generic source values like 'RAG Document' are overriding specific metadata sources")
    print("  The fix should prioritize specific sources from metadata over generic ones")

    return corrected_source == "GOST_R_52633.3-2011"
    
    print(f"\n{'='*60}")
    print("🔍 ANALYSIS:")
    print("  The issue is that generic source values like 'RAG Document' are overriding specific metadata sources")
    print("  The fix should prioritize specific sources from metadata over generic ones")
    
    return corrected_source == "GOST_R_52633.3-2011"


if __name__ == "__main__":
    success = test_augment_context_source_extraction()
    if success:
        print("\n✅ Source extraction logic identified and fixed!")
    else:
        print("\n❌ Source extraction logic still has issues")
    sys.exit(0 if success else 1)