"""
Simulation engine for LangGraph workflows.
Allows step-by-step execution with user input and decision explanations.
"""
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from queue import Queue, Empty
from enum import Enum


class SimulationStatus(Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    ERROR = "error"


class SimulationEngine:
    """Main simulation engine for LangGraph workflows."""

    def __init__(self):
        self.status = SimulationStatus.NOT_STARTED
        self.current_step = 0
        self.execution_history = []
        self.current_state = {}
        self.workflow = None
        self.user_inputs = {}
        self.decision_log = []
        self.lock = threading.Lock()
        self.input_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.checkpoint_saver = MemorySaver()

    def load_workflow_from_config(self, workflow_config: Dict[str, Any]):
        """Load workflow from configuration similar to the editor."""
        # For simulation, we'll use the actual langgraph_agent workflow
        # The workflow_config parameter is kept for future implementation
        # where we might construct a workflow from UI configuration
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph

        self.workflow = create_enhanced_agent_graph()
        self.status = SimulationStatus.NOT_STARTED

    def start_simulation(self, initial_inputs: Dict[str, Any]):
        """Start the simulation with initial inputs."""
        with self.lock:
            self.current_state = initial_inputs
            self.status = SimulationStatus.RUNNING
            self.current_step = 0
            self.execution_history = []
            self.decision_log = []

        # Begin execution in a separate thread
        future = self.executor.submit(self._execute_workflow)
        return future

    def _execute_workflow(self):
        """Execute the workflow step by step."""
        try:
            # Create a config with the checkpoint saver to enable state management
            config = {"configurable": {"thread_id": "simulation_thread"}}

            # Use the stream method to execute step by step
            for event in self.workflow.stream(
                self.current_state,
                config,
                stream_mode="values"  # Changed to values to get full state at each step
            ):
                # Process the state update
                self._process_state_update(event)

                # Check if we need to pause
                with self.lock:
                    if self.status in [SimulationStatus.PAUSED, SimulationStatus.WAITING_FOR_INPUT]:
                        # Wait until resumed
                        while self.status in [SimulationStatus.PAUSED, SimulationStatus.WAITING_FOR_INPUT]:
                            time.sleep(0.1)

                    if self.status == SimulationStatus.ERROR:
                        break

        except Exception as e:
            with self.lock:
                self.status = SimulationStatus.ERROR
                self.execution_history.append({
                    'step': self.current_step,
                    'type': 'error',
                    'message': str(e),
                    'timestamp': time.time()
                })

    def execute_one_step(self):
        """Execute just one step of the workflow."""
        try:
            # Create a config with the checkpoint saver to enable state management
            config = {"configurable": {"thread_id": "simulation_thread"}}

            # Get the next state update
            for event in self.workflow.stream(
                self.current_state,
                config,
                stream_mode="values"  # Changed to values to get full state at each step
            ):
                # Process the state update
                self._process_state_update(event)

                # Only execute one step, then pause
                with self.lock:
                    self.status = SimulationStatus.PAUSED
                break  # Exit after one step

        except Exception as e:
            with self.lock:
                self.status = SimulationStatus.ERROR
                self.execution_history.append({
                    'step': self.current_step,
                    'type': 'error',
                    'message': str(e),
                    'timestamp': time.time()
                })

    def _process_state_update(self, state_update: Dict[str, Any]):
        """Process a state update from the workflow."""
        with self.lock:
            # Update current state with the changes
            if isinstance(state_update, dict):
                self.current_state = state_update  # Update with the full state

            # Log this step
            step_info = {
                'step': self.current_step,
                'node_output': state_update,  # The output of the current node
                'current_state_snapshot': dict(list(state_update.items())[:10]),  # First 10 items as snapshot
                'timestamp': time.time(),
                'status': 'completed'
            }

            self.execution_history.append(step_info)
            self.current_step += 1

            # For now, pause after each step to allow user to see what happened
            # In a real implementation, this would be configurable
            self.status = SimulationStatus.PAUSED

    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        with self.lock:
            return {
                'status': self.status.value,
                'current_step': self.current_step,
                'total_steps': len(self.execution_history),
                'current_state_keys': list(self.current_state.keys()) if self.current_state else [],
                'execution_history': self.execution_history[-5:],  # Last 5 steps
                'decision_log': self.decision_log,
                'full_current_state': self.current_state
            }

    def step_forward(self):
        """Continue execution to the next step."""
        with self.lock:
            if self.status == SimulationStatus.PAUSED:
                self.status = SimulationStatus.RUNNING
                return True
            return False

    def pause_simulation(self):
        """Pause the simulation."""
        with self.lock:
            if self.status == SimulationStatus.RUNNING:
                self.status = SimulationStatus.PAUSED
                return True
            return False

    def reset_simulation(self):
        """Reset the simulation to initial state."""
        with self.lock:
            self.status = SimulationStatus.NOT_STARTED
            self.current_step = 0
            self.execution_history = []
            self.current_state = {}
            self.decision_log = []
            return True

    def submit_user_input(self, input_data: Dict[str, Any]):
        """Submit user input when requested."""
        with self.lock:
            if self.status == SimulationStatus.WAITING_FOR_INPUT:
                # Process the input
                self.user_inputs.update(input_data)
                self.status = SimulationStatus.RUNNING
                # Put input in queue for the workflow to consume
                self.input_queue.put(input_data)
                return True
            return False

    def force_next_step(self):
        """Force the simulation to proceed to the next step."""
        with self.lock:
            if self.status in [SimulationStatus.PAUSED, SimulationStatus.WAITING_FOR_INPUT]:
                self.status = SimulationStatus.RUNNING
                return True
            return False


# Global instance of the simulation engine
simulation_engine = SimulationEngine()