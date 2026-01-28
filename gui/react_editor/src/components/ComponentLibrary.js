import React, { useState } from 'react';
import './ComponentLibrary.css';

// Define the available LangGraph components
const LANGGRAPH_COMPONENTS = [
  {
    id: 'start_node',
    name: 'Start Node',
    category: 'Special',
    description: 'Initial node of the workflow',
    icon: '▶️',
    nodeType: 'start',
    data: {
      label: 'Start Node',
      type: 'start',
      description: 'Starting point of the workflow. Initiates the process.',
      editable: false,
      logic: 'Initialize the workflow with user request',
      nodeFunction: '__start__',
      nextNode: 'initialize_agent_state',
      conditionalLogic: '',
      stateUpdates: {},
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'end_node',
    name: 'End Node',
    category: 'Special',
    description: 'Terminal node of the workflow',
    icon: '⏹️',
    nodeType: 'end',
    data: {
      label: 'End Node',
      type: 'end',
      description: 'Terminal point of the workflow. Represents the completion of the process.',
      editable: false,
      logic: 'Complete the workflow and return the final response',
      nodeFunction: '__end__',
      nextNode: '',
      conditionalLogic: '',
      stateUpdates: {},
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'initialize_agent_state',
    name: 'Initialize Agent State',
    category: 'Core',
    description: 'Initializes the agent state with default values',
    icon: 'InitStruct',
    nodeType: 'llm_calling',
    data: {
      label: 'Initialize Agent State',
      type: 'llm_calling',
      description: 'Initializes the agent state with default values.',
      editable: true,
      logic: 'Initialize the agent state with default values',
      nodeFunction: 'initialize_agent_state',
      nextNode: 'discover_services',
      conditionalLogic: '',
      stateUpdates: {
        user_request: 'state["user_request"]',
        mcp_queries: '[]',
        mcp_results: '[]',
        synthesized_result: '""',
        can_answer: 'False',
        iteration_count: '0',
        max_iterations: '3',
        final_answer: '""',
        error_message: 'None'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'discover_services',
    name: 'Discover Services',
    category: 'MCP',
    description: 'Discovers available MCP services from the registry',
    icon: '🔍',
    nodeType: 'mcp',
    data: {
      label: 'Discover Services',
      type: 'mcp',
      description: 'Discovers available MCP services from the registry.',
      editable: true,
      logic: 'Discover available MCP services',
      nodeFunction: 'discover_services',
      nextNode: 'analyze_request',
      conditionalLogic: '',
      stateUpdates: {
        mcp_servers: 'discovered_services',
        discovered_services: 'discovered_services'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'analyze_request',
    name: 'Analyze Request',
    category: 'Core',
    description: 'Analyzes the user request to determine how to proceed',
    icon: '🤔',
    nodeType: 'llm_calling',
    data: {
      label: 'Analyze Request',
      type: 'llm_calling',
      description: 'Analyzes the user request to determine how to proceed.',
      editable: true,
      logic: 'Analyze the user request to determine how to proceed',
      nodeFunction: 'analyze_request',
      nextNode: 'check_mcp_applicability',
      conditionalLogic: '',
      stateUpdates: {
        mcp_queries: 'suggested_queries',
        mcp_tool_calls: 'filtered_tool_calls',
        is_final_answer: 'analysis_result.get("is_final_answer", False)'
      },
      conditionalEdges: [
        {
          condition: 'no MCP tool calls generated and is_final_answer=True',
          target: 'generate_final_answer_from_analysis'
        },
        {
          condition: 'no MCP tool calls generated and is_final_answer=False',
          target: 'generate_failure_response_from_analysis'
        },
        {
          condition: 'MCP tool calls generated',
          target: 'check_mcp_applicability'
        }
      ],
      errorHandler: ''
    }
  },
  {
    id: 'plan_mcp_queries',
    name: 'Plan MCP Queries',
    category: 'MCP',
    description: 'Plans MCP queries based on the analyzed request',
    icon: '📋',
    nodeType: 'mcp',
    data: {
      label: 'Plan MCP Queries',
      type: 'mcp',
      description: 'Plans MCP queries based on the analyzed request.',
      editable: true,
      logic: 'Plan MCP queries based on the analyzed request',
      nodeFunction: 'plan_mcp_queries',
      nextNode: 'execute_mcp_queries',
      conditionalLogic: '',
      stateUpdates: {
        mcp_queries: 'planned_queries'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'execute_mcp_queries',
    name: 'Execute MCP Queries',
    category: 'MCP',
    description: 'Executes MCP queries in parallel or sequentially',
    icon: '⚡',
    nodeType: 'mcp',
    data: {
      label: 'Execute MCP Queries',
      type: 'mcp',
      description: 'Executes MCP queries in parallel or sequentially.',
      editable: true,
      logic: 'Execute MCP queries in parallel or sequentially',
      nodeFunction: 'execute_mcp_queries',
      nextNode: 'synthesize_results',
      conditionalLogic: '',
      stateUpdates: {
        mcp_results: 'results',
        error_message: 'None'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'synthesize_results',
    name: 'Synthesize Results',
    category: 'Core',
    description: 'Synthesizes results from multiple MCP queries',
    icon: '📊',
    nodeType: 'llm_calling',
    data: {
      label: 'Synthesize Results',
      type: 'llm_calling',
      description: 'Synthesizes results from multiple MCP queries.',
      editable: true,
      logic: 'Synthesize results from multiple MCP queries',
      nodeFunction: 'synthesize_results',
      nextNode: 'can_answer',
      conditionalLogic: '',
      stateUpdates: {
        synthesized_result: 'synthesized_result'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'can_answer',
    name: 'Can Answer',
    category: 'Core',
    description: 'Determines if the agent can answer the user\'s request',
    icon: '❓',
    nodeType: 'llm_calling',
    data: {
      label: 'Can Answer',
      type: 'llm_calling',
      description: 'Determines if the agent can answer the user\'s request.',
      editable: true,
      logic: 'Determine if the agent can answer the user\'s request',
      nodeFunction: 'can_answer',
      nextNode: 'generate_final_answer, plan_refined_queries, generate_failure_response',
      conditionalLogic: 'Condition: Check if the agent can answer the user\'s request',
      stateUpdates: {
        can_answer: 'can_answer'
      },
      conditionalEdges: [
        {
          condition: 'state["can_answer"]',
          target: 'generate_final_answer'
        },
        {
          condition: 'state["iteration_count"] < state["max_iterations"]',
          target: 'plan_refined_queries'
        },
        {
          condition: 'otherwise',
          target: 'generate_failure_response'
        }
      ],
      errorHandler: ''
    }
  },
  {
    id: 'generate_final_answer',
    name: 'Generate Final Answer',
    category: 'Core',
    description: 'Generates the final answer based on synthesized results',
    icon: '✅',
    nodeType: 'llm_calling',
    data: {
      label: 'Generate Final Answer',
      type: 'llm_calling',
      description: 'Generates the final answer based on synthesized results.',
      editable: true,
      logic: 'Generate the final answer based on synthesized results',
      nodeFunction: 'generate_final_answer',
      nextNode: '__end__',
      conditionalLogic: '',
      stateUpdates: {
        final_answer: 'final_answer'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'plan_refined_queries',
    name: 'Plan Refined Queries',
    category: 'Core',
    description: 'Plans refined queries for the next iteration',
    icon: '🔄',
    nodeType: 'llm_calling',
    data: {
      label: 'Plan Refined Queries',
      type: 'llm_calling',
      description: 'Plans refined queries for the next iteration.',
      editable: true,
      logic: 'Plan refined queries for the next iteration',
      nodeFunction: 'plan_refined_queries',
      nextNode: 'execute_mcp_queries',
      conditionalLogic: '',
      stateUpdates: {
        refined_queries: 'refined_queries',
        iteration_count: 'state["iteration_count"] + 1'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  },
  {
    id: 'generate_failure_response',
    name: 'Generate Failure Response',
    category: 'Core',
    description: 'Generates a failure response when iterations are exhausted',
    icon: '❌',
    nodeType: 'end',
    data: {
      label: 'Generate Failure Response',
      type: 'end',
      description: 'Generates a failure response when iterations are exhausted.',
      editable: true,
      logic: 'Generate a failure response when iterations are exhausted',
      nodeFunction: 'generate_failure_response',
      nextNode: '__end__',
      conditionalLogic: '',
      stateUpdates: {
        final_answer: 'final_answer',
        failure_reason: 'failure_reason'
      },
      conditionalEdges: [],
      errorHandler: ''
    }
  }
];

const ComponentLibrary = ({ onDragStart }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  // Get unique categories
  const categories = ['All', ...new Set(LANGGRAPH_COMPONENTS.map(comp => comp.category))];

  // Filter components based on search and category
  const filteredComponents = LANGGRAPH_COMPONENTS.filter(component => {
    const matchesSearch = component.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         component.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || component.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="component-library">
      <h3>Component Library</h3>
      
      <div className="library-controls">
        <input
          type="text"
          placeholder="Search components..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="category-select"
        >
          {categories.map(category => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
      </div>
      
      <div className="components-grid">
        {filteredComponents.map(component => (
          <div
            key={component.id}
            className="component-item"
            draggable
            onDragStart={(e) => onDragStart(e, component)}
          >
            <div className="component-icon">{component.icon}</div>
            <div className="component-info">
              <h4>{component.name}</h4>
              <p>{component.description}</p>
              <span className="component-category">{component.category}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ComponentLibrary;