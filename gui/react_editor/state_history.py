"""
State history tracking system for the LangGraph editor.
Implements undo/redo functionality by storing workflow states.
"""
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid


class StateHistoryManager:
    """Manages the history of workflow states for undo/redo functionality."""
    
    def __init__(self, history_file: str = "./history/workflow_history.json", max_states: int = 3):
        self.history_file = Path(history_file)
        self.max_states = max_states
        self.history_dir = self.history_file.parent
        self.history_dir.mkdir(exist_ok=True)
        
        # Load existing history or initialize empty
        self.states = self._load_history()
        self.current_index = len(self.states) - 1 if self.states else -1  # Points to current state
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    return data.get('states', [])
            except (json.JSONDecodeError, KeyError):
                return []
        return []
    
    def _save_history(self):
        """Save history to file."""
        data = {
            'states': self.states,
            'max_states': self.max_states,
            'timestamp': time.time()
        }
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_state(self, workflow_data: Dict[str, Any]) -> str:
        """Save a new state to history."""
        state_id = str(uuid.uuid4())
        
        new_state = {
            'id': state_id,
            'timestamp': time.time(),
            'workflow': workflow_data,
            'label': f"State {len(self.states) + 1} - {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # If we're not at the end of the history, truncate future states
        if self.current_index < len(self.states) - 1:
            self.states = self.states[:self.current_index + 1]
        
        # Add the new state
        self.states.append(new_state)
        
        # Limit the history size
        if len(self.states) > self.max_states:
            # Remove the oldest state
            self.states.pop(0)
            # Adjust current index if needed
            self.current_index = len(self.states) - 1
        
        # Update current index to point to the new state
        self.current_index = len(self.states) - 1
        
        # Save to file
        self._save_history()
        
        return state_id
    
    def get_current_state(self) -> Optional[Dict[str, Any]]:
        """Get the current state."""
        if 0 <= self.current_index < len(self.states):
            return self.states[self.current_index]['workflow']
        return None
    
    def get_state_by_id(self, state_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific state by ID."""
        for state in self.states:
            if state['id'] == state_id:
                return state['workflow']
        return None
    
    def get_history_list(self) -> List[Dict[str, Any]]:
        """Get the list of available states."""
        return [{'id': state['id'], 'label': state['label'], 'timestamp': state['timestamp']} 
                for state in self.states]
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.current_index < len(self.states) - 1
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """Move to the previous state."""
        if self.can_undo():
            self.current_index -= 1
            return self.states[self.current_index]['workflow']
        return None
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """Move to the next state."""
        if self.can_redo():
            self.current_index += 1
            return self.states[self.current_index]['workflow']
        return None
    
    def clear_future_states(self):
        """Clear any states after the current one (when a new change is made)."""
        if self.current_index < len(self.states) - 1:
            self.states = self.states[:self.current_index + 1]
            self._save_history()


# Global instance of the history manager
history_manager = StateHistoryManager()