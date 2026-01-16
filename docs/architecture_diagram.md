# Architecture Diagram

## LangGraph Workflow Visualization

```mermaid
graph TD
    A[Start: User Request] --> B[Get Schema Node]
    B --> C[Generate SQL Node]
    C --> D[Validate SQL Node]
    
    D -->|Unsafe/Invalid| E[Refine SQL Node]
    D -->|Safe/Valid| F[Execute SQL Node]
    
    E --> G[Security Check After Refinement]
    G -->|Needs Refinement| D
    G -->|Safe| F
    
    F -->|Has Results| H[Generate Prompt Node]
    F -->|No Results| I[Generate Wider Search Query Node]
    
    H --> J[Generate Response Node]
    J --> K[End: Natural Language Response]
    
    I --> L[Validate Wider Search Query]
    L -->|Invalid| E
    L -->|Valid| M[Execute Wider Search Node]
    
    M -->|Has Results| H
    M -->|No Results| I
    M -->|Errors| E
    
    style A fill:#e1f5fe
    style K fill:#e8f5e8
    style D fill:#fff3e0
    style F fill:#f3e5f5
    style I fill:#e0f2f1
    style M fill:#e0f2f1
```

## Node Descriptions

### 1. Get Schema Node
- Retrieves database schema from all available databases
- Creates table-to-database mappings
- Combines schema information from multiple databases

### 2. Generate SQL Node
- Generates SQL query based on user request and schema
- Considers history of previous SQL queries to avoid repetition
- Incorporates error feedback from previous attempts

### 3. Validate SQL Node
- Performs security validation using dual-layer approach
- Basic keyword matching and LLM-based security analysis
- Checks for potentially harmful commands and SQL injection patterns

### 4. Execute SQL Node
- Executes SQL query on appropriate databases based on table-to-database mapping
- Handles cross-database queries when needed
- Collects results from multiple databases

### 5. Refine SQL Node
- Refines SQL query based on execution results or errors
- Uses error feedback to improve query generation
- Considers previous errors when generating new queries

### 6. Security Check After Refinement
- Performs additional security validation on refined queries
- Ensures refined queries meet security requirements
- Routes back to validation if needed

### 7. Generate Wider Search Query Node
- Activates when initial query returns no results
- Generates alternative search strategies based on schema analysis
- Considers history of previous attempts to avoid repetition

### 8. Execute Wider Search Node
- Executes wider search queries across databases
- Continues until results are found or maximum attempts reached
- Handles execution errors and retries as needed

### 9. Generate Prompt Node
- Creates specialized prompt for response generation
- Incorporates user request and database results
- Formats information for natural language processing

### 10. Generate Response Node
- Converts database results into natural language response
- Produces human-readable output based on query results
- Returns final response to user

## Key Features Highlighted

- **State Management**: All nodes maintain and update state information
- **Error Handling**: Multiple retry mechanisms and error recovery paths
- **Security**: Dual-layer validation at multiple points in the workflow
- **Multi-Database Support**: Automatic routing based on table-to-database mappings
- **Wider Search**: Automatic activation when initial queries return no results
- **Query History**: Maintains history of all generated queries to prevent repetition