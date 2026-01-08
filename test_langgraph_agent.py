"""
Test script for the LangGraph agent implementation
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent import create_enhanced_agent_graph, AgentState


def test_langgraph_agent():
    """
    Test the LangGraph agent with a sample request
    """
    # Create the graph
    graph = create_enhanced_agent_graph()
    
    # Define initial state
    initial_state: AgentState = {
        "user_request": "Get all users from the database",
        "schema_dump": {},
        "sql_query": "",
        "db_results": [],
        "final_response": "",
        "messages": [],
        "validation_error": None,
        "retry_count": 0
    }
    
    # Run the graph
    result = graph.invoke(initial_state)
    
    print("Final state:", result)
    print("Final response:", result.get("final_response"))
    

if __name__ == "__main__":
    test_langgraph_agent()