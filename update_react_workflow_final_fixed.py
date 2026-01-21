#!/usr/bin/env python3
"""
Final script to update the React app with the current LangGraph workflow.
This script extracts the current workflow from the LangGraph agent and updates the React app's initialNodes and initialEdges.
"""

import json
import re
from pathlib import Path

def get_current_workflow():
    """Get the current workflow from the LangGraph agent."""
    import sys
    import os
    
    # Add the project root to the Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
    
    # Create the graph
    graph = create_enhanced_agent_graph()
    
    # Get nodes and edges
    graph_structure = graph.get_graph()
    nodes = list(graph_structure.nodes)
    edges = list(graph_structure.edges)
    
    return nodes, edges

def map_node_type(node_name):
    """Map node names to visual node types for the React app."""
    # Define mapping from node names to visual types
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
    
    return type_mapping.get(node_name, 'default')

def map_node_description(node_name):
    """Provide descriptions for nodes."""
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
    
    return descriptions.get(node_name, f'Node: {node_name}')

def get_node_style(node_type):
    """Get the style for a node based on its type."""
    styles = {
        'start': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#d5f5e3',  # Light green
            'borderRadius': '50%',
            'width': '80px',
            'height': '80px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'fontWeight': 'bold'
        },
        'end': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#f1948a',  # Red
            'borderRadius': '50%',
            'width': '80px',
            'height': '80px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'fontWeight': 'bold'
        },
        'database': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#d6eaf8',  # Blue
            'borderRadius': '8px',
            'width': '120px',
            'height': '60px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
        'llm_calling': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#fadbd8',  # Pink
            'borderRadius': '8px',
            'width': '120px',
            'height': '60px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
        'mcp': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#d2b4de',  # Purple
            'borderRadius': '8px',
            'width': '120px',
            'height': '60px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
        'rag': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#85c1e9',  # Light blue
            'borderRadius': '8px',
            'width': '120px',
            'height': '60px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        },
        'default': {
            'border': '1px solid #555',
            'padding': '10px',
            'background': '#ffffff',  # White
            'borderRadius': '8px',
            'width': '120px',
            'height': '60px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center'
        }
    }
    
    return styles.get(node_type, styles['default'])

def generate_react_workflow(nodes, edges):
    """Generate React-compatible workflow data."""
    # Create positions for nodes in a more readable layout
    positions = {}
    x_pos = 0
    y_pos = 0
    row_height = 150
    col_width = 250
    
    # Arrange nodes in a logical flow
    main_flow = ['__start__', 'get_schema', 'check_rag_applicability', 'discover_services', 
                 'query_mcp_services', 'generate_sql', 'validate_sql', 'execute_sql', 
                 'generate_prompt', 'generate_response', '__end__']
    
    rag_flow = ['retrieve_documents', 'augment_context', 'generate_rag_response']
    
    # Position main flow nodes horizontally
    for i, node in enumerate(main_flow):
        if node in nodes:
            positions[node] = {'x': i * col_width, 'y': 0}
    
    # Position RAG nodes below the main flow
    for i, node in enumerate(rag_flow):
        if node in nodes:
            positions[node] = {'x': (main_flow.index('check_rag_applicability') if 'check_rag_applicability' in main_flow else 2) * col_width, 'y': (i + 1) * row_height}
    
    # Position other nodes
    y_offset = 2 * row_height
    other_nodes = [node for node in nodes if node not in main_flow and node not in rag_flow and node not in ['__start__', '__end__']]
    for i, node in enumerate(other_nodes):
        if node not in positions:
            positions[node] = {'x': (i % 6) * col_width, 'y': y_offset + (i // 6) * row_height}
    
    # Generate initialNodes array
    initial_nodes = []
    for node_id in nodes:
        if node_id in positions:
            position = positions[node_id]
        else:
            position = {'x': 0, 'y': 0}
        
        node_data = {
            'id': node_id,
            'position': position,
            'data': {
                'label': node_id.replace('_', ' ').title(),
                'type': map_node_type(node_id),
                'description': map_node_description(node_id),
                'editable': node_id not in ['__start__', '__end__'],  # Start/end nodes not editable
                'logic': '',  # Will be filled based on actual node implementation
                'nodeFunction': f'{node_id}',
                'nextNode': '',  # Will be determined by edges
                'conditionalLogic': ''
            },
            'type': 'default',
            'style': get_node_style(map_node_type(node_id))
        }

        initial_nodes.append(node_data)
    
    # Generate initialEdges array
    initial_edges = []
    for edge in edges:
        source = edge[0]  # Source node
        target = edge[1]  # Target node
        edge_data = {
            'id': f'e_{source}_{target}',
            'source': source,
            'target': target,
            'animated': True
        }
        
        initial_edges.append(edge_data)
    
    return initial_nodes, initial_edges

def update_react_app(nodes, edges):
    """Update the React app with the current workflow."""
    # Generate the new initialNodes and initialEdges
    initial_nodes, initial_edges = generate_react_workflow(nodes, edges)
    
    # Convert to JavaScript format (with proper indentation)
    nodes_js = json.dumps(initial_nodes, indent=2)
    edges_js = json.dumps(initial_edges, indent=2)
    
    # Read the current App.js file
    app_file_path = Path(__file__).parent / "gui/react_editor/src/App.js"
    with open(app_file_path, 'r') as f:
        content = f.read()
    
    # Replace the initialNodes and initialEdges definitions
    # Use regex to find and replace the initialNodes and initialEdges arrays
    import re
    
    # First, let's find and replace the initialNodes definition
    pattern_nodes = r'(const initialNodes = )\[([^\]]*?)\];(?=\n\s*(?:export|const|let|var|function|class|#))'
    if re.search(pattern_nodes, content, re.DOTALL):
        content = re.sub(pattern_nodes, f'const initialNodes = {nodes_js};', content, count=1, flags=re.DOTALL)
    else:
        # If the pattern doesn't match, try a simpler approach
        # Find the initialNodes assignment and replace it
        lines = content.split('\n')
        new_lines = []
        in_initial_nodes = False
        nodes_replaced = False
        
        for line in lines:
            if line.strip().startswith('const initialNodes = ['):
                in_initial_nodes = True
                if not nodes_replaced:
                    new_lines.append(f'const initialNodes = {nodes_js};')
                    nodes_replaced = True
            elif in_initial_nodes and line.strip() == '];':
                in_initial_nodes = False
                # Skip this line since we already added the new one
            elif not in_initial_nodes:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    # Do the same for initialEdges
    lines = content.split('\n')
    new_lines = []
    in_initial_edges = False
    edges_replaced = False
    
    for line in lines:
        if line.strip().startswith('const initialEdges = ['):
            in_initial_edges = True
            if not edges_replaced:
                new_lines.append(f'const initialEdges = {edges_js};')
                edges_replaced = True
        elif in_initial_edges and line.strip() == '];':
            in_initial_edges = False
            # Skip this line since we already added the new one
        elif not in_initial_edges:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Write the updated content back to the file
    with open(app_file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated React app with {len(nodes)} nodes and {len(edges)} edges")
    print("RAG nodes included:", [node for node in nodes if 'rag' in node.lower() or 'document' in node.lower() or 'context' in node.lower() or 'retrieve' in node.lower()])

def main():
    print("Updating React app with current LangGraph workflow...")

    try:
        nodes, edges = get_current_workflow()
        print(f"Current workflow has {len(nodes)} nodes and {len(edges)} edges")
        print("Nodes:", nodes)

        update_react_app(nodes, edges)
        print("React app updated successfully!")

    except Exception as e:
        print(f"Error updating React app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()