from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent  # Go up two levels to reach the project root
sys.path.insert(0, str(project_root))

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://192.168.51.138:3000", "http://*:3000"])  # Enable CORS for React dev server

@app.route('/api/workflow/current', methods=['GET'])
def get_current_workflow():
    """Get the current workflow from the LangGraph agent."""
    try:
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph

        # Create the graph
        graph = create_enhanced_agent_graph()

        # Get nodes and edges
        graph_structure = graph.get_graph()
        nodes = list(graph_structure.nodes)
        edges = list(graph_structure.edges)

        # Create positions for nodes in a more readable layout
        positions = {}
        x_pos = 0
        y_pos = 0
        row_height = 200  # Increased to account for larger nodes
        col_width = 350   # Increased to account for larger nodes

        # Arrange nodes in a logical flow
        main_flow = ['__start__', 'get_schema', 'check_rag_applicability', 'discover_services',
                     'query_mcp_services', 'generate_sql', 'validate_sql', 'execute_sql',
                     'generate_prompt', 'generate_response', '__end__']

        rag_flow = ['retrieve_documents', 'augment_context', 'generate_rag_response']

        # Position main flow nodes horizontally
        for i, node in enumerate(main_flow):
            if node in nodes:
                positions[node] = {'x': i * col_width, 'y': 0}

        # Position RAG nodes below the main flow with better vertical spacing
        for i, node in enumerate(rag_flow):
            if node in nodes:
                # Add more vertical spacing between RAG nodes to prevent overlap
                positions[node] = {'x': (main_flow.index('check_rag_applicability') if 'check_rag_applicability' in main_flow else 2) * col_width, 'y': (i + 1) * row_height * 2.5}  # Increased vertical spacing significantly

        # Position other nodes with better spacing to avoid overlaps
        y_offset = 6 * row_height  # Increased to account for greater RAG node spacing
        other_nodes = [node for node in nodes if node not in main_flow and node not in rag_flow and node not in ['__start__', '__end__']]

        # Calculate grid dimensions based on number of nodes to minimize overlaps
        num_other_nodes = len(other_nodes)
        if num_other_nodes > 0:
            cols = max(6, int(num_other_nodes ** 0.5) + 1)  # At least 6 columns or based on square root
            for i, node in enumerate(other_nodes):
                if node not in positions:
                    x_pos = (i % cols) * col_width
                    y_pos = y_offset + (i // cols) * row_height * 1.5  # Increased spacing between rows
                    positions[node] = {'x': x_pos, 'y': y_pos}

        # Generate nodes in React Flow format
        react_nodes = []
        for node_id in nodes:
            if node_id in positions:
                position = positions[node_id]
            else:
                position = {'x': 0, 'y': 0}

            # Map node types
            type_mapping = {
                '__start__': 'start',
                '__end__': 'end',
                'get_schema': 'database',
                'discover_services': 'mcp',
                'query_mcp_services': 'mcp',
                'check_rag_applicability': 'rag',
                'retrieve_documents': 'rag',
                'augment_context': 'rag',
                'generate_rag_response': 'rag',
                'generate_sql': 'llm_calling',
                'validate_sql': 'llm_calling',
                'execute_sql': 'database',
                'refine_sql': 'llm_calling',
                'generate_wider_search_query': 'llm_calling',
                'execute_wider_search': 'llm_calling',
                'generate_prompt': 'llm_calling',
                'generate_response': 'llm_calling',
                'execute_mcp_tool_calls_and_return': 'mcp',
                'return_mcp_response_to_llm': 'mcp',
                'await_mcp_response': 'mcp',
                'security_check_after_refinement': 'llm_calling'
            }

            node_type = type_mapping.get(node_id, 'default')

            # Get node descriptions
            descriptions = {
                '__start__': 'Starting point of the workflow. Initiates the process.',
                '__end__': 'Terminal point of the workflow. Represents the completion of the process.',
                'get_schema': 'Retrieves database schema from all available databases.',
                'discover_services': 'Discovers available MCP services from the registry.',
                'query_mcp_services': 'Queries discovered MCP services for information.',
                'check_rag_applicability': 'Checks if RAG (Retrieval-Augmented Generation) is applicable for the request.',
                'retrieve_documents': 'Retrieves relevant documents using the RAG component.',
                'augment_context': 'Augments the user request with retrieved documents for RAG.',
                'generate_rag_response': 'Generates a response using the RAG-augmented context.',
                'generate_sql': 'Generates SQL query based on the user request and available schema information.',
                'validate_sql': 'Validates the generated SQL for safety and correctness.',
                'execute_sql': 'Executes the validated SQL query against the databases and processes the results.',
                'refine_sql': 'Refines SQL query based on validation feedback.',
                'generate_wider_search_query': 'Generates a wider search query when initial results are insufficient.',
                'execute_wider_search': 'Executes the wider search query.',
                'generate_prompt': 'Generates a specialized prompt for the response generation step.',
                'generate_response': 'Generates the final human-readable response based on query results and context.',
                'execute_mcp_tool_calls_and_return': 'Executes MCP tool calls and returns results.',
                'return_mcp_response_to_llm': 'Returns MCP response directly to LLM for further processing.',
                'await_mcp_response': 'Awaits the response from LLM after MCP results have been processed.',
                'security_check_after_refinement': 'Performs security check on refined SQL query.'
            }

            description = descriptions.get(node_id, f'Node: {node_id}')

            # Get node styles
            styles = {
                'start': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#d5f5e3',  # Light green
                    'borderRadius': '50%',
                    'width': '120px',
                    'height': '120px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'fontWeight': 'bold'
                },
                'end': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#f1948a',  # Red
                    'borderRadius': '50%',
                    'width': '120px',
                    'height': '120px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center',
                    'fontWeight': 'bold'
                },
                'database': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#d6eaf8',  # Blue
                    'borderRadius': '8px',
                    'width': '200px',
                    'height': '100px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                'llm_calling': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#fadbd8',  # Pink
                    'borderRadius': '8px',
                    'width': '200px',
                    'height': '100px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                'mcp': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#d2b4de',  # Purple
                    'borderRadius': '8px',
                    'width': '200px',
                    'height': '100px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                'rag': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#85c1e9',  # Light blue
                    'borderRadius': '8px',
                    'width': '200px',
                    'height': '100px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                },
                'default': {
                    'border': '1px solid #555',
                    'padding': '15px',
                    'background': '#ffffff',  # White
                    'borderRadius': '8px',
                    'width': '200px',
                    'height': '100px',
                    'display': 'flex',
                    'alignItems': 'center',
                    'justifyContent': 'center'
                }
            }

            # Extract actual logic from the node function
            logic_description = extract_node_logic_description(node_id)

            # Determine next nodes based on edges
            next_nodes = [edge[1] for edge in edges if edge[0] == node_id]
            next_nodes_str = ', '.join(next_nodes) if next_nodes else ''

            # Determine conditional logic based on conditional edges
            conditional_logic = extract_conditional_logic(node_id, edges)

            node_data = {
                'id': node_id,
                'position': position,
                'data': {
                    'label': node_id.replace('_', ' ').title(),
                    'type': node_type,
                    'description': description,
                    'editable': node_id not in ['__start__', '__end__'],  # Start/end nodes not editable
                    'logic': logic_description,
                    'nodeFunction': f'{node_id}',  # Assuming function name pattern
                    'nextNode': next_nodes_str,
                    'conditionalLogic': conditional_logic
                },
                'type': 'default',
                'style': styles.get(node_type, styles['default'])
            }

            react_nodes.append(node_data)

        # Generate edges in React Flow format
        react_edges = []
        for edge in edges:
            source = edge[0]  # Source node
            target = edge[1]  # Target node
            edge_data = {
                'id': f'e_{source}_{target}',
                'source': source,
                'target': target,
                'animated': True
            }

            react_edges.append(edge_data)

        return jsonify({
            'nodes': react_nodes,
            'edges': react_edges,
            'status': 'success',
            'message': f'Current workflow with {len(nodes)} nodes and {len(edges)} edges'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Helper function to extract logic from node functions
def extract_node_logic_description(node_id):
    """Extract a description of the node's logic from the actual implementation."""
    try:
        # Import the langgraph agent to access node functions
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph

        # Get the graph to access node functions
        graph = create_enhanced_agent_graph()

        # Get the node function from the graph
        if node_id in graph.nodes:
            node_func = graph.nodes[node_id].func
            # Get the docstring of the function
            docstring = getattr(node_func, '__doc__', '')
            if docstring:
                # Clean up the docstring
                docstring = docstring.strip().split('\n')[0]  # Take just the first line
                return docstring
            else:
                return f"Logic for {node_id} node"
        else:
            return f"Logic for {node_id} node"
    except Exception:
        # Fallback logic if we can't extract from the function
        logic_descriptions = {
            '__start__': 'Initialize the workflow with user request',
            '__end__': 'Complete the workflow and return the final response',
            'get_schema': 'Retrieve database schemas from all connected databases',
            'discover_services': 'Discover available MCP services from the registry',
            'query_mcp_services': 'Query MCP services for relevant information',
            'check_rag_applicability': 'Determine if RAG approach is appropriate for the request',
            'retrieve_documents': 'Retrieve relevant documents using RAG component',
            'augment_context': 'Augment user request with retrieved documents',
            'generate_rag_response': 'Generate response using RAG-augmented context',
            'generate_sql': 'Generate SQL query based on user request and schema',
            'validate_sql': 'Validate SQL for safety and correctness',
            'execute_sql': 'Execute validated SQL query against databases',
            'refine_sql': 'Refine SQL query based on validation feedback',
            'generate_wider_search_query': 'Generate broader search query when needed',
            'execute_wider_search': 'Execute wider search query',
            'generate_prompt': 'Generate specialized prompt for response generation',
            'generate_response': 'Generate final human-readable response',
            'execute_mcp_tool_calls_and_return': 'Execute MCP tool calls and return results',
            'return_mcp_response_to_llm': 'Return MCP response directly to LLM',
            'await_mcp_response': 'Wait for response from LLM after MCP processing',
            'security_check_after_refinement': 'Perform security check on refined SQL',
        }
        return logic_descriptions.get(node_id, f"Logic for {node_id} node")

# Helper function to extract conditional logic
def extract_conditional_logic(node_id, edges):
    """Extract conditional logic information for the node."""
    # This is a simplified version - in a real implementation, you'd need to
    # inspect the actual conditional edge functions
    conditional_logic_map = {
        'check_rag_applicability': 'Condition: Check if RAG is applicable for the request',
        'validate_sql': 'Condition: Validate SQL safety and correctness',
        'execute_sql': 'Condition: Check if SQL execution was successful',
        'generate_wider_search_query': 'Condition: Check if wider search is needed',
    }
    return conditional_logic_map.get(node_id, '')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Workflow API is running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)