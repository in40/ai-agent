import streamlit as st
import json
import tempfile
import os
from pathlib import Path
import graphviz
import time

# Add the project root to the Python path
import sys
sys.path.insert(0, '/root/qwen_test/ai_agent')

from langgraph_agent.langgraph_agent import create_enhanced_agent_graph, AgentState, run_enhanced_agent
from langgraph.graph import StateGraph

# Import the state visualizer
from state_visualizer import StateVisualizer, visualize_state, visualize_state_transitions

# Import the debugger
from debugger import WorkflowDebugger, wrap_graph_for_debugging

# Set page config
st.set_page_config(
    page_title="Enhanced LangGraph Editor",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Enhanced LangGraph Visual Editor")
st.markdown("""
This tool allows you to visualize, edit, and interact with the LangGraph workflow.
""")

# Initialize session state for workflow editing
if 'workflow_nodes' not in st.session_state:
    graph = create_enhanced_agent_graph()
    g = graph.get_graph()
    
    # Extract nodes and edges from the graph
    nodes = {}
    for node_name in g.nodes:
        nodes[node_name] = {
            'id': node_name,
            'label': node_name,
            'x': 0,  # Will be set by layout algorithm
            'y': 0,  # Will be set by layout algorithm
            'type': 'default'
        }
    
    edges = []
    for edge in g.edges:
        edges.append({
            'source': edge.source,
            'target': edge.target,
            'condition': getattr(edge, 'condition', None)  # Conditional edges may have conditions
        })
    
    st.session_state.workflow_nodes = nodes
    st.session_state.workflow_edges = edges

# Initialize state visualizer in session state
if 'state_visualizer' not in st.session_state:
    st.session_state.state_visualizer = StateVisualizer()

# Initialize debugger in session state
if 'debugger' not in st.session_state:
    graph = create_enhanced_agent_graph()
    st.session_state.debugger = WorkflowDebugger(graph)

# Create tabs for different views
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Visualization", "Edit Workflow", "Workflow Details", "Run Simulation", "Debugging", "Export/Import"])

with tab1:
    st.header("Graph Visualization")
    
    # Create the graph
    graph = create_enhanced_agent_graph()
    g = graph.get_graph()

    # Display the mermaid diagram using graphviz
    mermaid_code = g.draw_mermaid()

    # Extract the nodes and edges from the mermaid code
    lines = mermaid_code.split('\n')
    dot_lines = ['digraph G {', 'rankdir=TB;']

    # Define node categories for styling
    start_nodes = set(['__start__'])
    end_nodes = set(['__end__'])
    database_nodes = set(['get_schema', 'generate_sql', 'validate_sql', 'execute_sql', 'refine_sql', 'generate_wider_search_query', 'execute_wider_search', 'security_check_after_refinement'])
    mcp_nodes = set(['discover_services', 'query_mcp_services', 'execute_mcp_tool_calls_and_return', 'return_mcp_response_to_llm', 'await_mcp_response'])
    response_nodes = set(['generate_prompt', 'generate_response'])

    # First, collect all node IDs to define them in the graph
    node_definitions = {}
    for line in lines:
        line_stripped = line.strip()
        # Skip mermaid-specific directives
        if line_stripped.startswith('%%{init:') or line_stripped.startswith('graph ') or line_stripped.startswith('classDef'):
            continue
        # Handle node definitions (format: \tnodeId(label) or \tnodeId[label]:::style)
        elif line.startswith('\t') and ('(' in line or '[' in line) and (';' not in line_stripped or line_stripped.count('(') > line_stripped.count(');')):
            # Extract node ID and label - handle both (label) and [label] formats
            if '(' in line:
                # Format like: \tget_schema(get_schema)
                node_part = line.split('(')
                node_id = node_part[0].strip().lstrip('\t')  # Remove leading tab and whitespace
                label_part = node_part[1].split(')')[0] if ')' in node_part[1] else node_part[1]
            elif '[' in line:
                # Format like: \t__start__([<p>__start__</p>]):::first
                node_part = line.split('[')
                node_id = node_part[0].strip().lstrip('\t')  # Remove leading tab and whitespace
                label_part = node_part[1].split(']')[0] if ']' in node_part[1] else node_part[1]

            # Clean up the label by removing HTML tags and styling info
            clean_label = label_part.replace('<p>', '').replace('</p>', '').replace(':::first', '').replace(':::last', '').replace(':::default', '')
            node_definitions[node_id] = clean_label

    # Define LLM calling nodes for special styling
    llm_calling_nodes = set(['generate_sql', 'validate_sql', 'refine_sql', 'generate_wider_search_query', 'generate_prompt', 'generate_response', 'return_mcp_response_to_llm', 'security_check_after_refinement', 'query_mcp_services'])

    # Add all node definitions to the DOT code with appropriate styling
    for node_id, label in node_definitions.items():
        if node_id in start_nodes:
            dot_lines.append(f'{node_id} [label="{label}", shape=ellipse, fillcolor=lightgreen, style=filled];')
        elif node_id in end_nodes:
            dot_lines.append(f'{node_id} [label="{label}", shape=ellipse, fillcolor=red, style=filled];')
        elif node_id in database_nodes:
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=lightblue, style=filled];')
        elif node_id in mcp_nodes and node_id not in llm_calling_nodes:
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=orange, style=filled];')
        elif node_id in mcp_nodes and node_id in llm_calling_nodes:
            # Special case: node is both MCP and calls LLMs - prioritize LLM indicator
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=pink, style=filled];')
        elif node_id in response_nodes:
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=yellow, style=filled];')
        elif node_id in llm_calling_nodes:
            # Add special styling for nodes that call LLMs
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=pink, style=filled];')
        else:
            dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=white, style=filled];')

    # Process edges
    for line in lines:
        line_stripped = line.strip()
        # Skip mermaid-specific directives and class definitions
        if line_stripped.startswith('%%{init:') or line_stripped.startswith('graph ') or line_stripped.startswith('classDef'):
            continue
        # Skip node definitions (they start with tab)
        if line.startswith('\t') and ('(' in line or '[' in line):
            continue
        # Handle edge definitions (format: start --> end; or start -. condition .-> end;)
        elif '-->' in line_stripped or '-.' in line_stripped:
            # Handle conditional edges (which use -. condition .-> syntax)
            if '-.' in line_stripped:
                # Split on the conditional arrow pattern
                parts = line_stripped.split(' -. ')
                if len(parts) >= 2:
                    start = parts[0].strip()
                    # Extract the condition and end node
                    condition_and_end = parts[1]
                    condition_part = condition_and_end.split(' .-> ')
                    if len(condition_part) >= 2:
                        condition = condition_part[0].strip()
                        end = condition_part[1].replace(';', '').strip()

                        # Decode HTML entities in condition
                        condition = condition.replace('&nbsp;', ' ')

                        # Enhance condition descriptions for better understanding
                        enhanced_condition = condition

                        # Handle special cases for different nodes
                        if start == "query_mcp_services":
                            # Provide more detailed descriptions for the query_mcp_services node
                            # These edges have None as data in the actual graph but no labels in mermaid
                            # So we'll enhance the generic "None" condition
                            if condition == "None":
                                # This is one of the unlabeled edges from query_mcp_services
                                if end == "execute_mcp_tool_calls_and_return":
                                    enhanced_condition = "execute_mcp_tool_calls\\n(databases disabled &\\nMCP tool calls exist)"
                                elif end == "generate_prompt":
                                    enhanced_condition = "generate_prompt\\n(databases disabled &\\nMCP results sufficient)"
                                elif end == "generate_sql":
                                    enhanced_condition = "generate_sql\\n(databases enabled)"
                                elif end == "return_mcp_response_to_llm":
                                    enhanced_condition = "return_to_llm\\n(MCP call initiated by LLM\\nwith results)"
                        elif start == "get_schema" and condition == "continue_with_dbs":
                            enhanced_condition = "continue_with_dbs\\n(databases enabled)"
                        elif start == "execute_mcp_tool_calls_and_return":
                            if condition == "to_user":
                                enhanced_condition = "to_user\\n(return results to user)"
                            elif condition == "to_llm_for_processing":
                                enhanced_condition = "to_llm_for_processing\\n(return results to LLM)"
                        elif start == "execute_sql":
                            if condition == "respond":
                                enhanced_condition = "respond\\n(results found)"
                            elif condition == "wider_search":
                                enhanced_condition = "wider_search\\n(no results, try wider search)"
                        elif start == "execute_wider_search":
                            if condition == "respond":
                                enhanced_condition = "respond\\n(results found)"
                            elif condition == "wider_search":
                                enhanced_condition = "wider_search\\n(still no results, continue search)"
                        elif start == "refine_sql":
                            if condition == "respond":
                                enhanced_condition = "respond\\n(validation passed)"
                            elif condition == "refine":
                                enhanced_condition = "refine\\n(validation failed, refine again)"
                        elif start == "security_check_after_refinement":
                            if condition == "respond":
                                enhanced_condition = "respond\\n(validation passed)"
                            elif condition == "refine":
                                enhanced_condition = "refine\\n(validation failed, refine again)"
                        elif start == "validate_sql":
                            enhanced_condition = "validation result\\n(check safety & correctness)"
                        elif condition == "None":
                            # Handle other edges that have None as data value
                            enhanced_condition = "conditional\\n(multiple possible paths)"
                        else:
                            # For other conditions, add more descriptive text
                            if condition == "skip_to_final":
                                enhanced_condition = "skip_to_final\\n(databases disabled &\\nprompt/response gen disabled)"
                            elif condition == "continue_with_dbs":
                                enhanced_condition = "continue_with_dbs\\n(databases enabled)"
                            elif condition == "to_user":
                                enhanced_condition = "to_user\\n(return results to user)"
                            elif condition == "to_llm_for_processing":
                                enhanced_condition = "to_llm_for_processing\\n(return results to LLM)"
                            elif condition == "respond":
                                enhanced_condition = "respond\\n(results found)"
                            elif condition == "wider_search":
                                enhanced_condition = "wider_search\\n(no results, try wider search)"
                            elif condition == "refine":
                                enhanced_condition = "refine\\n(validation failed, refine again)"

                        # Add the edge with enhanced condition as label
                        dot_lines.append(f'{start} -> {end} [label="{enhanced_condition}", style=dashed, color=red];')
            # Handle regular edges (which use --> syntax)
            elif '-->' in line_stripped:
                parts = line_stripped.replace('-->', '->').replace(';', '').strip()
                dot_lines.append(parts + ';')

    # Add decision point annotations as special nodes
    dot_lines.append('decision_note [shape=note, label="Decision Logic:\\n- Databases enabled/disabled?\\n- MCP services available?\\n- Results found?", fillcolor=lightgray, style=filled];')
    dot_lines.append('query_mcp_services_decision [shape=note, label="Query MCP Services:\\n- Databases disabled &\\n  MCP tool calls exist?\\n- MCP results sufficient?\\n- Databases enabled?", fillcolor=lightgray, style=filled];')
    dot_lines.append('validate_sql_decision [shape=note, label="Validate SQL:\\n- Is query safe?\\n- Should refine?", fillcolor=lightgray, style=filled];')

    # Connect decision nodes to relevant workflow nodes
    dot_lines.append('get_schema -> decision_note [style=dotted, color=blue];')
    dot_lines.append('query_mcp_services -> query_mcp_services_decision [style=dotted, color=blue];')
    dot_lines.append('validate_sql -> validate_sql_decision [style=dotted, color=blue];')

    dot_lines.append('}')
    dot_code = '\n'.join(dot_lines)

    # Create a selection box for users to choose which node to focus on
    all_nodes = list(node_definitions.keys())
    selected_node = st.selectbox("Select a node to explore its paths:", ["None"] + all_nodes, index=0)

    # If a node is selected, create a modified version of the graph highlighting paths from that node
    if selected_node != "None":
        # Create a new DOT code focusing on the selected node
        focused_dot_lines = ['digraph G {', 'rankdir=TB;']

        # Re-add all nodes with original styling
        for node_id, label in node_definitions.items():
            if node_id in start_nodes:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=ellipse, fillcolor=lightgreen, style=filled];')
            elif node_id in end_nodes:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=ellipse, fillcolor=red, style=filled];')
            elif node_id in database_nodes:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=lightblue, style=filled];')
            elif node_id in mcp_nodes and node_id not in llm_calling_nodes:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=orange, style=filled];')
            elif node_id in mcp_nodes and node_id in llm_calling_nodes:
                # Special case: node is both MCP and calls LLMs - prioritize LLM indicator
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=pink, style=filled];')
            elif node_id in response_nodes:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=yellow, style=filled];')
            elif node_id in llm_calling_nodes:
                # Add special styling for nodes that call LLMs
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=pink, style=filled];')
            else:
                focused_dot_lines.append(f'{node_id} [label="{label}", shape=box, fillcolor=white, style=filled];')

        # Highlight the selected node
        if selected_node in start_nodes:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=ellipse, fillcolor=gold, style=filled];')
        elif selected_node in end_nodes:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=ellipse, fillcolor=gold, style=filled];')
        elif selected_node in database_nodes:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=box, fillcolor=gold, style=filled];')
        elif selected_node in mcp_nodes:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=box, fillcolor=gold, style=filled];')
        elif selected_node in response_nodes:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=box, fillcolor=gold, style=filled];')
        else:
            focused_dot_lines.append(f'{selected_node} [label="{node_definitions[selected_node]}", shape=box, fillcolor=gold, style=filled];')

        # Process edges - highlight those connected to the selected node
        for line in lines:
            line_stripped = line.strip()
            # Skip mermaid-specific directives and class definitions
            if line_stripped.startswith('%%{init:') or line_stripped.startswith('graph ') or line_stripped.startswith('classDef'):
                continue
            # Skip node definitions (they start with tab)
            if line.startswith('\t') and ('(' in line or '[' in line):
                continue
            # Handle edge definitions (format: start --> end; or start -. condition .-> end;)
            elif '-->' in line_stripped or '-.' in line_stripped:
                # Handle conditional edges (which use -. condition .-> syntax)
                if '-.' in line_stripped:
                    # Split on the conditional arrow pattern
                    parts = line_stripped.split(' -. ')
                    if len(parts) >= 2:
                        start = parts[0].strip()
                        # Extract the condition and end node
                        condition_and_end = parts[1]
                        condition_part = condition_and_end.split(' .-> ')
                        if len(condition_part) >= 2:
                            condition = condition_part[0].strip()
                            end = condition_part[1].replace(';', '').strip()

                            # Decode HTML entities in condition
                            condition = condition.replace('&nbsp;', ' ')

                            # Enhance condition descriptions for better understanding
                            enhanced_condition = condition

                            # Handle special cases for different nodes
                            if start == "query_mcp_services":
                                # Provide more detailed descriptions for the query_mcp_services node
                                # These edges have None as data in the actual graph but no labels in mermaid
                                # So we'll enhance the generic "None" condition
                                if condition == "None":
                                    # This is one of the unlabeled edges from query_mcp_services
                                    if end == "execute_mcp_tool_calls_and_return":
                                        enhanced_condition = "execute_mcp_tool_calls\\n(databases disabled &\\nMCP tool calls exist)"
                                    elif end == "generate_prompt":
                                        enhanced_condition = "generate_prompt\\n(databases disabled &\\nMCP results sufficient)"
                                    elif end == "generate_sql":
                                        enhanced_condition = "generate_sql\\n(databases enabled)"
                                    elif end == "return_mcp_response_to_llm":
                                        enhanced_condition = "return_to_llm\\n(MCP call initiated by LLM\\nwith results)"
                            elif start == "get_schema" and condition == "continue_with_dbs":
                                enhanced_condition = "continue_with_dbs\\n(databases enabled)"
                            elif start == "execute_mcp_tool_calls_and_return":
                                if condition == "to_user":
                                    enhanced_condition = "to_user\\n(return results to user)"
                                elif condition == "to_llm_for_processing":
                                    enhanced_condition = "to_llm_for_processing\\n(return results to LLM)"
                            elif start == "execute_sql":
                                if condition == "respond":
                                    enhanced_condition = "respond\\n(results found)"
                                elif condition == "wider_search":
                                    enhanced_condition = "wider_search\\n(no results, try wider search)"
                            elif start == "execute_wider_search":
                                if condition == "respond":
                                    enhanced_condition = "respond\\n(results found)"
                                elif condition == "wider_search":
                                    enhanced_condition = "wider_search\\n(still no results, continue search)"
                            elif start == "refine_sql":
                                if condition == "respond":
                                    enhanced_condition = "respond\\n(validation passed)"
                                elif condition == "refine":
                                    enhanced_condition = "refine\\n(validation failed, refine again)"
                            elif start == "security_check_after_refinement":
                                if condition == "respond":
                                    enhanced_condition = "respond\\n(validation passed)"
                                elif condition == "refine":
                                    enhanced_condition = "refine\\n(validation failed, refine again)"
                            elif start == "validate_sql":
                                enhanced_condition = "validation result\\n(check safety & correctness)"
                            elif condition == "None":
                                # Handle other edges that have None as data value
                                enhanced_condition = "conditional\\n(multiple possible paths)"
                            else:
                                # For other conditions, add more descriptive text
                                if condition == "skip_to_final":
                                    enhanced_condition = "skip_to_final\\n(databases disabled &\\nprompt/response gen disabled)"
                                elif condition == "continue_with_dbs":
                                    enhanced_condition = "continue_with_dbs\\n(databases enabled)"
                                elif condition == "to_user":
                                    enhanced_condition = "to_user\\n(return results to user)"
                                elif condition == "to_llm_for_processing":
                                    enhanced_condition = "to_llm_for_processing\\n(return results to LLM)"
                                elif condition == "respond":
                                    enhanced_condition = "respond\\n(results found)"
                                elif condition == "wider_search":
                                    enhanced_condition = "wider_search\\n(no results, try wider search)"
                                elif condition == "refine":
                                    enhanced_condition = "refine\\n(validation failed, refine again)"

                            # Highlight edges coming from or going to the selected node
                            if start == selected_node or end == selected_node:
                                focused_dot_lines.append(f'{start} -> {end} [label="{enhanced_condition}", style=bold, color=purple, penwidth=3];')
                            else:
                                focused_dot_lines.append(f'{start} -> {end} [label="{enhanced_condition}", style=dashed, color=red];')
                # Handle regular edges (which use --> syntax)
                elif '-->' in line_stripped:
                    parts = line_stripped.replace('-->', '->').replace(';', '').strip()
                    start, end = parts.split(' -> ')

                    # Highlight edges coming from or going to the selected node
                    if start == selected_node or end == selected_node:
                        focused_dot_lines.append(f'{parts} [style=bold, color=purple, penwidth=3];')
                    else:
                        focused_dot_lines.append(parts + ';')

        # Add decision point annotations as special nodes
        focused_dot_lines.append('decision_note [shape=note, label="Decision Logic:\\n- Databases enabled/disabled?\\n- MCP services available?\\n- Results found?", fillcolor=lightgray, style=filled];')
        focused_dot_lines.append('query_mcp_services_decision [shape=note, label="Query MCP Services:\\n- Databases disabled &\\n  MCP tool calls exist?\\n- MCP results sufficient?\\n- Databases enabled?", fillcolor=lightgray, style=filled];')
        focused_dot_lines.append('validate_sql_decision [shape=note, label="Validate SQL:\\n- Is query safe?\\n- Should refine?", fillcolor=lightgray, style=filled];')

        # Connect decision nodes to relevant workflow nodes
        focused_dot_lines.append('get_schema -> decision_note [style=dotted, color=blue];')
        focused_dot_lines.append('query_mcp_services -> query_mcp_services_decision [style=dotted, color=blue];')
        focused_dot_lines.append('validate_sql -> validate_sql_decision [style=dotted, color=blue];')

        focused_dot_lines.append('}')
        focused_dot_code = '\n'.join(focused_dot_lines)

        # Render the focused graph
        st.graphviz_chart(focused_dot_code, use_container_width=True)

        # Show information about the selected node
        st.subheader(f"Information about '{selected_node}' node")

        # Define node-specific information
        node_info = {
            "__start__": "Starting point of the workflow. Initiates the process by moving to get_schema node.",
            "get_schema": "Retrieves database schema from all available databases. Checks if databases are disabled and adjusts the workflow accordingly.",
            "discover_services": "Discovers available MCP (Model Context Protocol) services that can assist with the user request.",
            "query_mcp_services": "Queries the discovered MCP services to see if they can provide relevant information for the user's request. **Calls MCP-Capable LLM** to analyze the request and generate appropriate tool calls. This is the most complex decision point in the workflow with multiple possible paths based on system configuration and results:",
            "generate_sql": "Generates SQL query based on the user request and available schema information. **Calls SQL LLM** (configured via SQL_LLM_* environment variables).",
            "validate_sql": "Validates the generated SQL for safety and correctness. Checks for potentially harmful SQL commands. **May call Security LLM** if USE_SECURITY_LLM is enabled.",
            "execute_sql": "Executes the validated SQL query against the databases and processes the results.",
            "refine_sql": "Refines the SQL query if it failed validation, attempting to fix any issues while preserving the original intent. **Calls SQL LLM** for refinement.",
            "generate_wider_search_query": "Generates a broader search query when initial SQL queries return no results. **Calls SQL LLM**.",
            "execute_wider_search": "Executes the broader search query to find relevant information.",
            "generate_prompt": "Generates a specialized prompt for the response generation step, incorporating all relevant context. **Calls PROMPT LLM** (configured via PROMPT_LLM_* environment variables).",
            "generate_response": "Generates the final human-readable response based on query results and context. **Calls RESPONSE LLM** (configured via RESPONSE_LLM_* environment variables).",
            "execute_mcp_tool_calls_and_return": "Executes any MCP tool calls and manages where to route the results.",
            "return_mcp_response_to_llm": "Returns MCP service results directly back to the LLM for further processing. **Calls MCP LLM** (configured via MCP_LLM_* environment variables).",
            "await_mcp_response": "Awaits the response from MCP services when called by the LLM.",
            "security_check_after_refinement": "Performs additional security checks on the refined SQL query. **Calls Security LLM** if USE_SECURITY_LLM is enabled.",
            "__end__": "Terminal point of the workflow. Represents the completion of the process."
        }

        # Special handling for query_mcp_services to explain its complex logic
        if selected_node == "query_mcp_services":
            st.markdown("**Decision Logic for `query_mcp_services`:**")
            st.markdown("""
            - **To `execute_mcp_tool_calls_and_return`**:
              - Triggered when: databases are disabled AND MCP tool calls exist
              - Purpose: Execute MCP tool calls and return results when databases are unavailable

            - **To `generate_prompt`**:
              - Triggered when: databases are disabled BUT MCP services provided useful results
              - Purpose: Skip SQL generation and go directly to response generation

            - **To `generate_sql`**:
              - Triggered when: databases are enabled
              - Purpose: Proceed with normal SQL generation workflow

            - **To `return_mcp_response_to_llm`**:
              - Triggered when: MCP call was initiated by LLM and results are available
              - Purpose: Return MCP response directly back to the LLM for processing
            """)

        # Show specific information about the selected node
        if selected_node in node_info:
            st.markdown(f"**Purpose:** {node_info[selected_node]}")

        # Find all outgoing edges from the selected node
        outgoing_edges = []
        incoming_edges = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('%%{init:') or line_stripped.startswith('graph ') or line_stripped.startswith('classDef'):
                continue
            if line.startswith('\t') and ('(' in line or '[' in line):
                continue
            if '-->' in line_stripped or '-.' in line_stripped:
                if '-.' in line_stripped:  # Conditional edge
                    parts = line_stripped.split(' -. ')
                    if len(parts) >= 2:
                        start = parts[0].strip()
                        condition_and_end = parts[1]
                        condition_part = condition_and_end.split(' .-> ')
                        if len(condition_part) >= 2:
                            end = condition_part[1].replace(';', '').strip()

                            if start == selected_node:
                                condition = condition_part[0].strip().replace('&nbsp;', ' ')
                                outgoing_edges.append((end, condition))
                            elif end == selected_node:
                                condition = condition_part[0].strip().replace('&nbsp;', ' ')
                                incoming_edges.append((start, condition))
                elif '-->' in line_stripped:  # Regular edge
                    parts = line_stripped.replace('-->', '->').replace(';', '').strip()
                    start, end = parts.split(' -> ')

                    if start == selected_node:
                        outgoing_edges.append((end, "Direct transition"))
                    elif end == selected_node:
                        incoming_edges.append((start, "Direct transition"))

        # Display outgoing paths
        if outgoing_edges:
            st.markdown(f"**Paths from '{selected_node}':**")
            for target, condition in outgoing_edges:
                st.markdown(f"- **{target}**: {condition}")

        # Display incoming paths
        if incoming_edges:
            st.markdown(f"**Paths to '{selected_node}':**")
            for source, condition in incoming_edges:
                st.markdown(f"- **{source}** → {condition}")
    else:
        # Render the original graph if no node is selected
        st.graphviz_chart(dot_code, use_container_width=True)

    # Add legend for the visualization
    st.subheader("Legend")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown("**<span style='color:lightgreen'>Start Node</span>**", unsafe_allow_html=True)
    with col2:
        st.markdown("**<span style='color:lightblue'>Database Node</span>**", unsafe_allow_html=True)
    with col3:
        st.markdown("**<span style='color:orange'>MCP Node</span>**", unsafe_allow_html=True)
    with col4:
        st.markdown("**<span style='color:yellow'>Response Node</span>**", unsafe_allow_html=True)
    with col5:
        st.markdown("**<span style='color:red'>End Node</span>**", unsafe_allow_html=True)

    st.markdown("**Solid Line**: Direct transition without conditions")
    st.markdown("**Dashed Line with Label**: Conditional transition based on specific criteria")
    st.markdown("**Bold Purple Line**: Highlighted path when a node is selected")

    # Add LLM indicator to the legend
    st.markdown("**<span style='background-color:pink'>LLM Calling Node</span>**: Nodes that make calls to LLMs (takes precedence over other categories)", unsafe_allow_html=True)

    # Add detailed explanation for key decision points
    with st.expander("Detailed Decision Logic Explanation"):
        st.markdown("""
        ### Key Decision Points in the Workflow

        **1. `get_schema` node:**
        - Checks if databases are disabled (`disable_databases` flag)
        - If disabled: skips database operations and proceeds to discover MCP services
        - If enabled: continues with normal flow including database operations

        **2. `query_mcp_services` node:**
        The most complex decision point with multiple possible paths:

        - **Path to `execute_mcp_tool_calls_and_return`:**
          - Triggered when: databases are disabled AND MCP tool calls exist
          - Purpose: Execute MCP tool calls and return results when databases are unavailable

        - **Path to `generate_prompt`:**
          - Triggered when: databases are disabled BUT MCP services provided useful results
          - Purpose: Skip SQL generation and go directly to response generation

        - **Path to `generate_sql`:**
          - Triggered when: databases are enabled
          - Purpose: Proceed with normal SQL generation workflow

        - **Path to `return_mcp_response_to_llm`:**
          - Triggered when: MCP call was initiated by LLM and results are available
          - Purpose: Return MCP response directly back to the LLM for processing

        - **Path to `execute_mcp_tool_calls_and_return` with "skip_to_final":**
          - Triggered when: Both prompt and response generation are disabled
          - Purpose: Skip to final response with MCP-capable model response

        **3. `validate_sql` node:**
        - Checks if SQL query is safe and valid
        - If unsafe: goes to `refine_sql` to fix the query
        - If safe: proceeds to `execute_sql`

        **4. `execute_sql` node:**
        - Checks if query returned results
        - If results found: goes to `generate_prompt` for response generation
        - If no results: goes to `generate_wider_search_query` for broader search

        **5. `execute_mcp_tool_calls_and_return` node:**
        - Determines where to route results:
          - To user directly (`to_user`)
          - Back to LLM for further processing (`to_llm_for_processing`)

        ### LLM Model Calls in the Workflow

        The workflow makes calls to different LLMs at various stages:

        - **`generate_sql` node:** Calls the **SQL LLM** (configured via SQL_LLM_* environment variables)
        - **`validate_sql` node:** May call the **Security LLM** if USE_SECURITY_LLM is enabled
        - **`refine_sql` node:** Calls the **SQL LLM** for query refinement
        - **`generate_wider_search_query` node:** Calls the **SQL LLM** for generating broader search queries
        - **`generate_prompt` node:** Calls the **PROMPT LLM** (configured via PROMPT_LLM_* environment variables)
        - **`generate_response` node:** Calls the **RESPONSE LLM** (configured via RESPONSE_LLM_* environment variables)
        - **`query_mcp_services` node:** Calls the **MCP-Capable LLM** to analyze the user request and available MCP services, and generate appropriate tool calls
        - **`return_mcp_response_to_llm` node:** Calls the **MCP LLM** (configured via MCP_LLM_* environment variables)
        - **`security_check_after_refinement` node:** Calls the **Security LLM** if USE_SECURITY_LLM is enabled
        """)

    # Also show as code
    with st.expander("Show Mermaid Code"):
        st.code(mermaid_code, language="mermaid")

with tab2:
    st.header("Edit Workflow")
    
    st.markdown("""
    **Note:** This is a simplified editing interface. For complex workflow modifications, 
    you would typically edit the Python code directly. This interface allows you to:
    - View the current nodes and edges
    - Add new nodes (conceptual)
    - Modify existing nodes (conceptual)
    """)
    
    # Show current nodes
    st.subheader("Current Nodes")
    node_cols = st.columns(3)
    for idx, (node_id, node_data) in enumerate(st.session_state.workflow_nodes.items()):
        with node_cols[idx % 3]:
            with st.container(border=True):
                st.write(f"**{node_data['label']}**")
                st.write(f"Type: {node_data['type']}")
                
                # Allow editing of node properties
                new_label = st.text_input(f"Label for {node_id}", value=node_data['label'], key=f"label_{node_id}")
                new_type = st.selectbox(f"Type for {node_id}", 
                                       options=['default', 'start', 'end', 'database', 'mcp', 'response', 'llm_calling'],
                                       index=['default', 'start', 'end', 'database', 'mcp', 'response', 'llm_calling'].index(node_data['type']),
                                       key=f"type_{node_id}")
                
                # Update node data if changed
                if new_label != node_data['label'] or new_type != node_data['type']:
                    st.session_state.workflow_nodes[node_id]['label'] = new_label
                    st.session_state.workflow_nodes[node_id]['type'] = new_type
    
    # Show current edges
    st.subheader("Current Edges")
    for idx, edge in enumerate(st.session_state.workflow_edges):
        st.write(f"{edge['source']} → {edge['target']}")
        if edge['condition']:
            st.write(f"Condition: {edge['condition']}")
    
    # Add new node functionality
    st.subheader("Add New Node")
    with st.form("add_node_form"):
        new_node_id = st.text_input("Node ID")
        new_node_label = st.text_input("Node Label")
        new_node_type = st.selectbox("Node Type", 
                                   ['default', 'start', 'end', 'database', 'mcp', 'response', 'llm_calling'])
        
        if st.form_submit_button("Add Node"):
            if new_node_id and new_node_label:
                st.session_state.workflow_nodes[new_node_id] = {
                    'id': new_node_id,
                    'label': new_node_label,
                    'x': 0,  # Will be set by layout algorithm
                    'y': 0,  # Will be set by layout algorithm
                    'type': new_node_type
                }
                st.success(f"Added node: {new_node_label}")
            else:
                st.error("Please provide both ID and label for the new node")
    
    # Add new edge functionality
    st.subheader("Add New Edge")
    with st.form("add_edge_form"):
        source_node = st.selectbox("Source Node", options=list(st.session_state.workflow_nodes.keys()))
        target_node = st.selectbox("Target Node", options=list(st.session_state.workflow_nodes.keys()))
        edge_condition = st.text_input("Condition (optional)")
        
        if st.form_submit_button("Add Edge"):
            # Check if edge already exists
            edge_exists = any(
                edge['source'] == source_node and edge['target'] == target_node 
                for edge in st.session_state.workflow_edges
            )
            
            if not edge_exists:
                st.session_state.workflow_edges.append({
                    'source': source_node,
                    'target': target_node,
                    'condition': edge_condition if edge_condition else None
                })
                st.success(f"Added edge: {source_node} → {target_node}")
            else:
                st.error("Edge already exists")

with tab3:
    st.header("Workflow Details")

    # Show nodes
    st.subheader("Nodes")
    nodes_list = list(st.session_state.workflow_nodes.keys())
    for node_id, node_data in st.session_state.workflow_nodes.items():
        st.write(f"- `{node_id}`: {node_data['label']} (type: {node_data['type']})")

    # Show edges
    st.subheader("Edges")
    for edge in st.session_state.workflow_edges:
        condition_text = f" (condition: {edge['condition']})" if edge['condition'] else ""
        st.write(f"- `{edge['source']}` → `{edge['target']}`{condition_text}")

    # Show conditional edges by examining the compiled graph
    st.subheader("Conditional Logic")
    st.write("The workflow contains conditional logic that routes between nodes based on:")
    st.write("- Validation results (safe vs unsafe SQL)")
    st.write("- Retry limits")
    st.write("- Query results (initial vs wider search)")
    st.write("- Database enablement settings")
    st.write("- MCP service availability and results")

with tab4:
    st.header("Run Simulation")

    # Input for user request
    user_input = st.text_area("Enter your query:", height=100,
                              placeholder="Enter a query to simulate the LangGraph workflow...")

    col1, col2 = st.columns(2)
    with col1:
        disable_databases = st.checkbox("Disable databases", value=False)
    with col2:
        disable_blocking = st.checkbox("Disable SQL blocking", value=False)

    # Add a checkbox to enable real-time state visualization
    enable_realtime_viz = st.checkbox("Enable real-time state visualization", value=False)

    if st.button("Run Workflow"):
        if user_input:
            if enable_realtime_viz:
                # Create a placeholder for real-time updates
                state_placeholder = st.empty()

                # Reset the state visualizer
                st.session_state.state_visualizer.reset()

                # For demonstration, we'll simulate the workflow with state updates
                # In a real implementation, you would need to hook into the actual workflow execution
                with st.spinner("Running workflow with state visualization..."):
                    # This is a simplified simulation - in practice, you'd need to
                    # intercept state changes during actual workflow execution

                    # Simulate the workflow steps
                    simulated_states = []

                    # Initial state
                    initial_state = {
                        "user_request": user_input,
                        "schema_dump": {},
                        "sql_query": "",
                        "db_results": [],
                        "all_db_results": {},
                        "table_to_db_mapping": {},
                        "table_to_real_db_mapping": {},
                        "response_prompt": "",
                        "final_response": "",
                        "messages": [],
                        "validation_error": None,
                        "execution_error": None,
                        "sql_generation_error": None,
                        "retry_count": 0,
                        "disable_sql_blocking": disable_blocking,
                        "query_type": "initial",
                        "database_name": "all_databases",
                        "previous_sql_queries": []
                    }

                    simulated_states.append(("Initial State", initial_state.copy()))

                    # Simulate schema retrieval
                    time.sleep(0.5)
                    schema_state = initial_state.copy()
                    schema_state["schema_dump"] = {"users": [{"name": "VARCHAR", "id": "INT"}]}
                    simulated_states.append(("Schema Retrieved", schema_state.copy()))

                    # Simulate SQL generation
                    time.sleep(0.5)
                    sql_state = schema_state.copy()
                    sql_state["sql_query"] = "SELECT * FROM users LIMIT 5;"
                    simulated_states.append(("SQL Generated", sql_state.copy()))

                    # Simulate SQL validation
                    time.sleep(0.5)
                    validation_state = sql_state.copy()
                    validation_state["validation_error"] = None  # Assume validation passes
                    simulated_states.append(("SQL Validated", validation_state.copy()))

                    # Simulate SQL execution
                    time.sleep(0.5)
                    execution_state = validation_state.copy()
                    execution_state["db_results"] = [{"id": 1, "name": "John Doe"}, {"id": 2, "name": "Jane Smith"}]
                    simulated_states.append(("SQL Executed", execution_state.copy()))

                    # Simulate prompt generation
                    time.sleep(0.5)
                    prompt_state = execution_state.copy()
                    prompt_state["response_prompt"] = "Generate a response based on these user records..."
                    simulated_states.append(("Prompt Generated", prompt_state.copy()))

                    # Simulate response generation
                    time.sleep(0.5)
                    response_state = prompt_state.copy()
                    response_state["final_response"] = "Found 2 users in the database: John Doe and Jane Smith."
                    simulated_states.append(("Response Generated", response_state.copy()))

                    # Add all simulated states to the visualizer
                    for node_name, state in simulated_states:
                        st.session_state.state_visualizer.add_state_snapshot(state, node_name)

                        # Update the visualization
                        with state_placeholder.container():
                            st.subheader(f"Current Step: {node_name}")
                            visualize_state(state)

                        time.sleep(1)  # Pause between steps to show the visualization

                st.success("Workflow completed successfully!")

                # Show the full state transition history
                st.subheader("Complete State Transition History")
                visualize_state_transitions(st.session_state.state_visualizer.get_state_history())

            else:
                with st.spinner("Running workflow..."):
                    try:
                        # Run the workflow normally
                        result = run_enhanced_agent(
                            user_input,
                            disable_sql_blocking=disable_blocking,
                            disable_databases=disable_databases
                        )

                        st.success("Workflow completed successfully!")

                        # Display results
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Generated SQL")
                            st.code(result.get("generated_sql", "No SQL generated"), language="sql")

                        with col2:
                            st.subheader("Final Response")
                            st.write(result.get("final_response", "No response generated"))

                        with st.expander("Full Result"):
                            st.json(json.dumps(result, indent=2, default=str))

                    except Exception as e:
                        st.error(f"Error running workflow: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        else:
            st.warning("Please enter a query to run the simulation.")

with tab5:
    st.header("Debugging Tools")
    
    st.info("This tab provides debugging capabilities for the LangGraph workflow.")
    
    # Get the current graph
    graph = create_enhanced_agent_graph()
    
    # Show all nodes for breakpoint selection
    st.subheader("Set Breakpoints")
    
    # Get all node names from the graph
    all_nodes = list(graph.get_graph().nodes.keys())
    
    # Create a form for selecting breakpoints
    with st.form("breakpoint_form"):
        st.write("Select nodes where execution should pause:")
        
        # Create columns for better layout
        cols = st.columns(min(4, len(all_nodes)))
        
        # Create checkboxes for each node
        selected_breakpoints = []
        for i, node in enumerate(all_nodes):
            col_idx = i % len(cols)
            if st.session_state.get(f'bp_{node}', False):
                selected_breakpoints.append(node)
            cols[col_idx].checkbox(node, key=f'bp_{node}')
        
        submitted = st.form_submit_button("Apply Breakpoints")
        
        if submitted:
            # Update debugger breakpoints
            for node in all_nodes:
                if st.session_state[f'bp_{node}']:
                    st.session_state.debugger.add_breakpoint(node)
                else:
                    st.session_state.debugger.remove_breakpoint(node)
            st.success("Breakpoints updated!")
    
    # Show current breakpoints
    st.subheader("Current Breakpoints")
    current_bps = st.session_state.debugger.breakpoints
    if current_bps:
        bp_str = ", ".join(current_bps)
        st.write(f"Active breakpoints: {bp_str}")
    else:
        st.write("No active breakpoints")
    
    # Show execution history if available
    st.subheader("Execution History")
    history = st.session_state.debugger.get_execution_history()
    if history:
        for i, record in enumerate(history):
            st.write(f"{i+1}. {record['node']} at {time.strftime('%H:%M:%S', time.localtime(record['timestamp']))}")
    else:
        st.write("No execution history available yet")
    
    # Add debugging controls
    st.subheader("Debugging Controls")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Resume Execution"):
            if hasattr(st.session_state, 'debug_paused') and st.session_state.debug_paused:
                st.session_state.debugger.resume_execution()
                st.session_state.debug_paused = False
                st.rerun()
            else:
                st.warning("Not currently paused at a breakpoint")
    
    with col2:
        if st.button("⏭️ Step Over"):
            if hasattr(st.session_state, 'debug_paused') and st.session_state.debug_paused:
                st.session_state.debugger.step_execution()
                st.rerun()
            else:
                st.warning("Not currently paused at a breakpoint")
    
    with col3:
        if st.button("🔄 Reset Debugger"):
            st.session_state.debugger = WorkflowDebugger(graph)
            st.success("Debugger reset!")

with tab6:
    st.header("Export/Import Workflow")

    # Enhanced export functionality
    st.subheader("Export Current Workflow")

    # Allow user to name their workflow
    workflow_name = st.text_input("Workflow Name", value="my_langgraph_workflow")

    if st.button("Export Workflow"):
        # Get the workflow definition
        workflow_def = {
            "name": workflow_name,
            "nodes": st.session_state.workflow_nodes,
            "edges": st.session_state.workflow_edges,
            "conditional_logic": "Complex conditional logic based on validation results, retry limits, and query results",
            "export_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Convert to JSON
        workflow_json = json.dumps(workflow_def, indent=2)

        # Create download button
        st.download_button(
            label="Download JSON",
            data=workflow_json,
            file_name=f"{workflow_name.replace(' ', '_')}_workflow.json",
            mime="application/json"
        )

    st.subheader("Import Workflow")
    uploaded_file = st.file_uploader("Choose a workflow JSON file", type="json")
    if uploaded_file is not None:
        try:
            imported_workflow = json.load(uploaded_file)

            # Validate the imported workflow structure
            required_keys = {"nodes", "edges"}
            if not required_keys.issubset(imported_workflow.keys()):
                st.error("Invalid workflow file: Missing required keys (nodes, edges)")
            else:
                st.session_state.workflow_nodes = imported_workflow.get("nodes", {})
                st.session_state.workflow_edges = imported_workflow.get("edges", [])

                # Update workflow name if available
                if "name" in imported_workflow:
                    st.session_state.workflow_name = imported_workflow["name"]

                st.success("Workflow imported successfully!")

                # Show imported workflow details
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Nodes", len(st.session_state.workflow_nodes))
                with col2:
                    st.metric("Edges", len(st.session_state.workflow_edges))

                if "export_date" in imported_workflow:
                    st.write(f"Exported on: {imported_workflow['export_date']}")

                with st.expander("View Imported Workflow"):
                    st.json(imported_workflow)
        except Exception as e:
            st.error(f"Error importing workflow: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Sidebar with information
with st.sidebar:
    st.header("About")
    st.info("""
    This is an enhanced visual editor for the LangGraph workflow used in the AI agent.

    The graph shows:
    - Nodes: Different processing steps in the workflow
    - Edges: Sequential connections between nodes
    - Conditional logic: Decision points that route to different nodes based on conditions
    """)

    st.header("How to Use")
    st.markdown("""
    1. **Visualization Tab**: See the workflow graph
    2. **Edit Workflow Tab**: Modify nodes and edges
    3. **Details Tab**: Explore nodes and edges
    4. **Simulation Tab**: Run the workflow with sample inputs
    5. **Debugging Tab**: Set breakpoints and step through execution
    6. **Export/Import Tab**: Save/load workflow definitions
    """)

    st.header("Current Workflow")
    st.metric(label="Number of Nodes", value=len(nodes_list))
    st.metric(label="Number of Edges", value=len(st.session_state.workflow_edges))