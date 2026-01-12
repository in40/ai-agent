# SSH Session Keep-Alive Feature

## Overview
This feature addresses the issue of SSH sessions becoming inactive and disconnecting during long-running operations, particularly when the AI agent is waiting for responses from Language Learning Models (LLMs).

## Problem
When the AI agent makes requests to LLMs, these requests can take a significant amount of time to complete. During this period, the SSH session remains idle, which can cause the connection to timeout and disconnect, interrupting the operation.

## Solution
The SSH keep-alive feature sends periodic signals to the terminal to maintain an active SSH session during long-running operations like LLM requests.

## Implementation Details

### SSHKeepAlive Class
Located in `utils/ssh_keep_alive.py`, this class provides the core functionality:

- Sends periodic null-byte signals to the terminal every 45-60 seconds
- Automatically detects if running in an SSH session
- Uses a background thread to send keep-alive signals
- Provides context manager support for easy integration

### Integration Points
The keep-alive functionality has been integrated into all LLM-related operations:

1. **SQL Generation** (`models/sql_generator.py`)
2. **Response Generation** (`models/response_generator.py`)
3. **Prompt Generation** (`models/prompt_generator.py`)
4. **Security Analysis** (`models/security_sql_detector.py`)

Each of these modules now uses the `SSHKeepAliveContext` context manager around LLM calls to ensure the SSH session remains active.

## Usage
The feature is automatically applied when the application makes LLM requests. No additional configuration is required.

For manual usage, you can use the context manager:

```python
from utils.ssh_keep_alive import SSHKeepAliveContext

with SSHKeepAliveContext():
    # Long-running operation here
    result = llm_client.generate(prompt)
```

Or use the decorator-like function:

```python
from utils.ssh_keep_alive import keep_ssh_alive_for_llm_call

result = keep_ssh_alive_for_llm_call(llm_client.generate, prompt)
```

## Configuration
The keep-alive interval can be customized (default is 60 seconds):

```python
with SSHKeepAliveContext(interval=30):  # 30-second intervals
    # LLM call here
```

## Benefits
- Prevents SSH disconnections during long-running LLM requests
- Maintains session continuity for better user experience
- Automatic detection of SSH sessions
- Minimal overhead during operations
- Transparent integration with existing codebase