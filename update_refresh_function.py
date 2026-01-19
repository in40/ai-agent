#!/usr/bin/env python3
"""
Script to update the React app with the refresh functionality.
This script adds the API endpoint call to refresh the workflow from the server.
"""

import json
import re
from pathlib import Path

def update_refresh_function():
    """Update the refresh function in the React app to call the API."""
    # Read the current App.js file
    app_file_path = Path(__file__).parent / "gui/react_editor/src/App.js"
    
    with open(app_file_path, 'r') as f:
        content = f.read()
    
    # Update the refreshWorkflow function to call the API
    updated_content = re.sub(
        r'(// Function to refresh workflow from server.*?)alert\([^)]+\);',
        r"""// Function to refresh workflow from server
const refreshWorkflow = async () => {
  try {
    // Call the backend API to get the current workflow
    const response = await fetch('http://localhost:5001/api/workflow/current');
    if (!response.ok) {
      throw new Error(`Failed to fetch workflow: ${response.status} ${response.statusText}`);
    }
    
    const workflowData = await response.json();
    if (workflowData.status === 'error') {
      throw new Error(workflowData.message || 'Unknown error occurred');
    }
    
    // Update the nodes and edges in the React Flow
    setNodes(workflowData.nodes);
    setEdges(workflowData.edges);
    
    alert(`Workflow refreshed successfully! Loaded ${workflowData.nodes.length} nodes and ${workflowData.edges.length} edges.`);
  } catch (error) {
    console.error('Error refreshing workflow:', error);
    alert('Error refreshing workflow: ' + error.message);
  }
};""",
        content,
        flags=re.DOTALL
    )
    
    # Write the updated content back to the file
    with open(app_file_path, 'w') as f:
        f.write(updated_content)
    
    print("Updated refreshWorkflow function to call API endpoint")

def main():
    print("Updating React app refresh functionality...")
    update_refresh_function()
    print("React app updated with API-based refresh functionality!")

if __name__ == "__main__":
    main()