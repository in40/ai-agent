import React, { useState } from 'react';

const AdvancedNodeConfig = ({ nodeData, onUpdate, onClose }) => {
  const [localData, setLocalData] = useState({ ...nodeData });

  const handleChange = (field, value) => {
    setLocalData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleStateUpdateChange = (key, value) => {
    setLocalData(prev => ({
      ...prev,
      stateUpdates: {
        ...prev.stateUpdates,
        [key]: value
      }
    }));
  };

  const handleAddConditionalEdge = () => {
    const newEdge = {
      condition: '',
      target: ''
    };
    
    setLocalData(prev => ({
      ...prev,
      conditionalEdges: [...(prev.conditionalEdges || []), newEdge]
    }));
  };

  const handleConditionalEdgeChange = (index, field, value) => {
    const updatedEdges = [...(localData.conditionalEdges || [])];
    updatedEdges[index][field] = value;
    
    setLocalData(prev => ({
      ...prev,
      conditionalEdges: updatedEdges
    }));
  };

  const handleRemoveConditionalEdge = (index) => {
    const updatedEdges = [...(localData.conditionalEdges || [])];
    updatedEdges.splice(index, 1);
    
    setLocalData(prev => ({
      ...prev,
      conditionalEdges: updatedEdges
    }));
  };

  const handleSave = () => {
    onUpdate(localData);
    onClose();
  };

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      backgroundColor: 'white',
      padding: '20px',
      borderRadius: '8px',
      boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
      zIndex: 1000,
      maxHeight: '80vh',
      overflowY: 'auto',
      minWidth: '500px'
    }}>
      <h3>Advanced Node Configuration: {localData.label}</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Node Function Name:
        </label>
        <input
          type="text"
          value={localData.nodeFunction || ''}
          onChange={(e) => handleChange('nodeFunction', e.target.value)}
          style={{ width: '100%', padding: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Error Handler:
        </label>
        <input
          type="text"
          value={localData.errorHandler || ''}
          onChange={(e) => handleChange('errorHandler', e.target.value)}
          style={{ width: '100%', padding: '5px' }}
        />
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          State Updates:
        </label>
        {Object.entries(localData.stateUpdates || {}).map(([key, value]) => (
          <div key={key} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
            <input
              type="text"
              value={key}
              onChange={(e) => {
                const newKey = e.target.value;
                const newStateUpdates = { ...localData.stateUpdates };
                delete newStateUpdates[key];
                newStateUpdates[newKey] = value;
                handleChange('stateUpdates', newStateUpdates);
              }}
              style={{ flex: 1, marginRight: '5px', padding: '3px' }}
            />
            <input
              type="text"
              value={typeof value === 'object' ? JSON.stringify(value) : String(value)}
              onChange={(e) => handleStateUpdateChange(key, e.target.value)}
              style={{ flex: 1, marginRight: '5px', padding: '3px' }}
            />
          </div>
        ))}
        <button 
          onClick={() => {
            const newStateUpdates = { ...localData.stateUpdates, 'new_field': 'default_value' };
            handleChange('stateUpdates', newStateUpdates);
          }}
          style={{ marginTop: '5px' }}
        >
          Add State Field
        </button>
      </div>
      
      <div style={{ marginBottom: '15px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          Conditional Edges:
        </label>
        {(localData.conditionalEdges || []).map((edge, index) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: '5px' }}>
            <input
              type="text"
              placeholder="Condition"
              value={edge.condition}
              onChange={(e) => handleConditionalEdgeChange(index, 'condition', e.target.value)}
              style={{ flex: 1, marginRight: '5px', padding: '3px' }}
            />
            <input
              type="text"
              placeholder="Target Node"
              value={edge.target}
              onChange={(e) => handleConditionalEdgeChange(index, 'target', e.target.value)}
              style={{ flex: 1, marginRight: '5px', padding: '3px' }}
            />
            <button onClick={() => handleRemoveConditionalEdge(index)}>Remove</button>
          </div>
        ))}
        <button onClick={handleAddConditionalEdge}>Add Conditional Edge</button>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
        <button onClick={handleSave} style={{ backgroundColor: '#4CAF50', color: 'white', padding: '10px 20px' }}>
          Save
        </button>
        <button onClick={onClose} style={{ backgroundColor: '#f44336', color: 'white', padding: '10px 20px' }}>
          Cancel
        </button>
      </div>
    </div>
  );
};

export default AdvancedNodeConfig;