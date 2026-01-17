import streamlit as st
import json
import tempfile
import os
from pathlib import Path

# Add the project root to the Python path
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState, run_enhanced_agent
from langgraph.graph import StateGraph

def test_visualization():
    """Test the visualization capabilities"""
    print("Testing visualization...")
    
    # Create the graph
    graph = create_enhanced_agent_graph()
    g = graph.get_graph()
    
    # Test different visualization methods
    try:
        ascii_graph = g.draw_ascii()
        print("✓ ASCII visualization works")
    except Exception as e:
        print(f"✗ ASCII visualization failed: {e}")
    
    try:
        mermaid_code = g.draw_mermaid()
        print("✓ Mermaid visualization works")
    except Exception as e:
        print(f"✗ Mermaid visualization failed: {e}")
    
    try:
        # Test getting nodes and edges
        nodes = list(g.nodes.keys())
        edges = list(g.edges)
        
        print(f"✓ Graph structure accessible: {len(nodes)} nodes, {len(edges)} edges")
        print(f"  Nodes: {list(nodes)[:5]}{'...' if len(nodes) > 5 else ''}")
    except Exception as e:
        print(f"✗ Graph structure access failed: {e}")

def test_workflow_execution():
    """Test the workflow execution"""
    print("\nTesting workflow execution...")
    
    try:
        # Run a simple test query
        result = run_enhanced_agent("What is your name?", disable_databases=True)
        
        print("✓ Workflow execution works")
        print(f"  Request: {result['original_request']}")
        print(f"  Response: {result['final_response'][:100]}...")
    except Exception as e:
        print(f"✗ Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()

def test_streamlit_components():
    """Test if Streamlit components work properly"""
    print("\nTesting Streamlit components...")
    
    try:
        # Just test if we can import and use basic Streamlit functions
        st.write("Test")
        print("✓ Streamlit basic components work")
    except Exception as e:
        print(f"✗ Streamlit components failed: {e}")

if __name__ == "__main__":
    print("Running GUI functionality tests...\n")
    
    test_visualization()
    test_workflow_execution()
    test_streamlit_components()
    
    print("\nTests completed!")