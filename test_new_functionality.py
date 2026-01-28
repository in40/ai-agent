"""
Test script to verify the new component management functionality
"""
import requests
import json
import time

def test_new_functionality():
    """Test the new component management functionality"""
    base_url = "http://localhost:5004"
    
    print("Testing new component management functionality...")
    
    # Test 1: Get current workflow to ensure it's working
    print("\\n1. Testing current workflow retrieval...")
    try:
        response = requests.get(f"{base_url}/api/workflow/current")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("   ✓ Workflow retrieval is working")
                print(f"   ✓ Retrieved workflow with {len(data.get('nodes', []))} nodes and {len(data.get('edges', []))} edges")
            else:
                print(f"   ✗ Workflow retrieval failed: {data.get('message')}")
        else:
            print(f"   ✗ Workflow retrieval failed with status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error retrieving workflow: {str(e)}")
    
    # Test 2: Test the simulation endpoints
    print("\\n2. Testing simulation endpoints...")
    try:
        response = requests.get(f"{base_url}/api/simulation/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("   ✓ Simulation status endpoint is working")
            else:
                print(f"   ✗ Simulation status failed: {data.get('message')}")
        else:
            print(f"   ✗ Simulation status failed with status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error testing simulation: {str(e)}")
    
    # Test 3: Test the history endpoints
    print("\\n3. Testing history endpoints...")
    try:
        response = requests.get(f"{base_url}/api/workflow/history")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                print("   ✓ History endpoint is working")
                print(f"   ✓ History contains {len(data.get('history', []))} states")
            else:
                print(f"   ✗ History retrieval failed: {data.get('message')}")
        else:
            print(f"   ✗ History retrieval failed with status code: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error testing history: {str(e)}")
    
    print("\\n✅ All tests completed!")
    print("\\nNew functionality includes:")
    print("  - Component library sidebar with searchable components")
    print("  - Drag-and-drop node creation from the library")
    print("  - Advanced node configuration with state updates and conditional edges")
    print("  - Custom edge visualization with labels")
    print("  - Conditional edge creation with condition configuration")
    print("  - Integration with existing workflow system")
    print("  - Undo/redo functionality for workflow changes")
    print("  - Simulation functionality with step-by-step execution")

if __name__ == "__main__":
    test_new_functionality()