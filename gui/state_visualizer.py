"""
Module for visualizing the state of the LangGraph workflow during execution.
"""
import streamlit as st
import json
import time
from typing import Dict, Any, List
from langchain_core.messages import BaseMessage

class StateVisualizer:
    def __init__(self):
        self.state_history = []
        self.current_state_index = 0
        
    def add_state_snapshot(self, state: Dict[str, Any], node_name: str = None):
        """Add a snapshot of the current state to the history."""
        snapshot = {
            'timestamp': time.time(),
            'node': node_name,
            'state': state.copy()
        }
        self.state_history.append(snapshot)
        self.current_state_index = len(self.state_history) - 1
        
    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state from the history."""
        if self.state_history:
            return self.state_history[self.current_state_index]['state']
        return {}
        
    def get_state_at_index(self, index: int) -> Dict[str, Any]:
        """Get the state at a specific index in the history."""
        if 0 <= index < len(self.state_history):
            return self.state_history[index]['state']
        return {}
        
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get the entire state history."""
        return self.state_history
        
    def reset(self):
        """Reset the state history."""
        self.state_history = []
        self.current_state_index = 0

def visualize_state(state: Dict[str, Any]):
    """Visualize the current state in Streamlit."""
    st.subheader("Current State")
    
    # Create expandable sections for different state components
    with st.expander("User Request", expanded=True):
        st.text_area("Request", value=state.get('user_request', ''), height=100, disabled=True)
    
    with st.expander("Schema Dump"):
        schema_dump = state.get('schema_dump', {})
        if schema_dump:
            st.json(json.dumps(schema_dump, indent=2, default=str))
        else:
            st.write("No schema dump available")
    
    with st.expander("SQL Query"):
        st.code(state.get('sql_query', ''), language='sql')
    
    with st.expander("Database Results"):
        results = state.get('db_results', [])
        if results:
            st.write(f"Number of results: {len(results)}")
            for i, result in enumerate(results[:5]):  # Show first 5 results
                st.json(json.dumps(result, indent=2, default=str))
            if len(results) > 5:
                st.write(f"... and {len(results) - 5} more results")
        else:
            st.write("No database results")
    
    with st.expander("All Database Results"):
        all_results = state.get('all_db_results', {})
        if all_results:
            st.json(json.dumps(all_results, indent=2, default=str))
        else:
            st.write("No all database results")
    
    with st.expander("Response Prompt"):
        st.text_area("Prompt", value=state.get('response_prompt', ''), height=150, disabled=True)
    
    with st.expander("Final Response"):
        st.text_area("Response", value=state.get('final_response', ''), height=150, disabled=True)
    
    with st.expander("Messages"):
        messages = state.get('messages', [])
        if messages:
            for msg in messages:
                if hasattr(msg, 'content'):
                    st.write(f"**{msg.type}**: {msg.content}")
                else:
                    st.write(str(msg))
        else:
            st.write("No messages")
    
    with st.expander("Errors"):
        validation_error = state.get('validation_error')
        execution_error = state.get('execution_error')
        sql_generation_error = state.get('sql_generation_error')
        
        if validation_error:
            st.error(f"Validation Error: {validation_error}")
        if execution_error:
            st.error(f"Execution Error: {execution_error}")
        if sql_generation_error:
            st.error(f"SQL Generation Error: {sql_generation_error}")
        
        if not any([validation_error, execution_error, sql_generation_error]):
            st.success("No errors")
    
    with st.expander("Retry Count"):
        st.write(state.get('retry_count', 0))
    
    with st.expander("Other State Variables"):
        # Show other state variables not covered above
        excluded_keys = {
            'user_request', 'schema_dump', 'sql_query', 'db_results', 'all_db_results',
            'response_prompt', 'final_response', 'messages', 'validation_error',
            'execution_error', 'sql_generation_error', 'retry_count', 'table_to_db_mapping',
            'table_to_real_db_mapping', 'disable_sql_blocking', 'query_type', 'database_name',
            'previous_sql_queries'
        }
        
        other_vars = {k: v for k, v in state.items() if k not in excluded_keys}
        if other_vars:
            st.json(json.dumps(other_vars, indent=2, default=str))
        else:
            st.write("No additional variables")

def visualize_state_transitions(state_history: List[Dict[str, Any]]):
    """Visualize the state transitions over time."""
    if not state_history:
        st.write("No state history to display")
        return
    
    st.subheader("State Transitions")
    
    # Create a timeline of state changes
    for i, snapshot in enumerate(state_history):
        timestamp = time.strftime('%H:%M:%S', time.localtime(snapshot['timestamp']))
        node_name = snapshot.get('node', 'Unknown')
        
        with st.expander(f"Step {i}: {node_name} at {timestamp}"):
            # Show key changes in state
            state = snapshot['state']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**SQL Query:**")
                st.code(state.get('sql_query', '')[:200] + "..." if len(state.get('sql_query', '')) > 200 else state.get('sql_query', ''))
                
                st.write("**Results Count:**")
                st.write(len(state.get('db_results', [])))
            
            with col2:
                st.write("**Errors:**")
                errors = []
                if state.get('validation_error'):
                    errors.append(f"Validation: {state['validation_error'][:50]}...")
                if state.get('execution_error'):
                    errors.append(f"Execution: {state['execution_error'][:50]}...")
                if state.get('sql_generation_error'):
                    errors.append(f"Generation: {state['sql_generation_error'][:50]}...")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    st.success("No errors")