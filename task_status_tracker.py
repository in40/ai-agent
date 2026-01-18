import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class TaskStatusTracker:
    """
    A simple task status tracker that persists task completion status to disk.
    This allows resuming work if the server crashes or the session is interrupted.
    """
    
    def __init__(self, status_file: str = "task_status.json"):
        self.status_file = status_file
        self.status_data = self._load_status()
    
    def _load_status(self) -> Dict:
        """Load task status from the file if it exists."""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If there's an error reading the file, start fresh
                return {"tasks": {}, "last_updated": None}
        else:
            return {"tasks": {}, "last_updated": None}
    
    def _save_status(self):
        """Save task status to the file."""
        self.status_data["last_updated"] = datetime.now().isoformat()
        with open(self.status_file, 'w') as f:
            json.dump(self.status_data, f, indent=2)
    
    def mark_task_completed(self, task_id: str, task_description: str = ""):
        """Mark a task as completed and save to disk."""
        self.status_data["tasks"][task_id] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "description": task_description
        }
        self._save_status()
        
    def mark_task_in_progress(self, task_id: str, task_description: str = ""):
        """Mark a task as in progress and save to disk."""
        self.status_data["tasks"][task_id] = {
            "status": "in_progress",
            "started_at": datetime.now().isoformat(),
            "description": task_description
        }
        self._save_status()
    
    def mark_task_pending(self, task_id: str, task_description: str = ""):
        """Mark a task as pending and save to disk."""
        self.status_data["tasks"][task_id] = {
            "status": "pending",
            "updated_at": datetime.now().isoformat(),
            "description": task_description
        }
        self._save_status()
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get the status of a specific task."""
        return self.status_data["tasks"].get(task_id)
    
    def get_all_tasks(self) -> Dict:
        """Get all tracked tasks."""
        return self.status_data["tasks"]
    
    def get_completed_tasks(self) -> List[str]:
        """Get a list of all completed task IDs."""
        return [
            task_id for task_id, task_data in self.status_data["tasks"].items()
            if task_data.get("status") == "completed"
        ]
    
    def get_incomplete_tasks(self) -> List[str]:
        """Get a list of all incomplete task IDs."""
        return [
            task_id for task_id, task_data in self.status_data["tasks"].items()
            if task_data.get("status") != "completed"
        ]

# Example usage:
if __name__ == "__main__":
    tracker = TaskStatusTracker()
    
    # Example of tracking a task
    task_id = "analyze_react_editor"
    tracker.mark_task_in_progress(task_id, "Analyze the React LangGraph editor for existing extended edit capabilities")
    
    # Simulate work being done...
    
    # Mark as completed
    tracker.mark_task_completed(task_id)
    
    print(f"Task '{task_id}' marked as completed.")
    print(f"All completed tasks: {tracker.get_completed_tasks()}")