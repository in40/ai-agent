# Architecture Diagram

## Enhanced LangGraph AI Agent Architecture

```
                    ┌─────────────────┐
                    │   get_schema    │
                    │ (Multi-DB)      │
                    │ (with real DB   │
                    │  name mapping)  │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  generate_sql   │
                    │ (with previous  │
                    │  SQL queries,   │
                    │  real DB names) │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  validate_sql   │
                    │ (Security LLM)  │
                    │ (after refine)  │
                    └─────────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  execute_sql    │   │  refine_sql     │
           │ (Multi-DB)      │   │ (with previous │
           └─────────┬───────┘   │  SQL queries)   │
                     │           └─────────┬───────┘
                     │                     │
                     │                     │
                     │         ┌───────────┘
                     │         │
                     ▼         ▼
           ┌─────────────────┐ │
           │ should_execute_ │ │
           │ _wider_search   │◄┘
           └─────────┬───────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ generate_wider_ │  │ generate_prompt │
    │ _search_query   │  │ (specialized)   │
    │ (with previous  │  │                 │
    │  SQL queries)   │  └─────────┬───────┘
    └─────────┬───────┘            │
              │                    │
              │            ┌───────┘
              ▼            ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ execute_wider_  │  │ query_mcp_      │
    │ _search         │  │ _services       │
    │ (Multi-DB)      │  │ (with dedicated│
    └─────────┬───────┘  │  MCP model)     │
              │          └─────────┬───────┘
              │                    │
              ▼                    ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ should_continue_│  │ execute_mcp_    │
    │ _wider_search   │  │ _tool_calls     │
    └─────────┬───────┘  └─────────┬───────┘
              │                    │
    ┌─────────┴─────────┐          │
    │                   │          ▼
    ▼                   ▼  ┌─────────────────┐
┌─────────────┐  ┌─────────────────┐ │return_mcp_    │
│generate_resp│  │  refine_sql     │ │_response_to_  │
│             │  │ (with previous  │ │_llm          │
└─────────────┘  │  SQL queries)   │ └───────────────┘
         │       └─────────────────┘         │
         │                  │                │
         └──────────────────┘                ▼
                    │               ┌─────────────────┐
                    │               │generate_response│
                    ▼               │                 │
           ┌────────────┐           └─────────────────┘
           │   END      │                      │
           └────────────┘                      ▼
                                           ┌────────────┐
                                           │   END      │
                                           └────────────┘
```

## MCP Integration Architecture

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
                    │   Tool Execution│    │   MCP Search    │
                    │                 │    │   Server        │
                    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   Response      │    │   Web Search    │
                    │   Formatting    │    │   Results       │
                    └─────────────────┘    └─────────────────┘
```

## Component Interactions

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│   LangGraph     │───▶│   Database(s)   │
│                 │    │   Workflow      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │   LLM Models    │    │ Schema Analysis │
                    │ (SQL, Response, │    │ (Security, etc.)│
                    │  Prompt, etc.)  │    └─────────────────┘
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Natural Language│
                    │   Response      │
                    └─────────────────┘
```

## Multi-Database Architecture

```
┌─────────────────┐
│   Application   │
└─────────┬───────┘
          │
          ▼
┌─────────────────┐
│ MultiDatabase   │
│ Manager         │
└─────────┬───────┘
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
┌───────┐ ┌───────┐ ┌───────┐
│ DB 1  │ │ DB 2  │ │ DB N  │
│       │ │       │ │       │
└───────┘ └───────┘ └───────┘
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
    │   Query?   │ Yes   │   Query    │
    └────────────┘       └────────────┘
         │ No
         ▼
    ┌────────────┐
    │  Refine    │
    │   Query    │
    └────────────┘
```

## SSH Session Keep-Alive

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Call      │───▶│ SSHKeepAlive    │───▶│ Active SSH      │
│   (Long-running)│    │  Context        │    │  Session        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐              │
         │              │ Send periodic   │              │
         │              │ keep-alive      │              │
         │              │ signals every   │              │
         │              │ 45-60 seconds   │              │
         │              └─────────────────┘              │
         └───────────────────────────────────────────────┘
```