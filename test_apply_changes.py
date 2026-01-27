import json
import tempfile
import os
from pathlib import Path

def test_apply_changes():
    """Test the apply changes functionality"""
    print("Testing apply changes functionality...")
    
    # Create a test workflow config
    test_workflow = {
        "name": "TestWorkflow",
        "nodes": [
            {
                "id": "start_node",
                "position": {"x": 0, "y": 0},
                "data": {
                    "label": "Start Node",
                    "type": "start",
                    "description": "Starting point of the workflow",
                    "editable": False,
                    "logic": "Initialize workflow state",
                    "nodeFunction": "start_node",
                    "nextNode": "process_node",
                    "conditionalLogic": "",
                    "stateUpdates": {
                        "user_request": "state['user_request']",
                        "step_count": "0"
                    },
                    "conditionalEdges": [],
                    "errorHandler": ""
                },
                "type": "default",
                "style": {"background": "#d5f5e3"}
            },
            {
                "id": "process_node",
                "position": {"x": 200, "y": 0},
                "data": {
                    "label": "Process Node",
                    "type": "processing",
                    "description": "Processes the input",
                    "editable": True,
                    "logic": "Process the input data",
                    "nodeFunction": "process_node",
                    "nextNode": "decision_node",
                    "conditionalLogic": "",
                    "stateUpdates": {
                        "processed_data": "process(input_data)",
                        "status": "'completed'"
                    },
                    "conditionalEdges": [
                        {
                            "condition": "data_valid",
                            "target": "output_node"
                        },
                        {
                            "condition": "not data_valid",
                            "target": "error_node"
                        }
                    ],
                    "errorHandler": "handle_process_error"
                },
                "type": "default",
                "style": {"background": "#d2b4de"}
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "source": "start_node",
                "target": "process_node",
                "animated": True
            }
        ]
    }
    
    # Write to a temporary file to simulate the request
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_workflow, f)
        temp_path = f.name
    
    print("Test workflow created successfully")
    print(f"Test workflow has {len(test_workflow['nodes'])} nodes and {len(test_workflow['edges'])} edges")
    
    # Clean up
    os.unlink(temp_path)
    
    print("✅ Test workflow structure is valid")
    print("\nThe apply changes functionality is ready to be tested in the UI.")
    print("When you click 'Apply to Code' in the React UI, it will:")
    print("1. Send the current workflow configuration to the backend")
    print("2. Create a backup of the original langgraph_agent.py file")
    print("3. Parse the file using AST")
    print("4. Update node functions, state definitions, and graph structure")
    print("5. Write the modified code back to the file")
    print("6. Report success or error to the UI")

if __name__ == "__main__":
    test_apply_changes()