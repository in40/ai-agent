#!/usr/bin/env python3
"""
Test script to verify that the knowledge is properly passed from generate_rag_response_node 
to generate_final_answer_node.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent.langgraph_agent import generate_final_answer_node


def test_knowledge_passing():
    """
    Test that the generate_final_answer_node correctly uses existing final answer.
    """
    print("Testing knowledge passing fix...")
    
    # Simulate the state that would come from generate_rag_response_node
    # with a pre-existing final answer
    test_state = {
        "synthesized_result": "Some synthesized result from MCP queries",
        "final_answer": "This is the RAG-generated response that should be preserved",
        "user_request": "What do we know about digital education?",
    }
    
    print(f"Initial state final_answer: '{test_state['final_answer']}'")
    print(f"Synthesized result: '{test_state['synthesized_result']}'")
    
    try:
        # Call the generate_final_answer_node function
        updated_state = generate_final_answer_node(test_state)
        
        print(f"After processing, final_answer: '{updated_state['final_answer']}'")
        
        # Check if the existing final answer was preserved
        if updated_state['final_answer'] == test_state['final_answer']:
            print("✅ SUCCESS: Existing final answer was preserved!")
            return True
        else:
            print(f"❌ FAILURE: Expected '{test_state['final_answer']}', but got '{updated_state['final_answer']}'")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_knowledge_passing()
    if success:
        print("\n🎉 Test passed! The knowledge passing fix is working correctly.")
    else:
        print("\n💥 Test failed! The fix needs more work.")
        sys.exit(1)