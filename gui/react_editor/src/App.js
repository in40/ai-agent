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
import ComponentLibrary from './components/ComponentLibrary';

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

// Custom edge component for conditional edges
const CustomEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}) => {
  // Calculate the midpoint for the label
  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={`M${sourceX},${sourceY} C ${sourceX + 100},${sourceY} ${targetX - 100},${targetY} ${targetX},${targetY}`}
        stroke="#555"
        strokeWidth={2}
        markerEnd={markerEnd}
      />
      {data && data.label && (
        <foreignObject
          width={data.labelWidth || 100}
          height={data.labelHeight || 30}
          x={midX - (data.labelWidth || 100) / 2}
          y={midY - 15}
        >
          <div style={{
            background: 'rgba(255, 255, 255, 0.8)',
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '12px',
            textAlign: 'center',
            border: '1px solid #ccc'
          }}>
            {data.label}
          </div>
        </foreignObject>
      )}
    </>
  );
};

const nodeTypes = {
  default: CustomNode,
};

const edgeTypes = {
  customEdge: CustomEdge,
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
const refreshWorkflowFromServer = async (setNodes, setEdges) => {
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
        workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
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
          apiUrl = 'http://192.168.51.216:5000';  // Changed from 5001 to 5000 (gateway service)
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
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [simulationStatus, setSimulationStatus] = useState(null);
  const [simulationLog, setSimulationLog] = useState([]);

  // Connection handlers for conditional edge creation
  const [connectionStart, setConnectionStart] = useState(null);

  // Load workflow from backend when component mounts
  useEffect(() => {
    // Add a small delay to ensure the UI is rendered before the API call
    const loadWorkflow = async () => {
      // Small delay to ensure UI is ready
      await new Promise(resolve => setTimeout(resolve, 500));
      if (activeTab === 'editor') {
        refreshWorkflowFromServer(setNodes, setEdges);
        // Update history status after loading workflow
        updateHistoryStatus();
      }
    };

    loadWorkflow();
  }, [activeTab]);

  // Update history status when nodes or edges change
  useEffect(() => {
    // Save the current state to history when the workflow changes
    const saveCurrentState = async () => {
      // Only save if we have valid nodes
      if (nodes && nodes.length > 0) {
        await saveWorkflowState(nodes, edges, workflowName);
        // Update history status after saving
        updateHistoryStatus();
      }
    };

    // Debounce the save operation to avoid too frequent saves
    const timer = setTimeout(() => {
      saveCurrentState();
    }, 1000); // Wait 1 second after changes before saving

    return () => clearTimeout(timer);
  }, [nodes, edges, workflowName]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Connection handlers for conditional edge creation
  const onConnectStart = (_, { nodeId, handleType }) => {
    setConnectionStart({ nodeId, handleType });
  };

  const onConnectEnd = (event) => {
    const targetIsPane = (event.target && event.target.classList.contains('react-flow__pane'));

    if (targetIsPane) {
      // User dropped connection on pane - could open conditional edge configuration modal
      if (connectionStart) {
        // Show a modal to configure the conditional edge
        showConditionalEdgeModal(connectionStart.nodeId);
      }
    }
  };

  // Function to show conditional edge configuration modal
  const showConditionalEdgeModal = (sourceNodeId) => {
    // In a real implementation, this would open a modal to configure the conditional edge
    // For now, we'll just show a prompt to get the condition
    const condition = prompt("Enter the condition for this conditional edge:");

    if (condition) {
      // In a real implementation, we would store this temporarily until the user
      // completes the connection to the target node
      console.log(`Conditional edge from ${sourceNodeId} with condition: ${condition}`);
    }

    setConnectionStart(null);
  };

  // Function to handle drag start from component library
  const handleDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(nodeType));
    event.dataTransfer.effectAllowed = 'move';
  };

  // Function to handle drop on canvas
  const onDrop = (event) => {
    event.preventDefault();

    const componentType = event.dataTransfer.getData('application/reactflow');

    // Check if the dropped element is valid
    if (typeof componentType === 'undefined' || !componentType) {
      return;
    }

    const parsedComponent = JSON.parse(componentType);

    // Get the position of the drop
    const reactFlowBounds = event.currentTarget.getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top
    };

    // Create a new node with unique ID
    const newNode = {
      id: `${parsedComponent.id}-${Date.now()}`,
      type: 'default',
      position,
      data: {
        ...parsedComponent.data,
        label: parsedComponent.name,
        type: parsedComponent.nodeType,
        editable: true
      },
      // Apply appropriate style based on node type
      style: getNodeStyle(parsedComponent.nodeType)
    };

    // Add the new node to the state
    setNodes((nds) => nds.concat(newNode));
  };

  // Function to handle drag over
  const onDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  };

  // Helper function to get node style based on type
  const getNodeStyle = (nodeType) => {
    const styles = {
      start: {
        border: '1px solid #555',
        padding: '15px',
        background: '#d5f5e3',  // Light green
        borderRadius: '50%',
        width: '120px',
        height: '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold'
      },
      end: {
        border: '1px solid #555',
        padding: '15px',
        background: '#f1948a',  // Red
        borderRadius: '50%',
        width: '120px',
        height: '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: 'bold'
      },
      database: {
        border: '1px solid #555',
        padding: '15px',
        background: '#d6eaf8',  // Blue
        borderRadius: '8px',
        width: '200px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      },
      llm_calling: {
        border: '1px solid #555',
        padding: '15px',
        background: '#fadbd8',  // Pink
        borderRadius: '8px',
        width: '200px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      },
      mcp: {
        border: '1px solid #555',
        padding: '15px',
        background: '#d2b4de',  // Purple
        borderRadius: '8px',
        width: '200px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      },
      rag: {
        border: '1px solid #555',
        padding: '15px',
        background: '#85c1e9',  // Light blue
        borderRadius: '8px',
        width: '200px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      },
      default: {
        border: '1px solid #555',
        padding: '15px',
        background: '#ffffff',  // White
        borderRadius: '8px',
        width: '200px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }
    };

    return styles[nodeType] || styles.default;
  };

  // Function to handle undo operation
  const handleUndo = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/workflow/history/undo`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        // Update the UI with the retrieved workflow
        setNodes(result.workflow.nodes || []);
        setEdges(result.workflow.edges || []);
        setCanUndo(result.can_undo);
        setCanRedo(result.can_redo);
        console.log('Undo successful:', result);
      } else {
        alert(`Error: ${result.message}`);
        console.error('Error performing undo:', result);
      }
    } catch (error) {
      console.error('Error performing undo:', error);
      alert(`Error performing undo: ${error.message}`);
    }
  };

  // Function to handle redo operation
  const handleRedo = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/workflow/history/redo`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        // Update the UI with the retrieved workflow
        setNodes(result.workflow.nodes || []);
        setEdges(result.workflow.edges || []);
        setCanUndo(result.can_undo);
        setCanRedo(result.can_redo);
        console.log('Redo successful:', result);
      } else {
        alert(`Error: ${result.message}`);
        console.error('Error performing redo:', result);
      }
    } catch (error) {
      console.error('Error performing redo:', error);
      alert(`Error performing redo: ${error.message}`);
    }
  };

  // Function to refresh workflow from server and update history status
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
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
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
            apiUrl = 'http://192.168.51.216:5000';  // Changed from 5001 to 5000 (gateway service)
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

  // Function to update history status
  const updateHistoryStatus = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/workflow/history`;

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        setCanUndo(result.can_undo);
        setCanRedo(result.can_redo);
      } else {
        console.error('Error getting history status:', result);
      }
    } catch (error) {
      console.error('Error getting history status:', error);
    }
  };

  // Function to start/stop the simulation
  const toggleSimulation = async () => {
    if (isSimulating) {
      // Stop the simulation
      try {
        // Use environment variable for API URL with fallback
        let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

        if (!workflowApiUrl) {
          const currentHost = window.location.hostname;
          if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
          } else {
            workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
          }
        }

        const endpoint = `${workflowApiUrl}/api/simulation/reset`;

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        const result = await response.json();

        if (result.status === 'success') {
          setIsSimulating(false);
          setIsPaused(false);
          setSimulationStatus(null);
          setSimulationLog([]);
          console.log('Simulation stopped:', result);
        } else {
          console.error('Error stopping simulation:', result);
          alert(`Error stopping simulation: ${result.message}`);
        }
      } catch (error) {
        console.error('Error stopping simulation:', error);
        alert(`Error stopping simulation: ${error.message}`);
      }
    } else {
      // Start the simulation
      try {
        // Use environment variable for API URL with fallback
        let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

        if (!workflowApiUrl) {
          const currentHost = window.location.hostname;
          if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
            workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
          } else {
            workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
          }
        }

        const endpoint = `${workflowApiUrl}/api/simulation/start`;

        // Get initial inputs from user
        const userInput = prompt("Enter initial input for the simulation:", "Initial request");
        if (userInput === null) return; // User cancelled

        const requestBody = {
          initial_inputs: {
            user_request: userInput,
            mcp_queries: [],
            mcp_results: [],
            synthesized_result: "",
            can_answer: false,
            iteration_count: 0,
            max_iterations: 3,
            final_answer: "",
            error_message: null,
            mcp_servers: [],
            refined_queries: [],
            failure_reason: null,
            schema_dump: {},
            sql_query: "",
            db_results: [],
            all_db_results: {},
            table_to_db_mapping: {},
            table_to_real_db_mapping: {},
            response_prompt: "",
            messages: [],
            validation_error: null,
            retry_count: 0,
            execution_error: null,
            sql_generation_error: null,
            disable_sql_blocking: false,
            disable_databases: false,
            query_type: "initial",
            database_name: "",
            previous_sql_queries: [],
            registry_url: null,
            discovered_services: [],
            mcp_service_results: [],
            use_mcp_results: false,
            mcp_tool_calls: [],
            mcp_capable_response: "",
            return_mcp_results_to_llm: false,
            is_final_answer: false,
            rag_documents: [],
            rag_context: "",
            use_rag_flag: false,
            rag_relevance_score: 0.0,
            rag_query: "",
            rag_response: ""
          },
          workflow_config: {
            nodes: nodes,
            edges: edges
          }
        };

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        if (result.status === 'success') {
          setIsSimulating(true);
          setIsPaused(false);
          console.log('Simulation started:', result);

          // Start polling for status updates
          pollSimulationStatus();
        } else {
          console.error('Error starting simulation:', result);
          alert(`Error starting simulation: ${result.message}`);
        }
      } catch (error) {
        console.error('Error starting simulation:', error);
        alert(`Error starting simulation: ${error.message}`);
      }
    }
  };

  // Function to step through the simulation
  const stepSimulation = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/simulation/step`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        console.log('Stepped forward in simulation:', result);
        // The step function now handles pausing, so we just need to update status
        await updateSimulationStatus();
      } else {
        console.error('Error stepping simulation:', result);
        alert(`Error stepping simulation: ${result.message}`);
      }
    } catch (error) {
      console.error('Error stepping simulation:', error);
      alert(`Error stepping simulation: ${error.message}`);
    }
  };

  // Function to pause/resume the simulation
  const pauseResumeSimulation = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = isPaused
        ? `${workflowApiUrl}/api/simulation/step`  // Resume is like stepping
        : `${workflowApiUrl}/api/simulation/pause`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        setIsPaused(!isPaused);
        console.log(isPaused ? 'Simulation resumed' : 'Simulation paused:', result);
      } else {
        console.error('Error toggling pause state:', result);
        alert(`Error toggling pause state: ${result.message}`);
      }
    } catch (error) {
      console.error('Error toggling pause state:', error);
      alert(`Error toggling pause state: ${error.message}`);
    }
  };

  // Function to update simulation status
  const updateSimulationStatus = async () => {
    try {
      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/simulation/status`;

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      const result = await response.json();

      if (result.status === 'success') {
        setSimulationStatus(result.data);

        // Update log with new execution history
        if (result.data.execution_history) {
          setSimulationLog(prevLog => [
            ...prevLog,
            ...result.data.execution_history.map(step => ({
              ...step,
              timestamp: new Date(step.timestamp * 1000).toLocaleString()
            }))
          ]);
        }

        // Update pause state based on simulation status
        if (result.data.status === 'paused') {
          setIsPaused(true);
        } else if (result.data.status === 'running') {
          setIsPaused(false);
        }

        console.log('Simulation status updated:', result.data);
      } else {
        console.error('Error getting simulation status:', result);
      }
    } catch (error) {
      console.error('Error getting simulation status:', error);
    }
  };

  // Function to poll simulation status periodically
  const pollSimulationStatus = () => {
    const interval = setInterval(async () => {
      if (isSimulating && !isPaused) {
        await updateSimulationStatus();
      } else if (!isSimulating) {
        // Stop polling if simulation is stopped
        clearInterval(interval);
      }
    }, 2000); // Poll every 2 seconds

    // Return function to clear interval when component unmounts or simulation stops
    return () => clearInterval(interval);
  };

  // Function to save the current workflow state to history
  const saveWorkflowState = async (nodes, edges, workflowName) => {
    try {
      // Construct the workflow configuration object
      const workflowConfig = {
        name: workflowName,
        nodes: nodes,
        edges: edges
      };

      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/workflow/history/save`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowConfig)
      });

      const result = await response.json();

      if (result.status !== 'success') {
        console.error('Error saving workflow state:', result);
      }
    } catch (error) {
      console.error('Error saving workflow state:', error);
    }
  };

  // Function to apply changes directly to the LangGraph code
  const applyChangesToCode = async (nodes, edges, workflowName) => {
    try {
      // Construct the workflow configuration object
      const workflowConfig = {
        name: workflowName,
        nodes: nodes,
        edges: edges
      };

      // Use environment variable for API URL with fallback
      let workflowApiUrl = process.env.REACT_APP_WORKFLOW_API_URL;

      if (!workflowApiUrl) {
        const currentHost = window.location.hostname;
        if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
          workflowApiUrl = 'http://192.168.51.216:5004';  // Workflow API service
        } else {
          workflowApiUrl = `http://${currentHost}:5004`;  // Workflow API service
        }
      }

      const endpoint = `${workflowApiUrl}/api/workflow/apply_changes`;

      console.log('Sending workflow config to apply changes:', workflowConfig);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(workflowConfig)
      });

      const result = await response.json();

      if (result.status === 'success') {
        // After successfully applying changes, save the current state to history
        await saveWorkflowState(nodes, edges, workflowName);
        alert(`Success: ${result.message}`);
        console.log('Changes applied successfully:', result);
      } else {
        alert(`Error: ${result.message}`);
        console.error('Error applying changes:', result);
      }
    } catch (error) {
      console.error('Error applying changes to code:', error);
      alert(`Error applying changes to code: ${error.message}`);
    }
  };

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
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex' }}>
        {activeTab === 'editor' ? (
          <>
            {/* Component Library Sidebar */}
            <div style={{ width: '300px', backgroundColor: '#f8f9fa', borderRight: '1px solid #ddd', overflow: 'hidden' }}>
              <ComponentLibrary onDragStart={handleDragStart} />
            </div>

            {/* Main Canvas Area */}
            <div style={{ flex: 1 }}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onDrop={onDrop}
                onDragOver={onDragOver}
                connectionMode={ConnectionMode.Loose}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onConnectStart={onConnectStart}
                onConnectEnd={onConnectEnd}
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
                        onClick={handleUndo}
                        disabled={!canUndo}
                        style={{
                          marginRight: '5px',
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: canUndo ? '#2196F3' : '#cccccc',
                          color: 'white'
                        }}
                      >
                        ← Undo
                      </button>
                      <button
                        onClick={handleRedo}
                        disabled={!canRedo}
                        style={{
                          marginRight: '5px',
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: canRedo ? '#2196F3' : '#cccccc',
                          color: 'white'
                        }}
                      >
                        Redo →
                      </button>
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
                        style={{ marginRight: '5px', padding: '5px 10px', fontSize: '12px' }}
                      >
                        Export Python
                      </button>
                      <button
                        onClick={() => applyChangesToCode(nodes, edges, workflowName)}
                        style={{ marginRight: '5px', padding: '5px 10px', fontSize: '12px', backgroundColor: '#4CAF50', color: 'white' }}
                      >
                        Apply to Code
                      </button>
                      <button
                        onClick={toggleSimulation}
                        style={{
                          marginRight: '5px',
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: isSimulating ? '#f44336' : '#FF9800',
                          color: 'white'
                        }}
                      >
                        {isSimulating ? 'Stop Simulation' : 'Start Simulation'}
                      </button>
                      <button
                        onClick={stepSimulation}
                        disabled={!isSimulating}
                        style={{
                          marginRight: '5px',
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: !isSimulating ? '#cccccc' : '#2196F3',
                          color: 'white'
                        }}
                      >
                        Step
                      </button>
                      <button
                        onClick={pauseResumeSimulation}
                        disabled={!isSimulating}
                        style={{
                          marginRight: '5px',
                          padding: '5px 10px',
                          fontSize: '12px',
                          backgroundColor: !isSimulating ? '#cccccc' : '#9C27B0',
                          color: 'white'
                        }}
                      >
                        {isPaused ? 'Resume' : 'Pause'}
                      </button>
                    </div>
                  </div>

                  {/* Simulation Log Panel */}
                  {isSimulating && (
                    <div style={{
                      marginTop: '10px',
                      padding: '10px',
                      backgroundColor: '#f9f9f9',
                      borderRadius: '4px',
                      border: '1px solid #ccc',
                      maxHeight: '200px',
                      overflowY: 'auto'
                    }}>
                      <h4>Simulation Log</h4>
                      {simulationLog.length > 0 ? (
                        <div>
                          {simulationLog.slice(-5).map((logEntry, index) => (
                            <div key={index} style={{
                              padding: '5px',
                              margin: '2px 0',
                              backgroundColor: '#eef7ff',
                              borderRadius: '3px',
                              fontSize: '12px'
                            }}>
                              <strong>Step {logEntry.step}:</strong> {logEntry.node_output ?
                                `Node executed, state updated` :
                                'Processing...'}
                              <br />
                              <small>Time: {logEntry.timestamp}</small>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: '12px', color: '#666' }}>No simulation logs yet...</p>
                      )}

                      {simulationStatus && (
                        <div style={{ marginTop: '10px', fontSize: '12px' }}>
                          <strong>Status:</strong> {simulationStatus.status} |
                          <strong> Step:</strong> {simulationStatus.current_step} |
                          <strong> Total Steps:</strong> {simulationStatus.total_steps}
                        </div>
                      )}
                    </div>
                  )}
                </Panel>
              </ReactFlow>
            </div>
          </>
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