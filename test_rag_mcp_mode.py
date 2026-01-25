#!/usr/bin/env python3
"""
Test script to verify that the RAG MCP mode fix works correctly.
"""

import os
import sys
from unittest.mock import Mock, patch
from langgraph_agent.langgraph_agent import check_rag_applicability_node, retrieve_documents_node, AgentState

def test_check_rag_applicability_with_mcp_mode():
    """Test that check_rag_applicability_node respects RAG_MODE=mcp"""
    
    # Save original environment variable
    original_rag_mode = os.environ.get('RAG_MODE')
    
    try:
        # Ensure RAG is enabled for the tests
        os.environ['RAG_ENABLED'] = 'true'
        # Set RAG mode to MCP
        os.environ['RAG_MODE'] = 'mcp'

        # Test case 1: No RAG MCP services discovered
        state_no_rag_services = {
            "user_request": "What is the weather today?",
            "discovered_services": [{"id": "sql-service", "type": "sql"}],  # No RAG service
            "rag_query": ""
        }

        result = check_rag_applicability_node(state_no_rag_services)
        assert result["use_rag_flag"] is False, f"Expected use_rag_flag to be False when no RAG MCP services are available, got {result['use_rag_flag']}"
        print("✓ Test 1 passed: RAG not used when no RAG MCP services are available in MCP mode")

        # Test case 2: RAG MCP services discovered
        state_with_rag_services = {
            "user_request": "What is the weather today?",
            "discovered_services": [
                {"id": "rag-service", "type": "rag", "host": "localhost", "port": 8091},
                {"id": "sql-service", "type": "sql"}
            ],
            "rag_query": ""
        }

        result = check_rag_applicability_node(state_with_rag_services)
        assert result["use_rag_flag"] is True, f"Expected use_rag_flag to be True when RAG MCP services are available, got {result['use_rag_flag']}"
        print("✓ Test 2 passed: RAG used when RAG MCP services are available in MCP mode")

        # Test case 3: Local mode should always use RAG if enabled and not SQL-related
        os.environ['RAG_ENABLED'] = 'true'
        os.environ['RAG_MODE'] = 'local'
        state_local_mode = {
            "user_request": "Explain quantum computing concepts",
            "discovered_services": [{"id": "sql-service", "type": "sql"}],  # No RAG service
            "rag_query": ""
        }
        
        result = check_rag_applicability_node(state_local_mode)
        assert result["use_rag_flag"] is True, f"Expected use_rag_flag to be True in local mode, got {result['use_rag_flag']}"
        print("✓ Test 3 passed: RAG used in local mode regardless of MCP services")
        
    finally:
        # Restore original environment variable
        if original_rag_mode is not None:
            os.environ['RAG_MODE'] = original_rag_mode
        else:
            os.environ.pop('RAG_MODE', None)
        # Also remove the RAG_ENABLED we set for testing
        os.environ.pop('RAG_ENABLED', None)


def test_retrieve_documents_node_with_mcp_mode():
    """Test that retrieve_documents_node respects RAG_MODE=mcp"""
    
    # Save original environment variable
    original_rag_mode = os.environ.get('RAG_MODE')
    
    try:
        # Ensure RAG is enabled for the tests
        os.environ['RAG_ENABLED'] = 'true'
        # Set RAG mode to MCP
        os.environ['RAG_MODE'] = 'mcp'
        
        # Mock the DedicatedMCPModel to simulate calling the RAG MCP service
        mock_mcp_model = Mock()
        mock_mcp_model._call_mcp_service.return_value = {
            "status": "success",
            "result": {
                "results": [
                    {"content": "Weather is sunny today", "metadata": {}, "score": 0.9}
                ]
            }
        }
        
        # Create a state with RAG MCP service
        state_with_rag_service = {
            "user_request": "What is the weather today?",
            "rag_query": "What is the weather today?",
            "discovered_services": [
                {"id": "rag-service", "type": "rag", "host": "localhost", "port": 8091, "metadata": {"protocol": "http"}}
            ],
            "rag_documents": [],
            "rag_relevance_score": 0.0
        }
        
        # Patch the DedicatedMCPModel import and instantiation
        with patch('langgraph_agent.langgraph_agent.DedicatedMCPModel') as mock_mcp_class:
            mock_mcp_instance = Mock()
            mock_mcp_instance._call_mcp_service.return_value = {
                "status": "success",
                "result": {
                    "results": [
                        {"content": "Weather is sunny today", "metadata": {}, "score": 0.9}
                    ]
                }
            }
            mock_mcp_class.return_value = mock_mcp_instance
            
            result = retrieve_documents_node(state_with_rag_service)
            
            # Verify that the MCP service was called
            mock_mcp_instance._call_mcp_service.assert_called_once()
            
            # Verify that documents were retrieved
            assert len(result["rag_documents"]) == 1
            assert result["rag_documents"][0]["content"] == "Weather is sunny today"
            print("✓ Test 4 passed: RAG MCP service called when RAG_MODE=mcp and service is available")
        
        # Test case: No RAG MCP services available in MCP mode
        state_no_rag_service = {
            "user_request": "What is the weather today?",
            "rag_query": "What is the weather today?",
            "discovered_services": [
                {"id": "sql-service", "type": "sql", "host": "localhost", "port": 8092}
            ],  # No RAG service
            "rag_documents": [],
            "rag_relevance_score": 0.0
        }
        
        result = retrieve_documents_node(state_no_rag_service)
        
        # Verify that no documents were retrieved when no RAG MCP service is available
        assert len(result["rag_documents"]) == 0
        assert result["rag_relevance_score"] == 0.0
        print("✓ Test 5 passed: No documents retrieved when no RAG MCP service is available in MCP mode")
        
    finally:
        # Restore original environment variable
        if original_rag_mode is not None:
            os.environ['RAG_MODE'] = original_rag_mode
        else:
            os.environ.pop('RAG_MODE', None)
        # Also remove the RAG_ENABLED we set for testing
        os.environ.pop('RAG_ENABLED', None)


if __name__ == "__main__":
    print("Testing RAG MCP mode fix...")
    
    test_check_rag_applicability_with_mcp_mode()
    test_retrieve_documents_node_with_mcp_mode()
    
    print("\n🎉 All tests passed! The RAG MCP mode fix is working correctly.")
    print("\nSummary of changes:")
    print("- Added RAG_MODE configuration option with values 'local', 'mcp', 'hybrid'")
    print("- Updated check_rag_applicability_node to respect RAG_MODE setting")
    print("- Updated retrieve_documents_node to use MCP services when RAG_MODE='mcp'")
    print("- When RAG_MODE='mcp' and no RAG MCP services are available, RAG is not used")
    print("- When RAG_MODE='mcp' and RAG MCP services are available, they are used")