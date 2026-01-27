"""
Test script to verify the state history functionality
"""
import json
import requests
import time
from pathlib import Path

def test_state_history():
    """Test the state history functionality"""
    base_url = "http://localhost:5004"
    
    print("Testing state history functionality...")
    
    # Step 1: Get initial workflow
    print("\\n1. Getting initial workflow...")
    response = requests.get(f"{base_url}/api/workflow/current")
    if response.status_code == 200:
        initial_workflow = response.json()
        print(f"   ✓ Got initial workflow with {len(initial_workflow.get('nodes', []))} nodes")
    else:
        print(f"   ✗ Failed to get initial workflow: {response.text}")
        return False
    
    # Step 2: Save the initial state to history
    print("\\n2. Saving initial state to history...")
    save_response = requests.post(
        f"{base_url}/api/workflow/history/save",
        json=initial_workflow
    )
    if save_response.status_code == 200:
        save_result = save_response.json()
        print(f"   ✓ Saved state: {save_result.get('state_id')}")
    else:
        print(f"   ✗ Failed to save state: {save_response.text}")
        return False
    
    # Step 3: Create a modified workflow
    print("\\n3. Creating a modified workflow...")
    modified_workflow = {
        "name": "ModifiedWorkflow",
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
    
    # Step 4: Save the modified state to history
    print("\\n4. Saving modified state to history...")
    save_modified_response = requests.post(
        f"{base_url}/api/workflow/history/save",
        json=modified_workflow
    )
    if save_modified_response.status_code == 200:
        save_mod_result = save_modified_response.json()
        print(f"   ✓ Saved modified state: {save_mod_result.get('state_id')}")
    else:
        print(f"   ✗ Failed to save modified state: {save_modified_response.text}")
        return False
    
    # Step 5: Get history list
    print("\\n5. Getting history list...")
    history_response = requests.get(f"{base_url}/api/workflow/history")
    if history_response.status_code == 200:
        history_data = history_response.json()
        print(f"   ✓ Got history with {len(history_data.get('history', []))} states")
        print(f"   ✓ Current index: {history_data.get('current_index', -1)}")
        print(f"   ✓ Can undo: {history_data.get('can_undo', False)}")
        print(f"   ✓ Can redo: {history_data.get('can_redo', False)}")
    else:
        print(f"   ✗ Failed to get history: {history_response.text}")
        return False
    
    # Step 6: Perform undo
    print("\\n6. Performing undo operation...")
    undo_response = requests.post(f"{base_url}/api/workflow/history/undo")
    if undo_response.status_code == 200:
        undo_result = undo_response.json()
        print(f"   ✓ Undo successful: {undo_result.get('message')}")
        print(f"   ✓ Can undo after undo: {undo_result.get('can_undo', False)}")
        print(f"   ✓ Can redo after undo: {undo_result.get('can_redo', False)}")
    else:
        print(f"   ✗ Failed to perform undo: {undo_response.text}")
        return False
    
    # Step 7: Perform redo
    print("\\n7. Performing redo operation...")
    redo_response = requests.post(f"{base_url}/api/workflow/history/redo")
    if redo_response.status_code == 200:
        redo_result = redo_response.json()
        print(f"   ✓ Redo successful: {redo_result.get('message')}")
        print(f"   ✓ Can undo after redo: {redo_result.get('can_undo', False)}")
        print(f"   ✓ Can redo after redo: {redo_result.get('can_redo', False)}")
    else:
        print(f"   ✗ Failed to perform redo: {redo_response.text}")
        return False
    
    print("\\n✅ All state history functionality tests passed!")
    return True


if __name__ == "__main__":
    success = test_state_history()
    if success:
        print("\\n🎉 State history functionality is working correctly!")
    else:
        print("\\n❌ State history functionality has issues!")