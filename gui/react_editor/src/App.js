import React, { useCallback, useState, useRef } from 'react';
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

// Define custom node types
const nodeTypes = {};

// Define initial elements for the flow
const initialNodes = [
  {
    id: '__start__',
    position: { x: 0, y: 0 },
    data: {
      label: 'Start',
      type: 'start',
      description: 'Starting point of the workflow. Initiates the process by moving to get_schema node.',
      editable: false,
      logic: '',
      nodeFunction: 'start_node',
      nextNode: 'get_schema',
      conditionalLogic: 'Always proceed to get_schema'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#d5f5e3',
      borderRadius: '50%',
      width: '80px',
      height: '80px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 'bold'
    }
  },
  {
    id: 'get_schema',
    position: { x: 200, y: 0 },
    data: {
      label: 'Get Schema',
      type: 'database',
      description: 'Retrieves database schema from all available databases. Checks if databases are disabled and adjusts the workflow accordingly.',
      editable: true,
      logic: 'SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = \'public\'',
      nodeFunction: 'get_schema_node',
      nextNode: 'generate_sql',
      conditionalLogic: 'If databases are disabled, skip to discover_services'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#d6eaf8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: 'generate_sql',
    position: { x: 400, y: 0 },
    data: {
      label: 'Generate SQL',
      type: 'llm_calling',
      description: 'Generates SQL query based on the user request and available schema information. **Calls SQL LLM** (configured via SQL_LLM_* environment variables).',
      editable: true,
      logic: 'llm_call(prompt=f"Generate SQL for: {user_request}", schema=schema)',
      nodeFunction: 'generate_sql_node',
      nextNode: 'validate_sql',
      conditionalLogic: 'Always proceed to validate_sql'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#fadbd8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: 'validate_sql',
    position: { x: 600, y: 0 },
    data: {
      label: 'Validate SQL',
      type: 'llm_calling',
      description: 'Validates the generated SQL for safety and correctness. Checks for potentially harmful SQL commands. **May call Security LLM** if USE_SECURITY_LLM is enabled.',
      editable: true,
      logic: 'check_sql_safety(sql_query)\nif USE_SECURITY_LLM:\n  llm_validate(sql_query)',
      nodeFunction: 'validate_sql_node',
      nextNode: 'execute_sql',
      conditionalLogic: 'If SQL is invalid, go to refine_sql; if valid, proceed to execute_sql'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#fadbd8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: 'execute_sql',
    position: { x: 800, y: 0 },
    data: {
      label: 'Execute SQL',
      type: 'database',
      description: 'Executes the validated SQL query against the databases and processes the results.',
      editable: true,
      logic: 'result = db.execute(sql_query)\nprocess_results(result)',
      nodeFunction: 'execute_sql_node',
      nextNode: 'generate_prompt',
      conditionalLogic: 'Always proceed to generate_prompt'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#d6eaf8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: 'generate_prompt',
    position: { x: 1000, y: 0 },
    data: {
      label: 'Generate Prompt',
      type: 'llm_calling',
      description: 'Generates a specialized prompt for the response generation step, incorporating all relevant context. **Calls PROMPT LLM** (configured via PROMPT_LLM_* environment variables).',
      editable: true,
      logic: 'llm_call(prompt=f"Create response prompt with context: {context}", type="prompt")',
      nodeFunction: 'generate_prompt_node',
      nextNode: 'generate_response',
      conditionalLogic: 'Always proceed to generate_response'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#fadbd8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: 'generate_response',
    position: { x: 1200, y: 0 },
    data: {
      label: 'Generate Response',
      type: 'llm_calling',
      description: 'Generates the final human-readable response based on query results and context. **Calls RESPONSE LLM** (configured via RESPONSE_LLM_* environment variables).',
      editable: true,
      logic: 'llm_call(prompt=f"Generate response from: {query_results}", type="response")',
      nodeFunction: 'generate_response_node',
      nextNode: '__end__',
      conditionalLogic: 'Always proceed to end'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#fadbd8',
      borderRadius: '8px',
      width: '120px',
      height: '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  },
  {
    id: '__end__',
    position: { x: 1400, y: 0 },
    data: {
      label: 'End',
      type: 'end',
      description: 'Terminal point of the workflow. Represents the completion of the process.',
      editable: false,
      logic: '',
      nodeFunction: 'end_node',
      nextNode: '',
      conditionalLogic: 'Workflow terminates here'
    },
    type: 'default',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    style: {
      border: '1px solid #555',
      padding: '10px',
      background: '#f1948a',
      borderRadius: '50%',
      width: '80px',
      height: '80px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 'bold'
    }
  },
];

const initialEdges = [
  { id: 'e1', source: '__start__', target: 'get_schema', animated: true },
  { id: 'e2', source: 'get_schema', target: 'generate_sql', animated: true },
  { id: 'e3', source: 'generate_sql', target: 'validate_sql', animated: true },
  { id: 'e4', source: 'validate_sql', target: 'execute_sql', animated: true },
  { id: 'e5', source: 'execute_sql', target: 'generate_prompt', animated: true },
  { id: 'e6', source: 'generate_prompt', target: 'generate_response', animated: true },
  { id: 'e7', source: 'generate_response', target: '__end__', animated: true },
];

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
        conditionalLogic: node.data.conditionalLogic
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

// Function to export workflow as Python LangGraph code
const exportAsPythonCode = (nodes, edges, workflowName) => {
  // Generate Python code for the workflow
  let pythonCode = `"""
LangGraph implementation of ${workflowName} workflow.

Auto-generated from the visual editor.
"""

from typing import TypedDict, List, Dict, Any
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

  // Generate node functions
  nodes.forEach(node => {
    if (node.data.nodeFunction) {
      pythonCode += `def ${node.data.nodeFunction}(state: AgentState):
    """
    ${node.data.description}
    """
    # TODO: Implement the logic for ${node.data.label}
    # Logic: ${node.data.logic || 'Not specified'}
    return state


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

  edges.forEach(edge => {
    pythonCode += `    workflow.add_edge("${edge.source}", "${edge.target}")
`;
  });

  // Find start and end nodes
  const startNode = nodes.find(node => node.data.type === 'start')?.id || nodes[0]?.id;
  const endNode = nodes.find(node => node.data.type === 'end')?.id || 'END';

  pythonCode += `
    # Set entry point and finish point
    workflow.set_entry_point("${startNode}")
    workflow.add_edge("${nodes[nodes.length - 2]?.id || startNode}", END)  # Assuming the second to last node connects to END

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

  // Create a downloadable file
  const dataUri = 'data:text/plain;charset=utf-8,'+ encodeURIComponent(pythonCode);
  const exportFileDefaultName = `${workflowName.replace(/\s+/g, '_')}_langgraph.py`;

  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
};

// Function to import workflow from JSON
const importWorkflow = (file, setNodes, setEdges) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const workflowData = JSON.parse(e.target.result);

      // Update nodes and edges
      setNodes(workflowData.nodes.map(node => ({
        ...node,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        // Ensure all data properties are properly initialized
        data: {
          ...node.data,
          label: node.data.label || '',
          type: node.data.type || 'default',
          description: node.data.description || '',
          editable: node.data.editable !== undefined ? node.data.editable : true,
          logic: node.data.logic || '',
          nodeFunction: node.data.nodeFunction || '',
          nextNode: node.data.nextNode || '',
          conditionalLogic: node.data.conditionalLogic || ''
        }
      })));
      setEdges(workflowData.edges || []);
    } catch (error) {
      console.error('Error parsing workflow file:', error);
      alert('Invalid workflow file format');
    }
  };
  reader.readAsText(file);
};

// Custom node component for editing
const CustomNode = ({ data, id, xPos, yPos, nodes, setNodes, ...rest }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const [description, setDescription] = useState(data.description);
  const [logic, setLogic] = useState(data.logic || '');
  const [nodeFunction, setNodeFunction] = useState(data.nodeFunction || '');
  const [nextNode, setNextNode] = useState(data.nextNode || '');
  const [conditionalLogic, setConditionalLogic] = useState(data.conditionalLogic || '');

  const handleSave = () => {
    // Update the node data in the parent component
    const updatedNodes = nodes.map(node =>
      node.id === id
        ? {
            ...node,
            data: {
              ...node.data,
              label,
              description,
              logic,
              nodeFunction,
              nextNode,
              conditionalLogic
            }
          }
        : node
    );
    setNodes(updatedNodes);
    setIsEditing(false);
  };

  const handleCancel = () => {
    // Reset to original values
    setLabel(data.label);
    setDescription(data.description);
    setLogic(data.logic || '');
    setNodeFunction(data.nodeFunction || '');
    setNextNode(data.nextNode || '');
    setConditionalLogic(data.conditionalLogic || '');
    setIsEditing(false);
  };

  return (
    <div style={{
      border: '1px solid #555',
      padding: '10px',
      background: data.type === 'start' ? '#d5f5e3' :
                 data.type === 'end' ? '#f1948a' :
                 data.type === 'database' ? '#d6eaf8' :
                 data.type === 'llm_calling' ? '#fadbd8' : '#ffffff',
      borderRadius: data.type === 'start' || data.type === 'end' ? '50%' : '8px',
      width: data.type === 'start' || data.type === 'end' ? '80px' : '120px',
      height: data.type === 'start' || data.type === 'end' ? '80px' : '60px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      position: 'relative'
    }}>
      <Handle type="target" position={Position.Left} />
      {isEditing ? (
        <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            style={{ marginBottom: '5px', fontSize: '12px' }}
            placeholder="Node Label"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ fontSize: '10px', resize: 'none', flex: 1, marginBottom: '5px' }}
            placeholder="Node Description"
          />
          <textarea
            value={logic}
            onChange={(e) => setLogic(e.target.value)}
            placeholder="Enter node logic (code, conditions, etc.)"
            style={{ fontSize: '10px', resize: 'none', flex: 1, marginBottom: '5px' }}
          />
          <input
            type="text"
            value={nodeFunction}
            onChange={(e) => setNodeFunction(e.target.value)}
            style={{ marginBottom: '5px', fontSize: '10px' }}
            placeholder="Node Function Name"
          />
          <input
            type="text"
            value={nextNode}
            onChange={(e) => setNextNode(e.target.value)}
            style={{ marginBottom: '5px', fontSize: '10px' }}
            placeholder="Next Node (for conditional edges)"
          />
          <textarea
            value={conditionalLogic}
            onChange={(e) => setConditionalLogic(e.target.value)}
            placeholder="Conditional Logic (when to go to next node)"
            style={{ fontSize: '10px', resize: 'none', flex: 1, marginBottom: '5px' }}
          />
          <div style={{ display: 'flex', gap: '5px', marginTop: '5px' }}>
            <button onClick={handleSave} style={{ fontSize: '10px', padding: '2px 4px' }}>Save</button>
            <button onClick={handleCancel} style={{ fontSize: '10px', padding: '2px 4px' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <div style={{ fontWeight: 'bold', textAlign: 'center', fontSize: '12px' }}>{label}</div>
          {data.editable && (
            <button
              onClick={() => setIsEditing(true)}
              style={{
                position: 'absolute',
                bottom: '2px',
                right: '2px',
                fontSize: '10px',
                padding: '1px 3px'
              }}
            >
              ✏️
            </button>
          )}
          {(data.logic || data.nodeFunction) && (
            <div title={`${data.logic || ''}\n${data.nodeFunction || ''}`} style={{ position: 'absolute', top: '2px', right: '2px', fontSize: '8px' }}>
              ⚙️
            </div>
          )}
        </>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
};

const nodeTypesWithCustom = {
  ...nodeTypes,
  custom: (props) => <CustomNode {...props} nodes={nodes} setNodes={setNodes} />,
};

const LangGraphEditor = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [workflowName, setWorkflowName] = useState('My LangGraph Workflow');
  const [nodeTypeFilter, setNodeTypeFilter] = useState('all');

  // Handle connection between nodes
  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, animated: true }, eds)),
    [setEdges]
  );

  // Function to add conditional edge
  const addConditionalEdge = (sourceNodeId, targetNodeId, condition) => {
    const newEdge = {
      id: `edge-${sourceNodeId}-${targetNodeId}-${Date.now()}`,
      source: sourceNodeId,
      target: targetNodeId,
      animated: true,
      label: condition || 'condition',
      style: { stroke: '#ff6b6b', strokeWidth: 2 }
    };
    setEdges(prevEdges => [...prevEdges, newEdge]);
  };

  // Handle initialization of React Flow instance
  const onInit = useCallback((instance) => {
    setReactFlowInstance(instance);
  }, []);

  // Handle node selection
  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  // Add a new node to the flow
  const addNode = (type) => {
    const newNode = {
      id: `${type}_${Date.now()}`,
      position: {
        x: Math.random() * 400,
        y: Math.random() * 400
      },
      data: {
        label: `${type.charAt(0).toUpperCase() + type.slice(1)} Node`,
        type: type,
        description: `A new ${type} node added to the workflow.`,
        editable: true,
        logic: '',
        nodeFunction: `${type}Node`,
        nextNode: '',
        conditionalLogic: ''
      },
      type: 'custom',
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        border: '1px solid #555',
        padding: '10px',
        background: type === 'start' ? '#d5f5e3' :
                   type === 'end' ? '#f1948a' :
                   type === 'database' ? '#d6eaf8' :
                   type === 'llm_calling' ? '#fadbd8' : '#ffffff',
        borderRadius: type === 'start' || type === 'end' ? '50%' : '8px',
        width: type === 'start' || type === 'end' ? '80px' : '120px',
        height: type === 'start' || type === 'end' ? '80px' : '60px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }
    };

    setNodes((nds) => nds.concat(newNode));
  };

  // Delete selected node
  const deleteSelectedNode = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter(node => node.id !== selectedNode.id));
      setEdges((eds) => eds.filter(edge => 
        edge.source !== selectedNode.id && edge.target !== selectedNode.id
      ));
      setSelectedNode(null);
    }
  };

  // Filter nodes based on type
  const filteredNodes = nodeTypeFilter === 'all' 
    ? nodes 
    : nodes.filter(node => node.data.type === nodeTypeFilter);

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      {/* Top panel with controls */}
      <Panel position="top-center" style={{
        display: 'flex',
        gap: '10px',
        padding: '10px',
        backgroundColor: 'white',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        zIndex: 10,
        flexWrap: 'wrap'
      }}>
        <input
          type="text"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          style={{ padding: '5px', fontSize: '16px' }}
        />
        <select
          value={nodeTypeFilter}
          onChange={(e) => setNodeTypeFilter(e.target.value)}
          style={{ padding: '5px' }}
        >
          <option value="all">All Nodes</option>
          <option value="default">Default</option>
          <option value="database">Database</option>
          <option value="llm_calling">LLM Calling</option>
          <option value="start">Start</option>
          <option value="end">End</option>
        </select>
        <button onClick={() => addNode('default')} style={{ padding: '5px 10px' }}>
          Add Node
        </button>
        <button onClick={() => addNode('database')} style={{ padding: '5px 10px' }}>
          Add DB Node
        </button>
        <button onClick={() => addNode('llm_calling')} style={{ padding: '5px 10px' }}>
          Add LLM Node
        </button>
        <button
          onClick={deleteSelectedNode}
          disabled={!selectedNode}
          style={{ padding: '5px 10px', opacity: selectedNode ? 1 : 0.5 }}
        >
          Delete Selected
        </button>
        <button
          onClick={() => console.log('Nodes:', nodes, 'Edges:', edges)}
          style={{ padding: '5px 10px' }}
        >
          Log Elements
        </button>
        <button
          onClick={() => exportWorkflow(nodes, edges, workflowName)}
          style={{ padding: '5px 10px' }}
        >
          Export Workflow
        </button>
        <button
          onClick={() => exportAsPythonCode(nodes, edges, workflowName)}
          style={{ padding: '5px 10px' }}
        >
          Export as Python Code
        </button>
        <label style={{ padding: '5px 10px', backgroundColor: '#f0f0f0', borderRadius: '4px', cursor: 'pointer' }}>
          Import Workflow
          <input
            type="file"
            accept=".json"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                importWorkflow(e.target.files[0], setNodes, setEdges);
              }
            }}
            style={{ display: 'none' }}
          />
        </label>

        {/* Conditional Edge Configuration */}
        <div style={{ display: 'flex', gap: '5px', alignItems: 'center', padding: '5px', border: '1px solid #ccc', borderRadius: '4px' }}>
          <span>Add Conditional Edge:</span>
          <select id="source-node-select" style={{ padding: '3px' }}>
            {nodes.map(node => (
              <option key={`source-${node.id}`} value={node.id}>{node.data.label || node.id}</option>
            ))}
          </select>
          <span>to</span>
          <select id="target-node-select" style={{ padding: '3px' }}>
            {nodes.map(node => (
              <option key={`target-${node.id}`} value={node.id}>{node.data.label || node.id}</option>
            ))}
          </select>
          <input
            type="text"
            id="condition-input"
            placeholder="Condition"
            style={{ padding: '3px', width: '100px' }}
          />
          <button
            onClick={() => {
              const sourceSelect = document.getElementById('source-node-select');
              const targetSelect = document.getElementById('target-node-select');
              const conditionInput = document.getElementById('condition-input');

              const sourceNodeId = sourceSelect.value;
              const targetNodeId = targetSelect.value;
              const condition = conditionInput.value;

              if (sourceNodeId && targetNodeId) {
                addConditionalEdge(sourceNodeId, targetNodeId, condition);
                conditionInput.value = '';
              }
            }}
            style={{ padding: '3px 6px' }}
          >
            Add
          </button>
        </div>
      </Panel>
      
      {/* Side panel with node details */}
      {selectedNode && (
        <Panel position="left" style={{
          width: '300px',
          padding: '10px',
          backgroundColor: 'white',
          boxShadow: '2px 0 10px rgba(0,0,0,0.1)',
          zIndex: 10
        }}>
          <h3>Node Details</h3>
          <p><strong>ID:</strong> {selectedNode.id}</p>
          <p><strong>Type:</strong> {selectedNode.data.type}</p>
          <p><strong>Label:</strong> {selectedNode.data.label}</p>
          <p><strong>Node Function:</strong> {selectedNode.data.nodeFunction}</p>
          <p><strong>Next Node:</strong> {selectedNode.data.nextNode}</p>
          <p><strong>Conditional Logic:</strong> {selectedNode.data.conditionalLogic}</p>

          <div style={{ marginTop: '15px' }}>
            <h4>Edit Properties</h4>
            <p><strong>Description:</strong></p>
            <textarea
              value={selectedNode.data.description}
              onChange={(e) => {
                const updatedNodes = nodes.map(node =>
                  node.id === selectedNode.id
                    ? { ...node, data: { ...node.data, description: e.target.value } }
                    : node
                );
                setNodes(updatedNodes);
              }}
              style={{ width: '100%', height: '80px', marginBottom: '10px' }}
            />

            <p><strong>Logic:</strong></p>
            <textarea
              value={selectedNode.data.logic}
              onChange={(e) => {
                const updatedNodes = nodes.map(node =>
                  node.id === selectedNode.id
                    ? { ...node, data: { ...node.data, logic: e.target.value } }
                    : node
                );
                setNodes(updatedNodes);
              }}
              style={{ width: '100%', height: '80px', marginBottom: '10px' }}
            />

            <p><strong>Node Function:</strong></p>
            <input
              type="text"
              value={selectedNode.data.nodeFunction}
              onChange={(e) => {
                const updatedNodes = nodes.map(node =>
                  node.id === selectedNode.id
                    ? { ...node, data: { ...node.data, nodeFunction: e.target.value } }
                    : node
                );
                setNodes(updatedNodes);
              }}
              style={{ width: '100%', marginBottom: '10px' }}
            />

            <p><strong>Next Node:</strong></p>
            <input
              type="text"
              value={selectedNode.data.nextNode}
              onChange={(e) => {
                const updatedNodes = nodes.map(node =>
                  node.id === selectedNode.id
                    ? { ...node, data: { ...node.data, nextNode: e.target.value } }
                    : node
                );
                setNodes(updatedNodes);
              }}
              style={{ width: '100%', marginBottom: '10px' }}
            />

            <p><strong>Conditional Logic:</strong></p>
            <textarea
              value={selectedNode.data.conditionalLogic}
              onChange={(e) => {
                const updatedNodes = nodes.map(node =>
                  node.id === selectedNode.id
                    ? { ...node, data: { ...node.data, conditionalLogic: e.target.value } }
                    : node
                );
                setNodes(updatedNodes);
              }}
              style={{ width: '100%', height: '80px' }}
            />
          </div>
        </Panel>
      )}
      
      <ReactFlow
        nodes={filteredNodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={onInit}
        onNodeClick={onNodeClick}
        connectionMode={ConnectionMode.Loose}
        nodeTypes={nodeTypesWithCustom}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <MiniMap />
        <Background variant="dots" gap={12} size={1} />
      </ReactFlow>
    </div>
  );
};

export default LangGraphEditor;