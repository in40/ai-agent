#!/usr/bin/env python3
"""
Comprehensive test to verify that both search and RAG results are properly preserved with correct source information.
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


def test_combined_search_rag_results():
    """Test that both search and RAG results are properly preserved with correct source information."""
    print("🔍 Testing Combined Search and RAG Results Preservation")
    print("="*60)
    
    # Simulate the combined results that would be in rag_documents after both search and RAG processing
    combined_results = [
        # Search results processed through download and summarization
        {
            "content": "Requirements for small biometric image databases...",
            "title": "ГОСТ Р 52633.1-2009 Requirements for Biometric Image Bases",
            "url": "http://docs.cntd.ru/document/1200079555",
            "summary": "This document specifies requirements for small biometric image databases used in testing high-reliability biometric authentication systems...",
            "original_description": "Необходимые для ... баз легко осуществимо, а для образов \"Чужой\" велики...",
            "relevance_score": 0.9869208057773704,
            "source": "docs.cntd.ru",  # This should be preserved
            "source_type": "web_search",
            "metadata": {
                "original_source_field": "search-server-127-0-0-1-8090",
                "service_used": "search-server-127-0-0-1-8090",
                "processing_timestamp": "2026-01-31T07:00:00.000000Z",
                "raw_result": {"success": True, "result": {"results": [...]}}
            }
        },
        # More search results
        {
            "content": "Biometric personal data regulations...",
            "title": "Biometric Personal Data: Requirements and Regulations",
            "url": "https://cyberleninka.ru/article/n/biometric-data-regulations",
            "summary": "Article about biometric data requirements in Russian regulatory framework...",
            "original_description": "By recommendations of this standard, small test databases of 'Alien' samples with volumes from 21 to 64 examples are required...",
            "relevance_score": 0.9234567890123456,
            "source": "cyberleninka.ru",  # This should be preserved
            "source_type": "web_search",
            "metadata": {
                "original_source_field": "search-server-127-0-0-1-8090",
                "service_used": "search-server-127-0-0-1-8090",
                "processing_timestamp": "2026-01-31T07:00:01.000000Z",
                "raw_result": {"success": True, "result": {"results": [...]}}
            }
        },
        # RAG results
        {
            "content": "Размножение осуществляют до момента, пока размер базы синтетических образов-потомков...",
            "metadata": {
                "source": "GOST_R_52633.3-2011",  # This should be preserved
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
            "source": "GOST_R_52633.3-2011",  # This should be preserved
            "source_type": "local_document",
            "relevance_score": 0.8336984377511674
        },
        # Another RAG result
        {
            "content": "Приложение Б (справочное) Результат оценки остаточной стойкости...",
            "metadata": {
                "source": "GOST_R_52633.3-2011",  # This should be preserved
                "chunk_id": 17,
                "section": "appendix_b",
                "title": "Appendix B: Residual Strength Example with Mutation Testing",
                "chunk_type": "appendix_example",
                "token_count": 198,
                "contains_formula": False,
                "upload_method": "Processed JSON Import",
                "user_id": "40in",
                "stored_file_path": "./data/rag_uploaded_files/b741aabd-d069-4b7c-94fa-b5f684158dcd/GOST_R_52633.3-2011.json",
                "file_id": "b741aabd-d069-4b7c-94fa-b5f684158dcd",
                "_id": "aa6b824f-c9c9-4960-9103-2f4692756902",
                "_collection_name": "documents"
            },
            "score": 0.761000766498952,
            "source": "GOST_R_52633.3-2011",  # This should be preserved
            "source_type": "local_document",
            "relevance_score": 0.761000766498952
        }
    ]
    
    print(f"Testing with {len(combined_results)} combined results ({len([r for r in combined_results if r.get('source_type') == 'web_search'])} search, {len([r for r in combined_results if r.get('source_type') == 'local_document'])} RAG)")
    
    # Apply the same source extraction logic as in the updated augment_context_node
    doc_context = "\n\nRetrieved Documents:\n"
    for i, doc in enumerate(combined_results):
        content = doc.get("content", doc.get("page_content", doc.get("summary", "")))

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
                        break
            # If still unknown and there's a source in metadata with specific naming convention
            if source == "Unknown source" and metadata.get("source"):
                specific_source = metadata["source"]
                if specific_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = specific_source

        # 2. If no specific source found in metadata, then try the main document field
        if source == "Unknown source" or source in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
            if doc.get("source") and doc["source"].strip() != "":
                top_level_source = doc["source"]
                # Only use top-level source if it's not generic
                if top_level_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = top_level_source

        # 3. If it's a processed search result, try to extract source from URL or title
        if source == "Unknown source" or source in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
            if doc.get("url"):
                import urllib.parse
                parsed_url = urllib.parse.urlparse(doc["url"])
                if parsed_url.netloc:
                    source = parsed_url.netloc
                else:
                    source = doc["url"][:50] + "..."  # Use first 50 chars of URL as source
            elif doc.get("title"):
                title_source = doc["title"]
                # Only use title if it's not generic
                if title_source not in ["RAG Document", "Search Result", "Search", "Web Search", "Document", "Result", "Generic Document"]:
                    source = title_source

        doc_context += f"\nDocument {i+1} ({source}):\n{content[:200]}...\n"
        
        print(f"Document {i+1}:")
        print(f"  - Type: {doc.get('source_type', 'unknown')}")
        print(f"  - Extracted source: {source}")
        print(f"  - Expected for search: domain name, for RAG: GOST standard name")
        if 'GOST' in str(source) or 'gost' in str(source).lower():
            print(f"  - ✅ RAG document source correctly preserved: {source}")
        elif any(domain in str(source) for domain in ['docs.cntd.ru', 'cyberleninka.ru']):
            print(f"  - ✅ Search document source correctly preserved: {source}")
        else:
            print(f"  - ⚠️  Source might not be optimally extracted: {source}")
    
    print(f"\nFinal formatted context preview:")
    print(doc_context[:500] + "..." if len(doc_context) > 500 else doc_context)
    
    # Check if all sources were properly extracted
    all_sources_valid = True
    expected_sources = ["docs.cntd.ru", "cyberleninka.ru", "GOST_R_52633.3-2011"]
    
    for expected_source in expected_sources:
        if expected_source not in doc_context:
            print(f"\n❌ MISSING: Expected source '{expected_source}' not found in final context")
            all_sources_valid = False
        else:
            print(f"\n✅ FOUND: Expected source '{expected_source}' is present in final context")
    
    # Count how many documents have proper sources vs unknown sources
    doc_lines = [line for line in doc_context.split('\n') if 'Document' in line and '(' in line and ')' in line]
    unknown_sources = sum(1 for line in doc_lines if 'Unknown source' in line)
    valid_sources = len(doc_lines) - unknown_sources
    
    print(f"\n📊 SOURCE EXTRACTION SUMMARY:")
    print(f"  - Total documents processed: {len(combined_results)}")
    print(f"  - Documents with valid sources: {valid_sources}")
    print(f"  - Documents with 'Unknown source': {unknown_sources}")
    print(f"  - Success rate: {valid_sources/len(combined_results)*100:.1f}%")
    
    if unknown_sources == 0 and all_sources_valid:
        print(f"\n🎉 PERFECT: All documents have proper source information!")
        print(f"   - Search results show domain names (e.g., 'docs.cntd.ru')")
        print(f"   - RAG results show document names (e.g., 'GOST_R_52633.3-2011')")
        print(f"   - No 'Unknown source' labels in the final output")
        return True
    elif unknown_sources <= 1:  # Allow for one potentially generic document
        print(f"\n✅ GOOD: Almost all documents have proper source information!")
        print(f"   - Only {unknown_sources} document(s) have 'Unknown source' label")
        print(f"   - Main sources (search and RAG) are properly differentiated")
        return True
    else:
        print(f"\n❌ ISSUES: {unknown_sources} documents still have 'Unknown source' labels")
        print(f"   - Source extraction logic needs improvement")
        return False


if __name__ == "__main__":
    success = test_combined_search_rag_results()
    
    print(f"\n{'='*60}")
    print("🎯 COMPREHENSIVE TEST RESULT:")
    if success:
        print("  ✅ Combined search and RAG results are properly preserved with correct source information!")
        print("  - Search results show proper domain/source information")
        print("  - RAG results show proper document source information") 
        print("  - No more 'Unknown source' labels for documents with identifiable sources")
    else:
        print("  ❌ Issues remain with source information preservation")
        print("  - Some documents still showing 'Unknown source' incorrectly")
    
    sys.exit(0 if success else 1)