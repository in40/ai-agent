#!/usr/bin/env python3
"""
Simple test to verify that source information is properly preserved in documents.
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

from langgraph_agent.langgraph_agent import augment_context_node, AgentState


def test_source_extraction():
    """Test that source information is properly extracted from documents."""
    print("Testing source extraction from documents...")
    
    # Create a test document similar to what we saw in the logs
    test_document = {
        "content": "Размножение осуществляют до момента, пока размер базы синтетических образов-потомков второго поколения не совпадет с размерами исходной базы естественных биометрических образов исходного (нулевого) поколения.",
        "metadata": {
            "source": "GOST_R_52633.3-2011",
            "chunk_id": 11,
            "section": "6.2.6_6.2.7",
            "title": "Medium DB Testing: Generation Forecasting and Formula (2) (with overlap)",
            "chunk_type": "formula_with_context",
            "token_count": 418,
            "contains_formula": True,
            "contains_table": False,
            "upload_method": "Processed JSON Import",
            "user_id": "40in",
            "stored_file_path": "./data/rag_uploaded_files/b741aabd-d069-4b7c-94fa-b5f684158dcd/GOST_R_52633.3-2011.json",
            "file_id": "b741aabd-d069-4b7c-94fa-b5f684158dcd",
            "testing_scenario": "medium_db",
            "formula_id": "2",
            "_id": "4f931fd5-9aa0-4b25-b377-d29a4df4a151",
            "_collection_name": "documents"
        },
        "score": 0.8336984377511674
    }
    
    # Create a state with this document
    state = AgentState(
        user_request="Test request",
        rag_documents=[test_document],
        mcp_queries=[],
        mcp_results=[],
        synthesized_result="",
        can_answer=False,
        iteration_count=0,
        max_iterations=3,
        final_answer="",
        error_message=None,
        mcp_servers=[],
        refined_queries=[],
        failure_reason=None,
        # Fields retained for compatibility
        schema_dump={},
        sql_query="",
        db_results=[],
        all_db_results={},
        table_to_db_mapping={},
        table_to_real_db_mapping={},
        response_prompt="",
        messages=[],
        validation_error=None,
        retry_count=0,
        execution_error=None,
        sql_generation_error=None,
        disable_sql_blocking=False,
        disable_databases=False,
        query_type="initial",
        database_name="",
        previous_sql_queries=[],
        registry_url=None,
        discovered_services=[],
        mcp_service_results=[],
        use_mcp_results=False,
        mcp_tool_calls=[],
        mcp_capable_response="",
        return_mcp_results_to_llm=False,
        is_final_answer=False,
        rag_context="",
        use_rag_flag=False,
        rag_relevance_score=0.0,
        rag_query="",
        rag_response=""
    )
    
    # Call the augment_context_node function
    result_state = augment_context_node(state)
    
    # Check if the source was properly extracted
    rag_context = result_state.get("rag_context", "")
    print(f"Generated context:\n{rag_context}")
    
    # Check if the source appears in the context
    has_correct_source = "GOST_R_52633.3-2011" in rag_context
    has_unknown_source = "Unknown source" in rag_context
    
    print(f"\nCorrect source (GOST_R_52633.3-2011) found: {has_correct_source}")
    print(f"Unknown source found: {has_unknown_source}")
    
    if has_correct_source and not has_unknown_source:
        print("\n✅ SUCCESS: Source information is properly extracted from metadata!")
        return True
    elif has_unknown_source:
        print("\n❌ FAILURE: Source information is still showing as 'Unknown source'")
        return False
    else:
        print("\n⚠️  PARTIAL: Correct source not found but 'Unknown source' not present either")
        return False


if __name__ == "__main__":
    success = test_source_extraction()
    if success:
        print("\n🎉 Source extraction test passed!")
    else:
        print("\n💥 Source extraction test failed!")
    sys.exit(0 if success else 1)