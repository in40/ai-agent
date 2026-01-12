# Workflow Diagrams

## Main Workflow Diagram

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

## Error Handling Flow Diagram

```mermaid
graph TD
    A[Error Detected] --> B{Error Type?}
    
    B -->|Validation Error| C[Increment Retry Count]
    B -->|Execution Error| D[Log Execution Error]
    B -->|Generation Error| E[Log Generation Error]
    
    C --> F{Retry Limit Reached?}
    D --> F
    E --> F
    
    F -->|Yes| G[Return Error Response]
    F -->|No| H[Route to Appropriate Handler]
    
    G --> I[End: Error Response]
    H --> J[Continue Processing]
    
    style A fill:#ffcdd2
    style G fill:#f8bbd0
    style I fill:#ffcdd2
    style J fill:#c8e6c9
```

## Retry Mechanism Diagram

```mermaid
graph TD
    A[Process Request] --> B{Errors Exist?}
    
    B -->|No| C[Generate Response]
    B -->|Yes| D{Retry Count < Max?}
    
    C --> E[End Success]
    D -->|No| F[End with Error]
    D -->|Yes| G[Refine/Retry Logic]
    
    F --> H[End Failure]
    G --> I[Update State]
    I --> A
    
    style A fill:#e3f2fd
    style C fill:#e8f5e8
    style E fill:#c8e6c9
    style F fill:#ffcdd2
    style H fill:#f8bbd0
    style G fill:#fff3e0
    style I fill:#e1f5fe
```

## Wider Search Activation Diagram

```mermaid
graph TD
    A[Execute SQL] --> B{Results Empty?}
    
    B -->|No| C[Generate Prompt]
    B -->|Yes| D{Max Attempts Reached?}
    
    C --> E[Generate Response]
    D -->|Yes| E
    D -->|No| F[Generate Wider Search Query]
    
    F --> G[Execute Wider Search]
    G --> H{Results Available?}
    
    H -->|Yes| C
    H -->|No| D
    
    style A fill:#e3f2fd
    style C fill:#e1f5fe
    style E fill:#c8e6c9
    style F fill:#f3e5f5
    style G fill:#f3e5f5
    style D fill:#fff3e0
```

## Security Validation Flow Diagram

```mermaid
graph TD
    A[New SQL Query] --> B{Security Check Enabled?}
    
    B -->|No| C[Mark as Safe]
    B -->|Yes| D[LLM Security Analysis]
    
    D --> E{LLM Analysis Result?}
    E -->|Safe| F[Basic Validation]
    E -->|Unsafe| G[Mark as Unsafe]
    
    F --> H{Basic Validation Result?}
    H -->|Safe| I[Mark as Safe]
    H -->|Unsafe| G
    
    C --> J[Continue Processing]
    G --> K[Route to Refinement]
    I --> J
    
    style A fill:#e3f2fd
    style D fill:#fff3e0
    style F fill:#fff3e0
    style C fill:#e8f5e8
    style G fill:#ffcdd2
    style I fill:#e8f5e8
    style J fill:#c8e6c9
    style K fill:#fff3e0
```