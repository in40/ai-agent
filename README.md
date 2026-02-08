This is the only part written by the human :) 
---
Work in progress
- migrating MCP servers to JSON RPC 2 (instead of original http)
----
TODO
- migration to JSON-RPC-2 for MCP calls need to be implemented to follow industry standard (this wil also allow to test llm-side mcp calls instead of current agent-managed) 
- implement functionality for LLM-side parralelism testing (this ia now supportd on LM Studio, but unclear if it's actually enhance performance on my current GPU, but definitely should improve speeds when external commercial LLM is used - DeepSeek in my case)
- investigate, is LLM parameters can be set/requested form agent side - to be able to change temperature, top_*, etc - to see if moving to more strict genration with bring more code quality/stability or if relaxed generation will help to solve more complex issues
- introduce functionality for LLM based document chanking (with PDF conversion this will require GPU on localhost)
- move logging switch to variable instead of being hardcoded

----

This suit is ... for hands-on experience with RAG.
It contains all requird components to check you hypohitesis:

- sybsystems to import, process, store and retrieve documents (vector db based- I personally used chroma and qdrant)

- subsystems to build agent's logic (langgraph based) - with some web ui (not really suitable for editing at the moment)

- required MCP servers - web search (bravesearch based, you will need to provide your own api key), rag mcp server (to work with vector databases, including embedding conversions and reranking), sql mcp server (to query databases), dns mcp server (this is the simplest and fastest to test mcp integrations), download mcp server (i use it to download full web page content, returned from web search)

- web ui to do queries to agent, and also separate tabs to import documents, do direct vector db requests, do direct web search resuest - this is very helpful for hyphotesis testing (how to chunk documents, test different embedding models and so on)

i have to mention, that whole source code was written by qwen code as part of experiment to find out if it can be done without any knowledge in it (fortunately/unfortunately - i found it's not (yet) possible).  so if you will need to change/fix something, just use some vibe coding agent to do so.
i done it for myself, but will be happy if it will help somebody else.


but yes, then rewritten by llm model :)
--
What follows is a purpose-built experimentation suite for hands-on exploration of Retrieval-Augmented Generation. Designed not as a polished product but as a laboratory for inquiry, it provides every component necessary to formulate, test, and refine hypotheses about RAG systems:
Document pipeline subsystems for importing, processing, storing, and retrieving content—anchored by vector databases (I've worked extensively with Chroma and Qdrant).
Agent orchestration via LangGraph, structuring reasoning workflows with deliberate modularity—accompanied by a functional web interface (currently optimized for interaction rather than authoring).
A constellation of MCP servers, each serving a distinct investigative purpose:
Web search (BraheSearch-backed) for external knowledge grounding
RAG MCP for vector operations, embedding transformations, and reranking
SQL MCP for structured data interrogation
DNS MCP—the simplest and swiftest path to validating MCP integration mechanics
Download MCP, which I employ to capture full-page content from search results
A unified web interface offering not only agent querying but dedicated workspaces for document ingestion, direct vector database inspection, and raw web search execution—each tab a sandbox for methodical hypothesis testing: chunking strategies, embedding model comparisons, retrieval tuning, and beyond.
A candid disclosure: the entire codebase emerged from an experiment with Qwen Code—an attempt to determine whether a capable developer could be synthesized from pure promptcraft, absent domain knowledge. The verdict? Not yet. Human intuition, architectural judgment, and debugging tenacity remain irreplaceable. Should you wish to adapt or repair anything within the suite, I recommend enlisting a "vibe-coding" agent as collaborator—but keep a human hand on the tiller.
I built this for my own curiosity. If it proves useful to another explorer on the same path, all the better.
---


# AI Agent experimenal suite with MCP, vector db and other subsystems 

This AI agent processes natural language requests from users and leverages a flexible Model Context Protocol (MCP) architecture to interact with various services and tools. The system is built with an enhanced LangGraph-based architecture for complex workflows with sophisticated error handling and recovery mechanisms.

## Architecture

The AI agent consists of multiple interconnected components that work together:

1. **MCP Service Discovery**: Discovers and interacts with MCP services via registry
2. **MCP Service Execution**: Executes tool calls to various MCP services (RAG, Search, SQL, DNS, etc.)
3. **RAG (Retrieval-Augmented Generation)**: Retrieves and utilizes external documents to supplement responses
4. **Prompt Generator**: Creates detailed prompts for the response LLM based on query results
5. **Response Generator**: Uses an LLM to create natural language responses

## Enhanced LangGraph Architecture

The v0.5 version of the agent uses LangGraph to provide:
- Stateful workflow management with comprehensive state tracking
- Conditional logic for validation and error handling
- Advanced error recovery mechanisms with configurable retry limits
- Detailed execution monitoring and logging
- Multi-provider LLM support (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- MCP (Model Context Protocol) integration for external service interaction
- Flexible architecture supporting various tools and services

### LangGraph Nodes:
1. **get_schema**: Retrieves database schema information from all available databases
2. **discover_services**: Discovers MCP services from the registry
3. **query_mcp_services**: Queries MCP services for information before attempting database queries
4. **generate_sql**: Creates SQL queries from natural language requests
5. **validate_sql**: Performs safety and validation checks (with optional advanced LLM-based analysis)
6. **execute_sql**: Executes the SQL query against all databases
7. **refine_sql**: Improves queries based on errors or feedback
8. **security_check_after_refinement**: Performs security check on refined SQL query
9. **generate_wider_search_query**: Generates alternative queries when initial query returns no results
10. **execute_wider_search**: Executes the wider search query
11. **generate_prompt**: Creates specialized prompts for response generation
12. **generate_response**: Creates natural language responses from results
13. **execute_mcp_tool_calls_and_return**: Executes MCP tool calls and returns results when both prompt and response generation are disabled
14. **return_mcp_response_to_llm**: Returns MCP responses directly to the LLM model when initiated by the LLM
15. **await_mcp_response**: Awaits MCP response from the LLM model that was called with the MCP results

### Conditional Logic:
- **should_skip_database_operations**: Determines if database operations should be skipped based on the `disable_databases` flag
- **should_generate_sql_after_mcp_query**: Routes to appropriate nodes based on MCP service results and database availability
- **route_after_validation**: Routes to appropriate execution node based on query type and validation results
- **should_execute_wider_search**: Determines if wider search should be performed when initial query returns no results
- **should_refine_or_respond**: Determines if SQL should be refined or response generated based on errors and retry count
- **should_validate_after_security_check**: Determines if validation should occur after security check or proceed to response
- **should_continue_wider_search**: Determines next step after executing wider search based on results and errors
- **should_skip_prompt_and_response_generation**: Skips prompt/response generation when both are disabled
- **route_after_mcp_execution**: Routes MCP results to user or back to LLM for processing

## Key Features

### MCP (Model Context Protocol) Architecture
- **Service Discovery**: Automatically discovers available MCP services via registry
- **Flexible Tool Integration**: Supports various types of services (RAG, Search, SQL, DNS, etc.)
- **Dynamic Tool Calling**: Generates and executes appropriate tool calls based on user requests
- **Registry-Based Service Management**: Centralized service registry for service discovery and management
- **Dedicated MCP Model**: Specialized model for optimized MCP-related queries and tool generation

### MCP Services Ecosystem
- **RAG Service**: Provides document retrieval and ingestion capabilities
- **Search Service**: Enables web search functionality via Brave Search API
- **SQL Service**: Handles database query generation and execution
- **DNS Service**: Resolves hostnames to IP addresses
- **Extensible Architecture**: Easy to add new MCP services following the same pattern

### RAG (Retrieval-Augmented Generation) Support
- Retrieve and utilize external documents to supplement responses
- Support for various document formats (PDF, DOCX, TXT, HTML, MD)
- Vector storage and similarity search capabilities
- Seamless integration with existing LangGraph workflow
- Configurable embedding models and vector stores
- Automatic fallback to traditional approaches when appropriate

### Enhanced Error Handling
- Automatic retry mechanisms when service calls fail (up to 10 attempts)
- Graceful degradation when service queries fail
- Feedback loops to improve query generation
- Prevention of infinite loops during refinement
- Comprehensive error tracking across all node executions

### Database Support (Optional)
- Connect to multiple databases simultaneously (when enabled)
- Aggregate schema information from all databases
- Execute queries across all databases and combine results
- Map original table names to their respective databases
- Cross-database query execution support

### Advanced Security Analysis
- Basic keyword matching for harmful SQL commands
- Advanced LLM-based security analysis to reduce false positives
- Context-aware analysis that considers database schema
- Configurable security policies via environment variables
- Support for both basic keyword matching and advanced LLM-based analysis
- Security validation after query refinement

### Default Model Configuration
- Simplified configuration when using the same model for all tasks
- Reduces the number of environment variables to manage
- Provides a fallback when specific configurations are not set
- Supports disabling specific model components to optimize performance

### Configurable Component Disabling
- Option to disable database operations entirely
- Option to disable prompt generation for performance optimization
- Option to disable response generation for performance optimization
- Option to disable SQL blocking for trusted environments

## Workflow

### Enhanced LangGraph Architecture:
1. User submits a natural language request
2. The `get_schema` node retrieves database schema information from all available databases (if databases are enabled)
3. The `discover_services` node discovers MCP services from the registry
4. The `query_mcp_services` node queries MCP services for information before attempting database queries
5. Based on MCP results and database availability, the system routes to appropriate nodes:
   - If databases are disabled and MCP tool calls exist → `execute_mcp_tool_calls_and_return`
   - If databases are disabled and MCP results are sufficient → `generate_prompt`
   - If databases are enabled and MCP results should go to LLM → `return_mcp_response_to_llm`
   - Otherwise → `generate_sql`
6. The `generate_sql` node creates a SQL query from the request and schema
7. The `validate_sql` node performs safety checks (with optional advanced LLM-based analysis)
8. Based on validation results and query type, the system routes to:
   - If validation failed → `refine_sql`
   - If query type is 'wider_search' → `execute_wider_search`
   - Otherwise → `execute_sql`
9. The `execute_sql` node executes the query against all databases
10. If initial query returns no results or has execution errors, the system may route to:
   - `generate_wider_search_query` and `execute_wider_search` for alternative strategies
   - Otherwise → `generate_prompt`
11. If validation or execution fails, the `refine_sql` node improves the query
12. The `security_check_after_refinement` node validates refined queries for security issues
13. Based on security check results, the system routes to:
   - If security check failed → `validate_sql` (for further refinement)
   - Otherwise → `execute_sql` (to execute the secured refined query)
14. The `generate_prompt` node creates a specialized prompt for response generation
15. If both prompt and response generation are disabled, the system routes to `execute_mcp_tool_calls_and_return`
16. Otherwise, the `generate_response` node creates a natural language response from results
17. If MCP results need to be returned to LLM, the system goes through `return_mcp_response_to_llm` and `await_mcp_response`
18. The final response is returned to the user

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the application:
   You can either use the interactive configuration script or manually set up your environment:

   Using the configuration script:
   ```bash
   python setup_config.py
   ```

   Or manually set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and other configurations
   ```

3. Run the AI agent with MCP services:
   ```bash
   ./run_me.sh
   ```

## Usage

You can run the AI agent in interactive mode or pass a request directly:

```bash
# Interactive mode
python main.py

# Direct request
python main.py --request "What is the current URALS price?"
```

## Configuration

The agent can be configured via environment variables in the `.env` file:

### LLM Configuration
- `SQL_LLM_MODEL`: Model to use for SQL generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `RESPONSE_LLM_MODEL`: Model to use for response generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `PROMPT_LLM_MODEL`: Model to use for prompt generation (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `SQL_LLM_PROVIDER`: Provider for SQL generation (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama, default)
- `RESPONSE_LLM_PROVIDER`: Provider for response generation
- `PROMPT_LLM_PROVIDER`: Provider for prompt generation
- `SECURITY_LLM_PROVIDER`: Provider for security analysis
- `SQL_LLM_HOSTNAME`: Hostname for SQL LLM service (for non-OpenAI providers)
- `SQL_LLM_PORT`: Port for SQL LLM service (for non-OpenAI providers)
- `SQL_LLM_API_PATH`: API path for SQL LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_HOSTNAME`: Hostname for response LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_PORT`: Port for response LLM service (for non-OpenAI providers)
- `RESPONSE_LLM_API_PATH`: API path for response LLM service (for non-OpenAI providers)
- `PROMPT_LLM_HOSTNAME`: Hostname for prompt LLM service (for non-OpenAI providers)
- `PROMPT_LLM_PORT`: Port for prompt LLM service (for non-OpenAI providers)
- `PROMPT_LLM_API_PATH`: API path for prompt LLM service (for non-OpenAI providers)
- `SECURITY_LLM_HOSTNAME`: Hostname for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_PORT`: Port for security LLM service (for non-OpenAI providers)
- `SECURITY_LLM_API_PATH`: API path for security LLM service (for non-OpenAI providers)

### Default Model Configuration
- `DEFAULT_LLM_PROVIDER`: Provider to use when specific configurations are not provided (e.g., 'LM Studio', 'OpenAI', 'Ollama', 'default')
- `DEFAULT_LLM_MODEL`: Model name to use as default
- `DEFAULT_LLM_HOSTNAME`: Hostname of the default LLM service
- `DEFAULT_LLM_PORT`: Port of the default LLM service
- `DEFAULT_LLM_API_PATH`: API path for the default LLM service

### API Keys
- `OPENAI_API_KEY`: API key for OpenAI services
- `GIGACHAT_CREDENTIALS`: Your GigaChat authorization credentials
- `GIGACHAT_SCOPE`: The scope for your GigaChat API access (default: GIGACHAT_API_PERS)
- `BRAVE_SEARCH_API_KEY`: API key for Brave Search functionality

### Security Configuration
- `SECURITY_LLM_MODEL`: Model to use for security analysis (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `USE_SECURITY_LLM`: Whether to use the advanced security LLM analysis (default: true)
- `TERMINATE_ON_POTENTIALLY_HARMFUL_SQL`: Whether to block potentially harmful SQL (default: true)

### Logging Configuration
- `ENABLE_SCREEN_LOGGING`: Enable detailed logging output (default: false)

### Model Component Disabling
- `DISABLE_PROMPT_GENERATION`: Skip the prompt generation LLM to optimize performance
- `DISABLE_RESPONSE_GENERATION`: Skip the response generation LLM to optimize performance

### MCP Configuration
- `MCP_LLM_PROVIDER`: Provider for MCP service queries (default: LM Studio)
- `MCP_LLM_MODEL`: Model for MCP service queries (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `MCP_LLM_HOSTNAME`: Hostname for MCP LLM service (default: localhost)
- `MCP_LLM_PORT`: Port for MCP LLM service (default: 1234)
- `MCP_LLM_API_PATH`: API path for MCP LLM service (default: /v1)
- `REGISTRY_URL`: URL of the MCP registry server (can be passed via command line as well)

### Dedicated MCP Model Configuration
- `DEDICATED_MCP_LLM_PROVIDER`: Provider for dedicated MCP-related queries (default: LM Studio)
- `DEDICATED_MCP_LLM_MODEL`: Model for dedicated MCP-related queries (default: qwen2.5-coder-7b-instruct-abliterated@q3_k_m)
- `DEDICATED_MCP_LLM_HOSTNAME`: Hostname for dedicated MCP LLM service (default: localhost)
- `DEDICATED_MCP_LLM_PORT`: Port for dedicated MCP LLM service (default: 1234)
- `DEDICATED_MCP_LLM_API_PATH`: API path for dedicated MCP LLM service (default: /v1)

### Database Configuration (Optional)
- `DATABASE_URL`: PostgreSQL connection string for default database
- `DB_{NAME}_URL`: Connection string for additional databases (e.g., `DB_ANALYTICS_URL`)
- `DB_{NAME}_TYPE`: Database type (postgresql, mysql, sqlite, etc.)
- `DB_{NAME}_USERNAME`: Database username
- `DB_{NAME}_PASSWORD`: Database password
- `DB_{NAME}_HOSTNAME`: Database hostname
- `DB_{NAME}_PORT`: Database port
- `DB_{NAME}_NAME`: Database name
- `DISABLE_DATABASES`: Flag to disable all database operations (default: false)
- `DEFAULT_DATABASE_ENABLED`: Flag to specifically enable/disable the default database (default: true)

### Authentication Service Database Initialization
To initialize the PostgreSQL database for the authentication service:
1. Ensure PostgreSQL is installed and running
2. Create a database for the application (e.g., `ai_agent_db`)
3. Set the database connection parameters in your `.env` file:
   ```
   DB_TYPE=postgresql
   DB_USERNAME=your_db_username
   DB_PASSWORD=your_db_password
   DB_HOSTNAME=localhost
   DB_PORT=5432
   DB_NAME=ai_agent_db
   DATABASE_URL=postgresql://your_db_username:your_db_password@localhost:5432/ai_agent_db
   ```
4. The authentication service will automatically create the required `users` table on startup

### RAG Configuration
- `RAG_ENABLED`: Enable or disable RAG functionality (default: true)
- `RAG_EMBEDDING_MODEL`: Model to use for embeddings (default: all-MiniLM-L6-v2)
- `RAG_VECTOR_STORE_TYPE`: Type of vector store to use (default: chroma)
- `RAG_TOP_K_RESULTS`: Number of results to retrieve (default: 5)
- `RAG_SIMILARITY_THRESHOLD`: Minimum similarity threshold (default: 0.7)
- `RAG_CHUNK_SIZE`: Size of text chunks (default: 1000)
- `RAG_CHUNK_OVERLAP`: Overlap between chunks (default: 100)
- `RAG_CHROMA_PERSIST_DIR`: Directory for Chroma persistence (default: ./data/chroma_db)
- `RAG_COLLECTION_NAME`: Name of the Chroma collection (default: documents)
- `RAG_SUPPORTED_FILE_TYPES`: Supported file types (default: .txt,.pdf,.docx,.html,.md)

## Security

- SQL queries are validated to prevent harmful commands (no DROP, DELETE, INSERT, UPDATE, etc.)
- Only SELECT and WITH queries are allowed by default
- Connection parameters are loaded from environment variables
- Advanced security LLM analysis to reduce false positives
- Multiple layers of protection against SQL injection
- Configurable security policies via environment variables
- Security check after refinement to ensure refined queries are safe
- Protection against SQL injection through pattern detection and comment filtering

### Advanced Security LLM Analysis

The agent now includes an advanced security analysis feature that uses an LLM to detect potentially harmful SQL queries while reducing false positives. This addresses issues where legitimate column names like `created_at` were incorrectly flagged as harmful due to containing substrings like "create".

The security LLM analysis:
- Distinguishes between legitimate column/table names and actual malicious commands
- Reduces false positives compared to simple keyword matching
- Provides contextual analysis based on the database schema
- Offers confidence levels for security assessments
- Supports multiple LLM providers for security analysis (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)

By default, the security LLM is enabled. You can disable it by setting `USE_SECURITY_LLM=false`.

### Disabling SQL Blocking

To disable the SQL blocking feature, you can:

1. Pass `disable_sql_blocking=True` when calling `run_enhanced_agent()`:
   ```python
   result = run_enhanced_agent("Your request", disable_sql_blocking=True)
   ```

2. Set the environment variable `USE_SECURITY_LLM=false`:
   ```bash
   export USE_SECURITY_LLM=false
   ```

**Warning:** Disabling SQL blocking can pose security risks and should only be done in trusted environments.

## GigaChat Integration

The project now supports GigaChat models with OAuth token-based authentication:

### GigaChat Specific Variables
- `GIGACHAT_CREDENTIALS`: Your GigaChat authorization credentials
- `GIGACHAT_SCOPE`: The scope for your API access (default: `GIGACHAT_API_PERS`)
  - `GIGACHAT_API_PERS` - Personal API access
  - `GIGACHAT_API_B2B` - Business-to-business API access
  - `GIGACHAT_API_CORP` - Corporate API access
- `GIGACHAT_ACCESS_TOKEN`: Pre-generated access token (optional, if using credentials instead)
- `GIGACHAT_VERIFY_SSL_CERTS`: Whether to verify SSL certificates (default: `true`). Set to `false` to disable SSL verification for self-signed certificates.

### Model Provider Configuration
Set the provider to `GigaChat` for any of the model components:
- `SQL_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for SQL generation
- `RESPONSE_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for response generation
- `PROMPT_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for prompt generation
- `SECURITY_LLM_PROVIDER`: Set to `GigaChat` to use GigaChat for security analysis

## Monitoring and Observability

Detailed logs are available for each node execution:
- `[NODE START]` - When a node begins processing
- `[NODE SUCCESS]` - When a node completes successfully
- `[NODE ERROR]` - When a node encounters an error
- `[NODE WARNING]` - When a node generates a warning
- `[GRAPH START]` - When the graph begins execution
- `[GRAPH END]` - When the graph completes execution
- `[TIME]` - Execution time measurements for performance analysis

## Performance Considerations

- Each node is timed for performance analysis
- Retry limits prevent infinite loops (maximum 10 attempts)
- Schema caching reduces database load
- Error handling prevents cascading failures
- Wider search strategies are limited to prevent excessive database queries
- Multi-database schema aggregation is cached for efficiency
- Configurable component disabling for performance optimization

## Troubleshooting

If you encounter issues:

1. Check the logs for detailed error information
2. Verify LLM configurations are correct
3. Ensure MCP registry and services are running
4. Review the execution log for the sequence of operations
5. If using wider search strategies, verify that schema information is complete
6. For security analysis issues, ensure the security LLM is properly configured
7. For MCP integration issues, verify registry URL and service availability
8. If experiencing recursion limit errors, simplify your request or check for complex query patterns

## LangGraph Workflow Visualization and Editing Interfaces

The LangGraph Visual Editor suite provides specialized tools for visualizing, analyzing, and editing the LangGraph workflow that powers the AI agent. These interfaces are specifically designed for workflow development and debugging rather than direct AI agent interaction.

### Available Interfaces

- **Main Dashboard** (Port 8000): Central access point for all LangGraph workflow tools
- **Enhanced Streamlit Editor** (Port 8501): Comprehensive visualization and debugging environment
- **React Flow Editor** (Port 3000): Interactive workflow editor with drag-and-drop capabilities

### Starting the Interface Suite

The recommended way to start all LangGraph workflow interfaces is through the dedicated GUI script:

```bash
./start_gui.sh
```

This will:
- Launch the main dashboard on http://localhost:8000
- Automatically start the Streamlit editor on http://localhost:8501
- Provide access instructions for the React editor

### Individual Components

#### Enhanced Streamlit Editor
The primary interface for LangGraph workflow analysis and debugging:

Option 1: Using the dedicated GUI script (recommended):
```bash
./start_gui.sh
```

Option 2: Using the all-services script:
```bash
./start_all_services.sh
```

Option 3: Standalone access:
```bash
cd gui
streamlit run enhanced_streamlit_app.py
```

Then navigate to http://localhost:8501 in your browser.

**Features:**
- **Visualization Tab**: Interactive graph visualization with node coloring by type (database, MCP, response, LLM-calling nodes)
- **Workflow Editing**: Conceptual editing of nodes and edges (actual changes require code modification)
- **Detailed Node Information**: Comprehensive information about each node's purpose, logic, and conditional pathways
- **Simulation Mode**: Run the workflow with sample inputs and different configurations
- **Debugging Tools**: Set breakpoints, step through execution, and monitor execution history
- **State Visualization**: Track state changes throughout workflow execution
- **Export/Import**: Save and load workflow definitions

#### React Flow Editor
Advanced workflow editing interface using React Flow:

1. Navigate to the React editor directory:
   ```bash
   cd gui/react_editor
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Access the React editor at http://localhost:3000

**Features:**
- **Interactive Canvas**: Drag-and-drop interface for workflow visualization
- **Node Inspection**: Detailed view of node properties, logic, and conditional pathways
- **Real-time Sync**: Automatically syncs with the current LangGraph workflow structure
- **Export Capabilities**: Export workflows as JSON or Python LangGraph code
- **API Integration**: Communicates with the workflow API running on port 5001

### LangGraph-Specific Capabilities

These interfaces provide specialized tools for understanding and modifying the LangGraph workflow:

- **Node Type Classification**: Color-coded visualization of different node types:
  - Green: Start/end nodes
  - Blue: Database operation nodes
  - Orange: MCP (Model Context Protocol) nodes
  - Yellow: Response generation nodes
  - Pink: LLM-calling nodes
  - White: Default nodes

- **Conditional Logic Visualization**: Clear representation of decision points and routing logic
- **Execution Path Analysis**: Understanding how the workflow transitions between nodes based on conditions
- **LLM Integration Points**: Identification of nodes that make calls to various LLMs (SQL, Response, Prompt, Security, MCP)
- **Debugging Support**: Tools to pause execution at specific nodes and inspect state

### Prerequisites

For the Streamlit editor, ensure you have installed the required dependencies by running `pip install -r requirements.txt` in the gui directory or the main project directory.

For the React editor, you'll also need Node.js and npm installed on your system.

## Service Management Scripts

The project includes several scripts to manage the GUI services:

### Starting Services
- `start_gui.sh`: Starts the main dashboard and Streamlit editor
- `start_all_services.sh`: Starts all GUI services (React Editor, Streamlit App, LangGraph Studio, and Workflow API)

### Stopping Services
- `stop_all_gui_services.sh`: Stops all running GUI services

### Checking Service Status
- `check_gui_services.sh`: Checks the status of all GUI services and reports which ones are running

To use these scripts:
```bash
# Start all services
./start_all_services.sh

# Check service status
./check_gui_services.sh

# Stop all services
./stop_all_gui_services.sh
```
