# Architecture Diagram

## Enhanced LangGraph AI Agent with MCP Architecture

```
                    ┌─────────────────┐
                    │  discover_      │
                    │  services       │
                    │ (MCP Registry)  │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ query_mcp_      │
                    │ services        │
                    │ (Dedicated      │
                    │  MCP Model)     │
                    └─────────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
           ┌─────────────────┐   ┌─────────────────┐
           │ execute_mcp_    │   │ generate_sql    │
           │ tool_calls      │   │ (if databases  │
           │                 │   │  enabled)       │
           └─────────┬───────┘   └─────────┬───────┘
                     │                     │
                     │                     ▼
                     │           ┌─────────────────┐
                     │           │  validate_sql   │
                     │           │ (Security LLM)  │
                     └───────────► (after refine)  │
                                 └─────────┬───────┘
                                           │
                                 ┌─────────┴─────────┐
                                 │                   │
                                 ▼                   ▼
                        ┌─────────────────┐   ┌─────────────────┐
                        │  execute_sql    │   │  refine_sql     │
                        │ (Multi-DB)      │   │ (with previous │
                        └─────────┬───────┘   │  SQL queries)   │
                                  │           └─────────────────┘
                                  │                     │
                                  │         ┌───────────┘
                                  │         │
                                  ▼         ▼
                        ┌─────────────────┐ │
                        │ should_execute_ │ │
                        │ _wider_search   │◄┘
                        └─────────┬───────┘
                                  │
                         ┌────────┴────────┐
                         │                 │
                         ▼                 ▼
                   ┌─────────────────┐ ┌─────────────────┐
                   │generate_wider_  │ │generate_prompt  │
                   │_search_query    │ │(specialized)    │
                   │(with previous   │ │                 │
                   │ SQL queries)    │ └─────────┬───────┘
                   └─────────┬───────┘           │
                             │                   │
                             │           ┌───────┘
                             ▼           ▼
                   ┌─────────────────┐ ┌─────────────────┐
                   │execute_wider_   │ │query_mcp_       │
                   │_search          │ │_services       │
                   │(Multi-DB)       │ │(with dedicated │
                   └─────────┬───────┘ │ MCP model)     │
                             │         └─────────────────┘
                             │                   │
                             ▼                   ▼
                   ┌─────────────────┐   ┌─────────────────┐
                   │should_continue_ │   │execute_mcp_     │
                   │_wider_search    │   │_tool_calls      │
                   └─────────┬───────┘   └─────────────────┘
                             │                     │
                   ┌─────────┴─────────┐           ▼
                   │                   │ ┌─────────────────┐
                   ▼                   ▼ │generate_response│
           ┌─────────────────┐   ┌─────────────────┐ │                 │
           │generate_response│   │  refine_sql     │ └─────────────────┘
           │                 │   │ (with previous  │         │
           └─────────────────┘   │  SQL queries)   │         ▼
                     │           └─────────────────┘   ┌────────────┐
                     │                     │           │   END      │
                     └─────────────────────┘           └────────────┘
                              │
                              ▼
                     ┌────────────┐
                     │   END      │
                     └────────────┘
```

## MCP (Model Context Protocol) Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   MCP Model     │───▶│   MCP Services  │
│                 │    │ (Dedicated)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Tool Calls    │───▶│   Service Reg.  │
                    │  Generation     │    │   & Discovery   │
                    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Tool Execution│    │   MCP RAG       │
                    │                 │    │   Server        │
                    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Response      │    │   Document      │
                    │   Formatting    │    │   Retrieval     │
                    └─────────────────┘    └─────────────────┘
```

## Component Interactions

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   LangGraph     │───▶│   MCP Services  │
│                 │    │   Workflow      │    │ (RAG, Search,  │
└─────────────────┘    └─────────────────┘    │  SQL, DNS, etc.)│
                              │                └─────────────────┘
                              ▼                         │
                    ┌─────────────────┐                 │
                    │   LLM Models    │                 │
                    │ (MCP, Response, │                 ▼
                    │  Prompt, etc.)  │        ┌─────────────────┐
                    └─────────────────┘        │ External APIs   │
                              │                │ (Brave Search,  │
                              ▼                │  Databases, etc.)│
                    ┌─────────────────┐        └─────────────────┘
                    │ Natural Language│
                    │   Response      │
                    └─────────────────┘
```

## MCP Services Architecture

```
┌─────────────────┐
│   Application   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ MCP Registry    │
│ (Service       │
│  Discovery)     │
└─────────┬───────┘
          │
    ┌─────┼─────┬─────┬─────┐
    ▼     ▼     ▼     ▼     ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│RAG    │ │Search │ │SQL    │ │DNS    │
│Server │ │Server │ │Server │ │Server │
└───────┘ └───────┘ └───────┘ └───────┘
```

## Security Layers

```
┌─────────────────┐
│  User Request   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐  ┌─────────────────┐
│  Basic Keyword  │  │  Advanced LLM   │
│   Matching      │◀─┤  Analysis       │
│  (Block Harmful  │  │  (Reduce False │
│   Commands)      │  │   Positives)   │
└─────────┬───────┘  └─────────┬───────┘
          │                    │
          ▼                    ▼
    ┌────────────┐       ┌────────────┐
    │   Safe?    │──────▶│  Execute   │
    │   Query?   │ Yes   │   MCP      │
    └────────────┘       │  Services  │
         │ No            └────────────┘
         ▼
    ┌────────────┐
    │  Refine    │
    │   Query    │
    └────────────┘
```

## RAG Component Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   RAG Model     │───▶│   RAG Service   │
│                 │    │ (Dedicated)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Document      │    │   Vector Store  │
                    │   Retrieval     │───▶│   (ChromaDB)    │
                    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Context       │    │   Embedding     │
                    │   Augmentation  │    │   Models        │
                    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Response      │
                    │   Generation    │
                    └─────────────────┘
```