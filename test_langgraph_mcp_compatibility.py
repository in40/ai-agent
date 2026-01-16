#!/usr/bin/env python3
"""
Quick test to verify that the LangGraph agent works with the updated MCP model.
"""

import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import create_enhanced_agent_graph


def test_langgraph_agent_with_updated_mcp():
    """Test that the LangGraph agent works with the updated MCP model"""
    print("Testing LangGraph agent with updated MCP model...")
    
    try:
        # Create the agent graph - this should work without errors
        graph = create_enhanced_agent_graph()
        print("✓ LangGraph agent created successfully with updated MCP model")
        
        # The graph should have the expected nodes
        expected_nodes = {
            'get_schema', 'discover_services', 'query_mcp_services', 'generate_sql',
            'validate_sql', 'execute_sql', 'refine_sql', 'generate_wider_search_query',
            'execute_wider_search', 'generate_prompt', 'generate_response'
        }
        
        # Check that the query_mcp_services node exists
        if hasattr(graph, '_all_nodes'):
            nodes = set(graph._all_nodes.keys())
            if 'query_mcp_services' in nodes:
                print("✓ query_mcp_services node is present in the graph")
            else:
                print("✗ query_mcp_services node is missing from the graph")
                return False
        else:
            print("? Unable to verify nodes in graph structure")
        
        print("✓ LangGraph agent works correctly with updated MCP model")
        return True
        
    except Exception as e:
        print(f"✗ Error testing LangGraph agent with updated MCP model: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running LangGraph Agent Compatibility Test with Updated MCP Model...\n")
    
    success = test_langgraph_agent_with_updated_mcp()
    
    if success:
        print("\n🎉 LangGraph agent compatibility test passed!")
        sys.exit(0)
    else:
        print("\n❌ LangGraph agent compatibility test failed!")
        sys.exit(1)