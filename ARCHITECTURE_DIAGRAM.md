# Architecture Diagram

## Enhanced LangGraph AI Agent Architecture

```
                    ┌─────────────────┐
                    │   get_schema    │
                    │ (Multi-DB)      │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  generate_sql   │
                    │ (with previous │
                    │  SQL queries)   │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  validate_sql   │
                    │ (Security LLM)  │
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
    │ _search_query   │  │                 │
    │ (with previous  │  └─────────┬───────┘
    │  SQL queries)   │            │
    └─────────┬───────┘    ┌───────┘
              │            │
              │    ┌───────┘
              ▼    ▼
    ┌─────────────────┐
    │ execute_wider_  │
    │ _search         │
    │ (Multi-DB)      │
    └─────────┬───────┘
              │
              ▼
    ┌─────────────────┐
    │ should_continue_│
    │ _wider_search   │
    └─────────┬───────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────────┐  ┌─────────────────┐
│generate_resp│  │  refine_sql     │
│             │  │ (with previous  │
└─────────────┘  │  SQL queries)   │
         │       └─────────────────┘
         │                  │
         └──────────────────┘
                    │
                    ▼
           ┌────────────┐
           │   END      │
           └────────────┘
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