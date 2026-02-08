# Qwen Memory

This file is used to store personal information and preferences for the Qwen agent.

## Important Architecture Notes

When updating AI agent functionality:
- The API gateway is located at: `/root/qwen/ai_agent/backend/app.py`
- The actual agent service is located at: `/root/qwen/ai_agent/backend/services/agent/app.py`
- When making changes to AI agent behavior, modify the agent service, NOT the API gateway
- The API gateway only forwards requests to the appropriate microservices

## Task Status Tracking System

### Purpose
A persistent task tracking system has been implemented to allow resuming work if the server crashes or the session is interrupted.

### Implementation
- A `task_status_tracker.py` file has been created that implements a TaskStatusTracker class
- Task statuses are persisted to a `task_status.json` file on disk
- The system tracks task status (completed, in_progress, pending) along with timestamps
- Each task has an ID and description for easy identification

### Usage
```python
from task_status_tracker import TaskStatusTracker

tracker = TaskStatusTracker()

# Mark a task as in progress
tracker.mark_task_in_progress("task_id", "Description of the task")

# Mark a task as completed
tracker.mark_task_completed("task_id", "Description of the task")

# Get all completed tasks
completed_tasks = tracker.get_completed_tasks()

# Get all incomplete tasks
incomplete_tasks = tracker.get_incomplete_tasks()
```

### Benefits
- Resilience against server crashes or interruptions
- Persistent tracking of work progress
- Ability to resume from where work was left offr

## Qwen Added Memories
- To run the AI agent, first activate the virtual environment with: source ai_agent_env/bin/activate
- Avoid using Werkzeug for any functionality in the codebase going forward; implement custom solutions or use alternative libraries instead.
