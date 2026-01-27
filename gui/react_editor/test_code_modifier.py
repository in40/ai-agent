"""
Test script to verify the code modifier functionality
"""
import tempfile
import os
from pathlib import Path
from code_modifier import CodeModifier


def create_test_langgraph_file():
    """Create a minimal test LangGraph file to test the modifier"""
    test_code = '''"""
Test LangGraph implementation for testing purposes
"""

from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    """
    State definition for the test agent.
    """
    user_request: str
    messages: List[Any]


def start_node(state: AgentState) -> AgentState:
    """
    Starting node for the workflow.
    """
    return state


def process_node(state: AgentState) -> AgentState:
    """
    Processing node for the workflow.
    """
    return state


def create_test_graph():
    """
    Create the test workflow using LangGraph
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("start_node", start_node)
    workflow.add_node("process_node", process_node)

    # Define edges
    workflow.add_edge("start_node", "process_node")

    # Set entry point
    workflow.set_entry_point("start_node")

    return workflow.compile()
'''
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    temp_file.write(test_code)
    temp_file.flush()
    return temp_file.name


def test_code_modifier():
    """Test the code modifier functionality"""
    print("Testing CodeModifier functionality...")
    
    # Create a test LangGraph file
    test_file_path = create_test_langgraph_file()
    
    # Print original content
    print("\\nOriginal file content:")
    with open(test_file_path, 'r') as f:
        original_content = f.read()
        print(original_content)
    
    # Create a test workflow configuration
    test_workflow = {
        "name": "TestWorkflow",
        "nodes": [
            {
                "id": "start_node",
                "data": {
                    "label": "Start Node",
                    "description": "Starting point of the workflow",
                    "nodeFunction": "start_node",
                    "logic": "Initialize workflow state",
                    "stateUpdates": {
                        "user_request": "state['user_request']",
                        "step_count": "0"
                    }
                }
            },
            {
                "id": "process_node",
                "data": {
                    "label": "Process Node",
                    "description": "Processes the input",
                    "nodeFunction": "process_node",
                    "logic": "Process the input data",
                    "stateUpdates": {
                        "processed_data": "process(input_data)",
                        "status": "'completed'"
                    },
                    "conditionalEdges": [
                        {
                            "condition": "data_valid",
                            "target": "output_node"
                        }
                    ]
                }
            },
            {
                "id": "new_node",
                "data": {
                    "label": "New Node",
                    "description": "A newly added node",
                    "nodeFunction": "new_node",
                    "logic": "Perform new operation",
                    "stateUpdates": {
                        "new_field": "'new_value'"
                    }
                }
            }
        ],
        "edges": [
            {
                "source": "start_node",
                "target": "process_node"
            },
            {
                "source": "process_node",
                "target": "new_node"
            }
        ]
    }
    
    # Create the code modifier and apply changes
    modifier = CodeModifier(test_file_path)
    result = modifier.apply_changes(test_workflow)
    
    print(f"\\nResult of applying changes: {result}")
    
    # Print modified content
    print("\\nModified file content:")
    with open(test_file_path, 'r') as f:
        modified_content = f.read()
        print(modified_content)
    
    # Clean up
    os.unlink(test_file_path)
    
    print("\\n✅ CodeModifier test completed")
    return result


if __name__ == "__main__":
    test_code_modifier()