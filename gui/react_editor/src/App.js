import React, { useCallback, useState, useEffect } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  ConnectionMode,
  Panel,
  Position,
  Handle
} from '@xyflow/react';

// Import default node types
import '@xyflow/react/dist/style.css';

// Import RAG Component
import RAGComponent from './components/RAGComponent';
import './components/RAGComponent.css';
import AdvancedNodeConfig from './components/AdvancedNodeConfig';

// Define initial empty elements - will be populated from backend
const initialNodes = [];
const initialEdges = [];

// Custom node component to display node information
const CustomNode = ({ data }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [nodeData, setNodeData] = useState(data);
  const [showAdvancedConfig, setShowAdvancedConfig] = useState(false);

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
  };

  const handleSave = () => {
    setIsEditing(false);
    // Here you would typically send the updated data to the backend
  };

  const handleChange = (field, value) => {
    setNodeData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleAdvancedConfigUpdate = (updatedData) => {
    setNodeData(updatedData);
    setShowAdvancedConfig(false);
  };

  // Render state fields for this node
  const renderStateFields = () => {
    if (!nodeData.stateUpdates || Object.keys(nodeData.stateUpdates).length === 0) {
      return <div>No state updates defined</div>;
    }

    return Object.entries(nodeData.stateUpdates).map(([key, value]) => (
      <div key={key} style={{ marginBottom: "4px" }}>
        <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : String(value)}
      </div>
    ));
  };

  // Render conditional edges for this node
  const renderConditionalEdges = () => {
    if (!nodeData.conditionalEdges || nodeData.conditionalEdges.length === 0) {
      return <div>No conditional edges defined</div>;
    }

    return nodeData.conditionalEdges.map((edge, index) => (
      <div key={index} style={{ marginBottom: "4px" }}>
        <strong>Condition {index + 1}:</strong> {edge.condition} → {edge.target}
      </div>
    ));
  };

  return (
    <div style={{
      border: "1px solid #555",
      padding: "10px",
      borderRadius: "8px",
      width: "400px",
      minHeight: "200px",
      backgroundColor: data.style?.background || "#fff",
      overflow: "visible"  // Allow content to be visible even if it extends beyond the node
    }}>
      <div style={{ fontWeight: "bold", marginBottom: "8px" }}>
        {data.label}
      </div>

      <div style={{ fontSize: "12px", marginBottom: "8px", fontStyle: "italic" }}>
        Type: {data.type}
      </div>

      <div style={{ fontSize: "12px", marginBottom: "8px" }}>
        Description: {data.description}
      </div>

      {data.editable && (
        <>
          <button onClick={handleEditToggle} style={{ fontSize: "10px", marginRight: "5px", marginBottom: "4px" }}>
            {isEditing ? "Save" : "Edit"}
          </button>

          <button
            onClick={() => setShowAdvancedConfig(true)}
            style={{ fontSize: "10px", marginBottom: "4px" }}
          >
            Advanced Config
          </button>

          {isEditing && (
            <div style={{ marginTop: "8px", fontSize: "12px" }}>
              <div style={{ marginBottom: "4px" }}>
                <label>Logic:</label><br />
                <textarea
                  value={nodeData.logic || ""}
                  onChange={(e) => handleChange("logic", e.target.value)}
                  rows="2"
                  cols="30"
                  style={{ fontSize: "10px", width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "4px" }}>
                <label>Next Node:</label><br />
                <input
                  type="text"
                  value={nodeData.nextNode || ""}
                  onChange={(e) => handleChange("nextNode", e.target.value)}
                  style={{ fontSize: "10px", width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "4px" }}>
                <label>Conditional Logic:</label><br />
                <textarea
                  value={nodeData.conditionalLogic || ""}
                  onChange={(e) => handleChange("conditionalLogic", e.target.value)}
                  rows="2"
                  cols="30"
                  style={{ fontSize: "10px", width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "4px" }}>
                <label>Node Function Name:</label><br />
                <input
                  type="text"
                  value={nodeData.nodeFunction || ""}
                  onChange={(e) => handleChange("nodeFunction", e.target.value)}
                  style={{ fontSize: "10px", width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "4px" }}>
                <label>Error Handler:</label><br />
                <input
                  type="text"
                  value={nodeData.errorHandler || ""}
                  onChange={(e) => handleChange("errorHandler", e.target.value)}
                  style={{ fontSize: "10px", width: "100%" }}
                />
              </div>
            </div>
          )}

          {!isEditing && (
            <div style={{ fontSize: "12px" }}>
              <div><strong>Logic:</strong> {nodeData.logic || "Not specified"}</div>
              <div><strong>Next Node:</strong> {nodeData.nextNode || "Not specified"}</div>
              <div><strong>Conditional Logic:</strong> {nodeData.conditionalLogic || "Not specified"}</div>
              <div><strong>Node Function:</strong> {nodeData.nodeFunction || "Not specified"}</div>
              <div><strong>Error Handler:</strong> {nodeData.errorHandler || "Not specified"}</div>

              <div style={{ marginTop: "8px" }}>
                <strong>State Updates:</strong>
                {renderStateFields()}
              </div>

              <div style={{ marginTop: "8px" }}>
                <strong>Conditional Edges:</strong>
                {renderConditionalEdges()}
              </div>
            </div>
          )}
        </>
      )}

      {!data.editable && (
        <div style={{ fontSize: "12px" }}>
          <div><strong>Logic:</strong> {nodeData.logic || "Not specified"}</div>
          <div><strong>Next Node:</strong> {nodeData.nextNode || "Not specified"}</div>
          <div><strong>Conditional Logic:</strong> {nodeData.conditionalLogic || "Not specified"}</div>
          <div><strong>Node Function:</strong> {nodeData.nodeFunction || "Not specified"}</div>
          <div><strong>Error Handler:</strong> {nodeData.errorHandler || "Not specified"}</div>

          <div style={{ marginTop: "8px" }}>
            <strong>State Updates:</strong>
            {renderStateFields()}
          </div>

          <div style={{ marginTop: "8px" }}>
            <strong>Conditional Edges:</strong>
            {renderConditionalEdges()}
          </div>
        </div>
      )}

      <Handle type="source" position={Position.Right} style={{ background: '#555' }} />
      <Handle type="target" position={Position.Left} style={{ background: '#555' }} />

      {showAdvancedConfig && (
        <AdvancedNodeConfig
          nodeData={nodeData}
          onUpdate={handleAdvancedConfigUpdate}
          onClose={() => setShowAdvancedConfig(false)}
        />
      )}
    </div>
  );
};

const nodeTypes = {
  default: CustomNode,
};

// Function to export workflow to JSON
const exportWorkflow = (nodes, edges, workflowName) => {
  const workflowData = {
    name: workflowName,
    nodes: nodes.map(node => ({
      id: node.id,
      position: node.position,
      data: {
        ...node.data,
        // Ensure all properties are preserved
        label: node.data.label,
        type: node.data.type,
        description: node.data.description,
        editable: node.data.editable,
        logic: node.data.logic,
        nodeFunction: node.data.nodeFunction,
        nextNode: node.data.nextNode,
        conditionalLogic: node.data.conditionalLogic,
        stateUpdates: node.data.stateUpdates,
        conditionalEdges: node.data.conditionalEdges,
        errorHandler: node.data.errorHandler
      },
      type: node.type,
      style: node.style
    })),
    edges: edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      animated: edge.animated
    }))
  };

  const dataStr = JSON.stringify(workflowData, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

  const exportFileDefaultName = `${workflowName.replace(/\s+/g, '_')}_workflow.json`;

  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
};

// Function to refresh workflow from server
const refreshWorkflow = async (setNodes, setEdges) => {
  try {
    // Call the backend API to get the current workflow
    console.log('Attempting to fetch workflow from API...');

    // Use environment variable for API URL with fallback
    // If not set, construct the API URL using the same host as the current page but different port
    // If the current host is localhost, try to use the actual IP address as well
    let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

    if (!workflowApiUrl) {
      const currentHost = window.location.hostname;
      // If accessing from localhost, try to use a common pattern for the actual IP
      if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
        // Try to get the actual IP from the window.location, or default to a common IP pattern
        // For now, we'll use the known IP address of this server
        workflowApiUrl = 'http://192.168.51.138:5004';  // Workflow API service
      } else {
        workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
      }
    }

    const endpoint = `${workflowApiUrl}/api/workflow/current`;

    console.log(`Fetching from: ${endpoint}`);

    // Add timeout and more detailed error handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minute timeout

    const response = await fetch(endpoint, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      // Adding credentials to handle potential authentication
      credentials: 'omit'
    });
    clearTimeout(timeoutId);

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

    console.log(`Workflow refreshed successfully! Loaded ${workflowData.nodes.length} nodes and ${workflowData.edges.length} edges.`);
    // Removed success alert to reduce notifications, keeping only error alerts
  } catch (error) {
    console.error('Error refreshing workflow:', error);

    // More specific error messages based on error type
    let errorMessage = 'Error refreshing workflow';
    if (error.name === 'AbortError') {
      errorMessage = 'Request timed out. Please check if the API server is running.';
    } else if (error instanceof TypeError && error.message.includes('fetch')) {
      // Recreate the apiUrl here since it's not in scope in this catch block
      let apiUrl = process.env.REACT_APP_API_URL;

      if (!apiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          apiUrl = 'http://192.168.51.138:5000';  // Changed from 5001 to 5000 (gateway service)
        } else {
          apiUrl = `http://${currentHost}:5000`;  // Changed from 5001 to 5000 (gateway service)
        }
      }

      errorMessage = `Network error. Please check your connection and ensure the API server is running on ${apiUrl}`;
    } else {
      errorMessage = error.message;
    }

    alert(errorMessage);
  }
};

// Function to export workflow as Python LangGraph code
const exportAsPythonCode = (nodes, edges, workflowName) => {
  // Generate Python code for the workflow
  let pythonCode = `"""
LangGraph implementation of ${workflowName} workflow.

Auto-generated from the visual editor.
"""

from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State definition for the ${workflowName} agent.
    """
    user_request: str
    messages: List[BaseMessage]
    # Add other state fields as needed based on your workflow
`;

  // Add state fields from nodes
  const allStateFields = new Set();
  nodes.forEach(node => {
    if (node.data.stateUpdates) {
      Object.keys(node.data.stateUpdates).forEach(field => {
        allStateFields.add(field);
      });
    }
  });

  allStateFields.forEach(field => {
    pythonCode += `    ${field}: Any  # Added from node state updates\n`;
  });

  pythonCode += `\n`;

  // Generate node functions
  nodes.forEach(node => {
    if (node.data.nodeFunction) {
      pythonCode += `def ${node.data.nodeFunction}(state: AgentState):
    """
    ${node.data.description}
    """
    # TODO: Implement the logic for ${node.data.label}
    # Logic: ${node.data.logic || 'Not specified'}

    # State updates from visual editor:
`;
      if (node.data.stateUpdates) {
        Object.entries(node.data.stateUpdates).forEach(([key, value]) => {
          pythonCode += `    # state['${key}'] = ${JSON.stringify(value)}  # From visual editor\n`;
        });
      }
      pythonCode += `    return state


`;
    }
  });

  // Generate conditional edge functions
  const conditionalEdges = new Map();
  nodes.forEach(node => {
    if (node.data.conditionalEdges && node.data.conditionalEdges.length > 0) {
      const functionName = `${node.data.nodeFunction || node.id}_router`;
      conditionalEdges.set(functionName, { node: node, edges: node.data.conditionalEdges });

      pythonCode += `def ${functionName}(state: AgentState) -> Literal[${node.data.conditionalEdges.map(e => `"${e.target}"`).join(', ')}]:
    """
    Router function for ${node.data.label} node.
    Determines which path to take based on state conditions.
    """
    # TODO: Implement conditional logic for ${node.data.label}
    # Conditions from visual editor:
`;
      node.data.conditionalEdges.forEach((edge, index) => {
        pythonCode += `    # Condition ${index + 1}: ${edge.condition} -> "${edge.target}"\n`;
      });
      pythonCode += `    # Default to first option if no conditions met
    return "${node.data.conditionalEdges[0]?.target || 'END'}"


`;
    }
  });

  // Generate the workflow graph
  pythonCode += `def create_${workflowName.toLowerCase().replace(/\s+/g, '_')}_graph():
    """
    Create the ${workflowName} workflow using LangGraph
    """
    workflow = StateGraph(AgentState)

    # Add nodes
`;

  nodes.forEach(node => {
    if (node.data.nodeFunction) {
      pythonCode += `    workflow.add_node("${node.id}", ${node.data.nodeFunction})
`;
    }
  });

  pythonCode += `
    # Define edges
`;

  // Add regular edges
  edges.forEach(edge => {
    pythonCode += `    workflow.add_edge("${edge.source}", "${edge.target}")
`;
  });

  // Add conditional edges
  conditionalEdges.forEach((info, funcName) => {
    pythonCode += `    workflow.add_conditional_edges(
        "${info.node.id}",
        ${funcName},
        {
`;
    info.edges.forEach(edge => {
      pythonCode += `            "${edge.target}": "${edge.target}",\n`;
    });
    pythonCode += `        }\n    )\n`;
  });

  // Find start and end nodes
  const startNode = nodes.find(node => node.data.type === 'start')?.id || nodes[0]?.id;
  const endNode = nodes.find(node => node.data.type === 'end')?.id || 'END';

  pythonCode += `
    # Set entry point
    workflow.set_entry_point("${startNode}")

    return workflow.compile()


# Example usage:
if __name__ == "__main__":
    graph = create_${workflowName.toLowerCase().replace(/\s+/g, '_')}_graph()

    # Example input
    initial_state = {
        "user_request": "Sample request",
        "messages": []
    }

    # Run the workflow
    result = graph.invoke(initial_state)
    print("Final state:", result)
`;

  const dataStr = pythonCode;
  const dataUri = 'data:application/text;charset=utf-8,'+ encodeURIComponent(dataStr);

  const exportFileDefaultName = `${workflowName.replace(/\s+/g, '_')}_workflow.py`;

  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
};

function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflowName, setWorkflowName] = useState('MyWorkflow');
  const [activeTab, setActiveTab] = useState('editor'); // 'editor' or 'rag'

  // Load workflow from backend when component mounts
  useEffect(() => {
    // Add a small delay to ensure the UI is rendered before the API call
    const loadWorkflow = async () => {
      // Small delay to ensure UI is ready
      await new Promise(resolve => setTimeout(resolve, 500));
      if (activeTab === 'editor') {
        refreshWorkflow(setNodes, setEdges);
      }
    };

    loadWorkflow();
  }, [activeTab]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #ccc',
        backgroundColor: '#f5f5f5',
        padding: '10px'
      }}>
        <button
          style={{
            padding: '10px 20px',
            cursor: 'pointer',
            backgroundColor: activeTab === 'editor' ? '#007bff' : '#e0e0e0',
            color: activeTab === 'editor' ? 'white' : '#333',
            border: '1px solid #ccc',
            borderRadius: '5px 5px 0 0',
            marginRight: '5px'
          }}
          onClick={() => setActiveTab('editor')}
        >
          Workflow Editor
        </button>
        <button
          style={{
            padding: '10px 20px',
            cursor: 'pointer',
            backgroundColor: activeTab === 'rag' ? '#007bff' : '#e0e0e0',
            color: activeTab === 'rag' ? 'white' : '#333',
            border: '1px solid #ccc',
            borderRadius: '5px 5px 0 0',
            marginRight: '5px'
          }}
          onClick={() => setActiveTab('rag')}
        >
          RAG Functions
        </button>
      </div>

      {/* Tab Content */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 'editor' ? (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            connectionMode={ConnectionMode.Loose}
            nodeTypes={nodeTypes}
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={12} size={1} />

            <Panel position="top-right">
              <div style={{ padding: '10px', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ccc' }}>
                <h3>Workflow Editor</h3>
                <div>
                  <label>
                    Workflow Name:
                    <input
                      type="text"
                      value={workflowName}
                      onChange={(e) => setWorkflowName(e.target.value)}
                      style={{ marginLeft: '5px' }}
                    />
                  </label>
                </div>
                <div style={{ marginTop: '10px' }}>
                  <button
                    onClick={() => refreshWorkflow(setNodes, setEdges)}
                    style={{ marginRight: '5px', padding: '5px 10px', fontSize: '12px' }}
                  >
                    Refresh Workflow
                  </button>
                  <button
                    onClick={() => exportWorkflow(nodes, edges, workflowName)}
                    style={{ marginRight: '5px', padding: '5px 10px', fontSize: '12px' }}
                  >
                    Export JSON
                  </button>
                  <button
                    onClick={() => exportAsPythonCode(nodes, edges, workflowName)}
                    style={{ padding: '5px 10px', fontSize: '12px' }}
                  >
                    Export Python
                  </button>
                </div>
              </div>
            </Panel>
          </ReactFlow>
        ) : (
          <div style={{ padding: '20px', height: '100%', overflowY: 'auto' }}>
            <RAGComponent />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;