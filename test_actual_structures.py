#!/usr/bin/env python3
"""
Test to check the actual structure of search results and verify source extraction
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


def test_actual_search_structure():
    """Test with the actual structure of search results from the logs."""
    print("Testing with actual search result structure from logs...")
    
    # This is the structure from the logs - the actual response from the search service
    actual_search_result = {
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
                        "title": "ГОСТ Р 52633.1-2009 Защита информации. Техника защиты информации. Требования к формированию баз естественных биометрических образов, предназначенных для тестирования средств высоконадежной биометрической аутентификации, ГОСТ Р от 15 декабря 2009 года №52633.1-2009",
                        "url": "http://docs.cntd.ru/document/1200079555",
                        "description": "Необходимые для ... баз легко осуществимо, а для образов \"Чужой\" велики (1012 образов и больше)....",
                        "date": "", 
                        "language": "ru",
                        "thumbnail": ""
                    },
                    {
                        "title": "Быстрая оценка энтропии длинных кодов с зависимыми разрядами...",
                        "url": "https://cyberleninka.ru/article/n/bystraya-otsenka-entropii-dlinnyh-kodov-s-zavisimymi-razryadami-na-mikrokontrollerah-s-malym-potrebleniem-i-nizkoy-razryadnostyu-obzor",
                        "description": "По рекомендациям этого стандарта требуется применение малых тестовых баз образов «Чужой» объемом от 21 до 64 примеров.",
                        "date": "",
                        "language": "ru", 
                        "thumbnail": "https://imgs.search.brave.com/Y-71_YB2wMZ-M83DK0xXQV5edlMdx6zsUUJ-c1-P62I/rs:fit:200:200:1:0/g:ce/aHR0cHM6Ly9jeWJl/cmxlbmlua2EucnUv/YXJ0aWNsZS9uL2J5/c3RyYXlhLW90c2Vu/a2EtZW50cm9waWkt/ZGxpbm55aC1rb2Rv/di1zLXphdmlzaW15/bWktcmF6cnlhZGFt/aS1uYS1taWtyb2tv/bnRyb2xsZXJhaC1z/LW1hbHltLXBvdHJl/YmxlbmllbS1pLW5p/emtveS1yYXpyeWFk/bm9zdHl1LW9iem9y/L2NvdmVy"
                    }
                ],
                "error": None
            }
        },
        "timestamp": "2026-01-31T06:52:30.703403Z"
    }
    
    # Normalize the actual search result
    normalized_search = normalize_mcp_result(actual_search_result, "search")
    
    print(f"Original service_id: {actual_search_result['service_id']}")
    print(f"Number of search results in nested structure: {len(actual_search_result['result']['result']['results'])}")
    print(f"First result URL: {actual_search_result['result']['result']['results'][0]['url']}")
    print(f"First result title: {actual_search_result['result']['result']['results'][0]['title'][:50]}...")
    print(f"Normalized search source: {normalized_search['source']}")
    print(f"Normalized search source type: {normalized_search['source_type']}")
    print(f"Normalized content preview: {normalized_search['content'][:100]}...")
    
    # Check if the source extraction worked properly
    source_contains_domain = "docs.cntd.ru" in normalized_search['source'] or "cyberleninka.ru" in normalized_search['source']
    source_not_generic = normalized_search['source'] not in ["Web Search", "search-server-127-0-0-1-8090"]  # Should not be just the service ID
    
    print(f"\nSource contains domain from results: {source_contains_domain}")
    print(f"Source is not generic service ID: {source_not_generic}")
    
    if source_contains_domain and source_not_generic:
        print("\n✅ SUCCESS: Actual search result structure properly extracts meaningful source information!")
        return True
    else:
        print("\n❌ FAILURE: Actual search result structure does not extract meaningful source information")
        return False


def test_rag_document_structure():
    """Test with the actual structure of RAG documents from the logs."""
    print("\nTesting with actual RAG document structure from logs...")
    
    # This is the structure from the logs - the actual response from the RAG service
    actual_rag_document = {
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
            '_id': '4f931fd5-9aa0-4b25-b377-d29a4df4a151',
            '_collection_name': 'documents'
        },
        'score': 0.8336984377511674,
        'source': 'RAG Document'  # This is from the original structure in logs
    }
    
    # Normalize the actual RAG document
    normalized_rag = normalize_mcp_result(actual_rag_document, "rag")
    
    print(f"Original metadata source: {actual_rag_document['metadata']['source']}")
    print(f"Original document source: {actual_rag_document.get('source', 'Not present')}")
    print(f"Normalized RAG source: {normalized_rag['source']}")
    print(f"Normalized RAG source type: {normalized_rag['source_type']}")
    print(f"Normalized content preview: {normalized_rag['content'][:100]}...")
    
    # Check if the source extraction worked properly
    source_preserved = normalized_rag['source'] == 'GOST_R_52633.3-2011'
    
    print(f"\nSource properly preserved from metadata: {source_preserved}")
    
    if source_preserved:
        print("\n✅ SUCCESS: RAG document structure properly preserves source information!")
        return True
    else:
        print("\n❌ FAILURE: RAG document structure does not preserve source information properly")
        return False


if __name__ == "__main__":
    print("🔍 Testing Actual Result Structures from Logs")
    print("="*60)
    
    test1_success = test_actual_search_structure()
    test2_success = test_rag_document_structure()
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS:")
    print(f"  Search result structure test:  {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"  RAG document structure test:   {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    overall_success = test1_success and test2_success
    
    if overall_success:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"   Source information is properly preserved in both search and RAG results")
    else:
        print(f"\n💥 SOME TESTS FAILED!")
        print(f"   Source information preservation still needs attention")
    
    sys.exit(0 if overall_success else 1)