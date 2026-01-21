# AI Agent Architecture Diagram

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[(User)]
    end
    
    subgraph "Core Agent Layer"
        A[LangGraph Agent]
        B[MCP Capable Model]
        C[Response Generator]
    end
    
    subgraph "MCP Services Registry"
        R[(MCP Registry)]
    end
    
    subgraph "MCP Services"
        S1[RAG Service]
        S2[Search Service]
        S3[SQL Service]
        S4[DNS Service]
    end
    
    subgraph "External Resources"
        DB[(Databases)]
        WEB[(Web/Internet)]
        DOC[(Documents)]
    end
    
    UI --> A
    A --> B
    A --> C
    B --> R
    R --> S1
    R --> S2
    R --> S3
    R --> S4
    S1 --> DOC
    S2 --> WEB
    S3 --> DB
    S4 --> WEB
    
    style A fill:#e1f5fe
    style R fill:#f3e5f5
    style S1 fill:#e8f5e8
    style S2 fill:#e8f5e8
    style S3 fill:#e8f5e8
    style S4 fill:#e8f5e8
```

## Architecture Overview

The AI Agent follows a Model Context Protocol (MCP) architecture where:

1. **User** submits natural language requests to the LangGraph Agent
2. **LangGraph Agent** coordinates the workflow and delegates tasks
3. **MCP Capable Model** generates appropriate tool calls to MCP services
4. **MCP Registry** maintains a catalog of available services
5. **MCP Services** provide specialized capabilities:
   - **RAG Service**: Document retrieval and ingestion
   - **Search Service**: Web search functionality
   - **SQL Service**: Database query generation and execution
   - **DNS Service**: Hostname resolution
6. **External Resources** provide the actual data and services

This architecture allows for flexible integration of various tools and services while maintaining a consistent interface through the MCP protocol.