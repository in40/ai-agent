# Previous SQL Queries Feature

## Overview
The Previous SQL Queries feature maintains a history of all SQL queries generated during the processing of a user request. This feature prevents the system from repeating failed approaches and provides context for subsequent query generations, improving the overall effectiveness of the AI agent.

## Purpose
- **Prevent Repetition**: Avoid generating the same SQL queries that have already been attempted and failed
- **Provide Context**: Give the LLM awareness of previous attempts to guide future query generation
- **Improve Efficiency**: Reduce the number of failed attempts by learning from past queries
- **Enhance Accuracy**: Help the system converge on successful queries faster

## Implementation Details

### State Management
The feature is implemented through the `previous_sql_queries` field in the `AgentState`:

```python
class AgentState(TypedDict):
    # ... other fields ...
    previous_sql_queries: List[str]  # History of all previously generated SQL queries
```

### Data Flow
1. When a new SQL query is generated, it's added to the `previous_sql_queries` list
2. The list is passed to the LLM as context when generating subsequent queries
3. The LLM is instructed to consider the history to avoid repeating failed approaches

### Prompt Integration
The SQL generator prompt includes a section for previous SQL queries:

```
Previous SQL Queries History:
{previous_sql_queries}

You are an expert SQL developer... [rest of prompt]
```

## Benefits
- **Reduced Redundancy**: The system won't repeatedly try the same failed queries
- **Contextual Awareness**: The LLM has visibility into the query generation history
- **Faster Convergence**: The system reaches successful queries more quickly
- **Improved User Experience**: Fewer failed attempts lead to better responses

## Usage in Nodes
The feature is utilized in several LangGraph nodes:

- `refine_sql_node`: Updates the history when refining queries
- `generate_wider_search_query_node`: Considers previous queries when generating alternative strategies
- All nodes that preserve state carry forward the query history

## Example Flow
1. User request: "Show me all users from New York"
2. Initial query: `SELECT * FROM users WHERE city = 'New York'` (fails due to table not existing)
3. History now contains: ["SELECT * FROM users WHERE city = 'New York'"]
4. Refined query: `SELECT * FROM customers WHERE city = 'New York'` (succeeds)
5. History now contains: ["SELECT * FROM users WHERE city = 'New York'", "SELECT * FROM customers WHERE city = 'New York'"]
6. If wider search is needed, the new query will consider both previous attempts to avoid similar mistakes

## Configuration
The feature is enabled by default and doesn't require any special configuration. The history is automatically maintained throughout the processing pipeline.