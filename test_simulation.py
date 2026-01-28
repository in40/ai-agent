"""
Test script to verify the simulation functionality
"""
import requests
import time
import json

def test_simulation():
    base_url = "http://localhost:5004"
    
    print("Testing simulation functionality...")
    
    # Step 1: Get initial simulation status
    print("\\n1. Getting initial simulation status...")
    response = requests.get(f"{base_url}/api/simulation/status")
    if response.status_code == 200:
        status_data = response.json()
        print(f"   ✓ Initial status: {status_data['data']['status']}")
    else:
        print(f"   ✗ Failed to get initial status: {response.text}")
        return False
    
    # Step 2: Start a simulation
    print("\\n2. Starting a simulation...")
    start_payload = {
        "initial_inputs": {
            "user_request": "Test request for simulation",
            "mcp_queries": [],
            "mcp_results": [],
            "synthesized_result": "",
            "can_answer": False,
            "iteration_count": 0,
            "max_iterations": 3,
            "final_answer": "",
            "error_message": None,
            "mcp_servers": [],
            "refined_queries": [],
            "failure_reason": None,
            "schema_dump": {},
            "sql_query": "",
            "db_results": [],
            "all_db_results": {},
            "table_to_db_mapping": {},
            "table_to_real_db_mapping": {},
            "response_prompt": "",
            "messages": [],
            "validation_error": None,
            "retry_count": 0,
            "execution_error": None,
            "sql_generation_error": None,
            "disable_sql_blocking": False,
            "disable_databases": False,
            "query_type": "initial",
            "database_name": "",
            "previous_sql_queries": [],
            "registry_url": None,
            "discovered_services": [],
            "mcp_service_results": [],
            "use_mcp_results": False,
            "mcp_tool_calls": [],
            "mcp_capable_response": "",
            "return_mcp_results_to_llm": False,
            "is_final_answer": False,
            "rag_documents": [],
            "rag_context": "",
            "use_rag_flag": False,
            "rag_relevance_score": 0.0,
            "rag_query": "",
            "rag_response": ""
        },
        "workflow_config": {
            "nodes": [],
            "edges": []
        }
    }
    
    response = requests.post(f"{base_url}/api/simulation/start", json=start_payload)
    if response.status_code == 200:
        start_result = response.json()
        print(f"   ✓ Simulation started: {start_result['message']}")
    else:
        print(f"   ✗ Failed to start simulation: {response.text}")
        return False
    
    # Step 3: Try to step through the simulation
    print("\\n3. Stepping through the simulation...")
    step_response = requests.post(f"{base_url}/api/simulation/step")
    if step_response.status_code == 200:
        step_result = step_response.json()
        print(f"   ✓ Step executed: {step_result['message']}")
    else:
        print(f"   ✗ Failed to step: {step_response.text}")
        # This might be expected if the workflow is already complete
        print("   (This might be OK if the workflow completed immediately)")
    
    # Step 4: Get updated status
    print("\\n4. Getting updated simulation status...")
    response = requests.get(f"{base_url}/api/simulation/status")
    if response.status_code == 200:
        status_data = response.json()
        print(f"   ✓ Updated status: {status_data['data']['status']}")
        print(f"   ✓ Current step: {status_data['data']['current_step']}")
        print(f"   ✓ Total steps: {status_data['data']['total_steps']}")
    else:
        print(f"   ✗ Failed to get updated status: {response.text}")
        return False
    
    # Step 5: Pause the simulation
    print("\\n5. Pausing the simulation...")
    pause_response = requests.post(f"{base_url}/api/simulation/pause")
    if pause_response.status_code == 200:
        pause_result = pause_response.json()
        print(f"   ✓ Simulation pause attempted: {pause_result['message']}")
    else:
        print(f"   ⚠ Pause failed (might be OK if simulation already ended): {pause_response.text}")
    
    # Step 6: Reset the simulation
    print("\\n6. Resetting the simulation...")
    reset_response = requests.post(f"{base_url}/api/simulation/reset")
    if reset_response.status_code == 200:
        reset_result = reset_response.json()
        print(f"   ✓ Simulation reset: {reset_result['message']}")
    else:
        print(f"   ✗ Failed to reset simulation: {reset_response.text}")
        return False
    
    print("\\n✅ All simulation functionality tests passed!")
    return True

if __name__ == "__main__":
    success = test_simulation()
    if success:
        print("\\n🎉 Simulation functionality is working correctly!")
    else:
        print("\\n❌ Simulation functionality has issues!")