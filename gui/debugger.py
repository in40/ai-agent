"""
Debugging module for LangGraph workflow with breakpoint and step-through capabilities.
"""
import streamlit as st
import time
from typing import Dict, Any, Callable, Optional
from langgraph.graph import StateGraph
from langgraph_agent.langgraph_agent import AgentState

class WorkflowDebugger:
    def __init__(self, graph: StateGraph):
        self.graph = graph
        self.breakpoints = set()  # Set of node names where execution should pause
        self.paused = False
        self.current_node = None
        self.step_mode = False
        self.execution_history = []
        
    def add_breakpoint(self, node_name: str):
        """Add a breakpoint at the specified node."""
        self.breakpoints.add(node_name)
        
    def remove_breakpoint(self, node_name: str):
        """Remove a breakpoint from the specified node."""
        self.breakpoints.discard(node_name)
        
    def toggle_breakpoint(self, node_name: str):
        """Toggle breakpoint at the specified node."""
        if node_name in self.breakpoints:
            self.remove_breakpoint(node_name)
        else:
            self.add_breakpoint(node_name)
            
    def is_breakpoint(self, node_name: str) -> bool:
        """Check if there's a breakpoint at the specified node."""
        return node_name in self.breakpoints
    
    def pause_execution(self, node_name: str, state: AgentState):
        """Pause execution at the specified node with the current state."""
        self.paused = True
        self.current_node = node_name
        st.session_state.debug_paused = True
        st.session_state.current_debug_state = state
        st.session_state.current_debug_node = node_name
        
        # Show debugging interface
        self.show_debug_interface(state, node_name)
        
    def resume_execution(self):
        """Resume execution from a paused state."""
        self.paused = False
        st.session_state.debug_paused = False
        self.step_mode = False
        
    def step_execution(self):
        """Execute one step and pause again."""
        self.step_mode = True
        self.resume_execution()
        
    def show_debug_interface(self, state: AgentState, node_name: str):
        """Show the debugging interface in Streamlit."""
        with st.container(border=True):
            st.subheader(f"🔍 Debugging Paused at: {node_name}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("▶️ Resume", key="resume_btn"):
                    self.resume_execution()
                    
            with col2:
                if st.button("⏭️ Step Over", key="step_over_btn"):
                    self.step_execution()
                    
            with col3:
                if st.button("⏸️ Stop", key="stop_btn"):
                    st.session_state.debug_paused = False
                    st.rerun()
            
            # Show current state
            with st.expander("Current State", expanded=True):
                # Show key state variables
                st.write("**User Request:**")
                st.text_area("", value=state.get('user_request', ''), height=100, disabled=True)
                
                st.write("**SQL Query:**")
                st.code(state.get('sql_query', ''), language='sql')
                
                st.write("**Results Count:**")
                st.write(len(state.get('db_results', [])))
                
                st.write("**Errors:**")
                errors = []
                if state.get('validation_error'):
                    errors.append(f"Validation: {state['validation_error']}")
                if state.get('execution_error'):
                    errors.append(f"Execution: {state['execution_error']}")
                if state.get('sql_generation_error'):
                    errors.append(f"Generation: {state['sql_generation_error']}")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    st.success("No errors")
    
    def get_execution_path(self) -> list:
        """Return the execution path taken so far."""
        return [record['node'] for record in self.execution_history]
    
    def get_execution_history(self) -> list:
        """Return the full execution history."""
        return self.execution_history

def wrap_graph_for_debugging(graph: StateGraph, debugger: WorkflowDebugger):
    """
    Wrap the graph to enable debugging capabilities.
    This is a conceptual implementation - actual implementation would require
    intercepting the graph execution at each node.
    """
    # In a real implementation, this would involve wrapping the graph's execution
    # to intercept state changes and node transitions
    pass