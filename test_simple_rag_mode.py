#!/usr/bin/env python3
"""
Simple test to verify the RAG MCP mode fix works correctly.
"""

import os
import sys
import importlib

# Clear any cached modules to ensure fresh imports
modules_to_clear = [k for k in sys.modules.keys() if k.startswith(('rag_component', 'langgraph_agent', 'config'))]
for module in modules_to_clear:
    del sys.modules[module]

def test_mcp_mode():
    """Test RAG MCP mode functionality"""
    print("Testing RAG MCP mode functionality...")
    
    # Set environment for MCP mode
    os.environ['RAG_ENABLED'] = 'true'
    os.environ['RAG_MODE'] = 'mcp'
    
    # Import after setting environment
    from langgraph_agent.langgraph_agent import check_rag_applicability_node
    
    # Test 1: No RAG MCP services available
    state_no_rag = {
        "user_request": "What is the weather today?",
        "discovered_services": [{"id": "sql-service", "type": "sql"}],  # No RAG service
        "rag_query": ""
    }
    
    result = check_rag_applicability_node(state_no_rag)
    print(f"No RAG services - use_rag_flag: {result['use_rag_flag']}")
    assert result["use_rag_flag"] is False, "Should not use RAG when no RAG MCP services are available in MCP mode"
    print("✓ Test 1 passed: RAG not used when no RAG MCP services are available in MCP mode")
    
    # Test 2: RAG MCP services available
    state_with_rag = {
        "user_request": "What is the weather today?",
        "discovered_services": [
            {"id": "rag-service", "type": "rag", "host": "localhost", "port": 8091},
            {"id": "sql-service", "type": "sql"}
        ],
        "rag_query": ""
    }
    
    result = check_rag_applicability_node(state_with_rag)
    print(f"With RAG services - use_rag_flag: {result['use_rag_flag']}")
    assert result["use_rag_flag"] is True, "Should use RAG when RAG MCP services are available in MCP mode"
    print("✓ Test 2 passed: RAG used when RAG MCP services are available in MCP mode")
    
    # Clean up
    os.environ.pop('RAG_ENABLED', None)
    os.environ.pop('RAG_MODE', None)


def test_local_mode():
    """Test RAG local mode functionality"""
    print("\nTesting RAG local mode functionality...")
    
    # Clear modules to ensure fresh import with new environment
    modules_to_clear = [k for k in sys.modules.keys() if k.startswith(('rag_component', 'langgraph_agent', 'config'))]
    for module in modules_to_clear:
        del sys.modules[module]
    
    # Set environment for local mode
    os.environ['RAG_ENABLED'] = 'true'
    os.environ['RAG_MODE'] = 'local'
    
    # Import after setting environment
    from langgraph_agent.langgraph_agent import check_rag_applicability_node
    
    # Test: Local mode should use RAG even without MCP services
    state_local = {
        "user_request": "Explain quantum computing concepts",
        "discovered_services": [{"id": "sql-service", "type": "sql"}],  # No RAG service
        "rag_query": ""
    }
    
    result = check_rag_applicability_node(state_local)
    print(f"Local mode - use_rag_flag: {result['use_rag_flag']}")
    assert result["use_rag_flag"] is True, "Should use RAG in local mode regardless of MCP services"
    print("✓ Test 3 passed: RAG used in local mode regardless of MCP services")
    
    # Clean up
    os.environ.pop('RAG_ENABLED', None)
    os.environ.pop('RAG_MODE', None)


if __name__ == "__main__":
    test_mcp_mode()
    test_local_mode()
    print("\n🎉 All tests passed! The RAG MCP mode fix is working correctly.")
    print("\nSummary of changes:")
    print("- Added RAG_MODE configuration option with values 'local', 'mcp', 'hybrid'")
    print("- Updated check_rag_applicability_node to respect RAG_MODE setting")
    print("- Updated retrieve_documents_node to use MCP services when RAG_MODE='mcp'")
    print("- When RAG_MODE='mcp' and no RAG MCP services are available, RAG is not used")
    print("- When RAG_MODE='mcp' and RAG MCP services are available, they are used")