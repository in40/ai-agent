import json
import os
from datetime import datetime
from typing import List, Dict, Optional

TODO_FILE_PATH = 'task_status.json'

class TodoManager:
    """Manages persistent storage of todo items across server restarts"""
    
    def __init__(self, file_path: str = TODO_FILE_PATH):
        self.file_path = file_path
        self.todos = self.load_todos()
    
    def load_todos(self) -> List[Dict]:
        """Load todos from file, return empty list if file doesn't exist"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    # Ensure all todos have the required structure
                    for todo in data:
                        if 'id' not in todo:
                            todo['id'] = str(datetime.now().timestamp())
                        if 'status' not in todo:
                            todo['status'] = 'pending'
                        if 'content' not in todo:
                            todo['content'] = 'Unnamed task'
                    return data
            except (json.JSONDecodeError, KeyError):
                # If there's an error reading the file, return empty list
                return []
        return []
    
    def save_todos(self) -> bool:
        """Save todos to file, return True if successful"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.todos, f, indent=2, default=str)
            return True
        except Exception:
            return False
    
    def get_todos(self) -> List[Dict]:
        """Get current todos"""
        return self.todos
    
    def update_todos(self, new_todos: List[Dict]) -> bool:
        """Update todos with new list and save to file"""
        self.todos = new_todos
        return self.save_todos()

# Global instance
todo_manager = TodoManager()

def get_current_todos() -> List[Dict]:
    """Get the current list of todos"""
    return todo_manager.get_todos()

def update_todos(new_todos: List[Dict]) -> bool:
    """Update the todos list and persist to file"""
    return todo_manager.update_todos(new_todos)

# Load initial todos
current_todos = get_current_todos()