# LangChain Implementation in AI Agent

## Overview

This AI Agent project utilizes LangChain for creating language model chains that process natural language requests into SQL queries and then into natural language responses. The implementation uses LangChain's Expression Language (LCEL) to create composable chains of prompts, models, and output parsers.

**Important Note**: This project includes both a traditional linear architecture using LangChain's LCEL (LangChain Expression Language) for simple, linear chains of operations, and an enhanced architecture using LangGraph for complex, stateful workflows.

## Traditional Linear Architecture

The traditional system is built around three main LangChain-based components:

1. **SQLGenerator**: Converts natural language to SQL queries
2. **PromptGenerator**: Creates prompts for the response generation
3. **ResponseGenerator**: Generates natural language responses from database results

Each component follows the same pattern:
- ChatPromptTemplate → LLM → OutputParser → Chain

## Enhanced LangGraph Architecture

The enhanced system uses LangGraph to create a stateful, graph-based workflow with the following nodes:

1. **get_schema**: Retrieves database schema information
2. **generate_sql**: Creates SQL queries from natural language requests
3. **validate_sql**: Performs safety and validation checks (with optional advanced LLM-based analysis)
4. **execute_sql**: Executes the SQL query against the database
5. **refine_sql**: Improves queries based on errors or feedback
6. **generate_wider_search_query**: Generates alternative queries when initial query returns no results
7. **execute_wider_search**: Executes the wider search query
8. **generate_prompt**: Creates specialized prompts for response generation
9. **generate_response**: Creates natural language responses from results

## Detailed Component Analysis

### 1. SQLGenerator

The SQLGenerator is responsible for converting natural language requests into SQL queries.

#### Code Structure:
```python
from pydantic import BaseModel, Field

class SQLOutput(BaseModel):
    """Structured output for SQL generation"""
    sql_query: str = Field(description="The generated SQL query")

class SQLGenerator:
    def __init__(self):
        # Initialize LLM based on configuration
        if SQL_LLM_PROVIDER.lower() == 'gigachat':
            self.llm = GigaChatModel(...).with_structured_output(SQLOutput)
        else:
            self.llm = ChatOpenAI(...).with_structured_output(SQLOutput)

        # Define the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL developer..."""),
            ("human", "{user_request}")
        ])

        # Create the chain - no need for separate output parser since we're using with_structured_output
        self.chain = self.prompt | self.llm

    def generate_sql(self, user_request, schema_dump, attached_files=None):
        response = self.chain.invoke({
            "user_request": user_request,
            "schema_dump": schema_str
        })

        # Since we're using Pydantic parser, the response should already be structured
        if isinstance(response, SQLOutput):
            sql_query = response.sql_query
        else:
            # Fallback to cleaning the string response if structured parsing fails
            sql_query = self.clean_sql_response(str(response))

        return sql_query
```

#### Chain Breakdown:
- **Prompt Template**: Provides the database schema and instructions to generate SQL
- **LLM**: Processes the prompt and generates a response
- **Output Parser**: Converts the LLM response to a string
- **Chain**: Combines all components using the `|` operator (LCEL syntax)

### 2. PromptGenerator

The PromptGenerator creates detailed prompts for the response LLM based on user requests and database results.

#### Code Structure:
```python
class PromptGenerator:
    def __init__(self):
        # Initialize LLM based on configuration
        if PROMPT_LLM_PROVIDER.lower() == 'gigachat':
            self.llm = GigaChatModel(...)
        else:
            self.llm = ChatOpenAI(...)

        # Define the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating detailed prompts..."""),
            ("human", """Original user request: {user_request}

            Database query results: {db_results}

            Create a detailed prompt for another LLM...""")
        ])

        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def generate_prompt_for_response_llm(self, user_request, db_results):
        results_str = self.format_db_results(db_results)
        response = self.chain.invoke({
            "user_request": user_request,
            "db_results": results_str
        })
        return response

    def generate_wider_search_prompt(self, wider_search_context, attached_files=None):
        """
        Generate a prompt for wider search strategies when initial query returns no results
        """
        wider_search_prompt = self.prompt.invoke({
            "user_request": "Generate wider search strategies",
            "db_results": wider_search_context
        })
        return wider_search_prompt
```

### 3. ResponseGenerator

The ResponseGenerator creates natural language responses based on the generated prompt.

#### Code Structure:
```python
from pydantic import BaseModel, Field

class ResponseOutput(BaseModel):
    """Structured output for response generation"""
    response_text: str = Field(description="The generated natural language response")

class ResponseGenerator:
    def __init__(self):
        # Initialize LLM based on configuration
        if RESPONSE_LLM_PROVIDER.lower() == 'gigachat':
            self.llm = GigaChatModel(...)
        else:
            self.llm = ChatOpenAI(...)

        # Define the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at converting database results into natural language responses."),
            ("human", "{generated_prompt}")
        ])

        # Create the output parser
        self.output_parser = StrOutputParser()

        # Create the chain with the parser
        self.chain = self.prompt | self.llm | self.output_parser

    def generate_natural_language_response(self, generated_prompt, attached_files=None):
        response = self.chain.invoke({
            "generated_prompt": generated_prompt
        })

        # Try to parse as structured output first
        try:
            # Attempt to parse the response with the Pydantic parser
            parser = PydanticOutputParser(pydantic_object=ResponseOutput)
            structured_response = parser.parse(response)
            response_text = structured_response.response_text
        except Exception:
            # Fallback to returning the string response if structured parsing fails
            response_text = response

        return response_text
```

## LCEL (LangChain Expression Language) Usage

The project extensively uses LCEL for creating chains:

```python
# Example from SQLGenerator
self.chain = self.prompt | self.llm | self.output_parser
```

This creates a functional composition where:
1. The prompt template is formatted with input variables
2. The formatted prompt is sent to the LLM
3. The LLM response is parsed by the output parser

## Custom GigaChat Integration

The project includes a custom GigaChat integration that extends LangChain's BaseChatModel:

```python
class GigaChatModel(BaseChatModel):
    # Configuration fields
    model: str = Field(default="GigaChat:latest")
    credentials: Optional[str] = Field(default=None)
    scope: Optional[str] = Field(default="GIGACHAT_API_PERS")
    access_token: Optional[str] = Field(default=None)
    verify_ssl_certs: bool = Field(default=True)
    # ... other fields

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Convert LangChain messages to GigaChat format
        gigachat_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                gigachat_messages.append(Messages(role="user", content=msg.content))
            # ... handle other message types

        # Handle authentication and make API call
        if self.access_token:
            # Use pre-generated access token
            headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            # Use credentials to obtain access token via OAuth
            headers = self._get_oauth_headers()

        # Make API call and convert response back to LangChain format
        response = self._client.chat(chat_request)
        content = response.choices[0].message.content
        generation = ChatGeneration(
            message=AIMessage(content=content),
            generation_info={
                "finish_reason": response.choices[0].finish_reason,
                "model": response.model,
            }
        )
        return ChatResult(generations=[generation])
```

## Configuration and Flexibility

The system is designed to work with multiple LLM providers:

- OpenAI
- GigaChat
- Local models (via LM Studio, Ollama, etc.)
- Cloud providers (DeepSeek, Qwen)

Configuration is handled through environment variables in the `config/settings.py` file.

### Multi-Provider Support

The system supports different LLM providers for different components:

- `SQL_LLM_PROVIDER`: Provider for SQL generation (OpenAI, GigaChat, DeepSeek, Qwen, LM Studio, Ollama)
- `RESPONSE_LLM_PROVIDER`: Provider for response generation
- `PROMPT_LLM_PROVIDER`: Provider for prompt generation
- `SECURITY_LLM_PROVIDER`: Provider for security analysis

Each provider can be configured with:
- Model name
- Hostname and port
- API path
- Authentication credentials

## Workflow Integration

The LangChain components are integrated into the main AI Agent workflow:

```
User Request → SQLGenerator → SQL Query → SQLExecutor → DB Results
DB Results + User Request → PromptGenerator → Generated Prompt
Generated Prompt → ResponseGenerator → Natural Language Response
```

## Key Benefits of This Approach

1. **Modularity**: Each component is independent and can be configured separately
2. **Flexibility**: Different LLMs can be used for different tasks (SQL generation, response generation, etc.)
3. **Composability**: LCEL allows for easy chaining of components
4. **Maintainability**: Clear separation of concerns between prompting, model selection, and output processing
5. **Extensibility**: Easy to add new nodes and functionality to the LangGraph workflow

## Diagram

### Traditional Linear Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  User Request   │───▶│  SQLGenerator   │───▶│  SQL Executor   │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│  │Natural    │  │    │ │ChatPrompt   │ │    │ │Database     │ │
│  │Language   │  │    │ │Template     │ │    │ │Query        │ │
│  │Request    │  │    │ └─────────────┘ │    │ │Execution    │ │
│  └───────────┘  │    │        │        │    │ └─────────────┘ │
└─────────────────┘    │        ▼        │    └─────────────────┘
                       │ ┌─────────────┐  │              │
                       │ │LLM (Chat   │  │              ▼
                       │ │OpenAI/     │  │    ┌─────────────────┐
                       │ │GigaChat)   │  │    │ PromptGenerator │
                       │ └─────────────┘  │    │                 │
                       │        │        │    │ ┌─────────────┐ │
                       │        ▼        │    │ │ChatPrompt   │ │
                       │ ┌─────────────┐  │    │ │Template     │ │
                       │ │Structured   │  │    │ └─────────────┘ │
                       │ │Output       │  │    │        │        │
                       │ │Parser       │  │    │        ▼        │
                       └─────────────────┘    │ ┌─────────────┐  │
                                              │ │LLM (Chat   │  │
                                              │ │OpenAI/     │  │
                                              │ │GigaChat)   │  │
                                              │ └─────────────┘  │
                                              │        │        │
                                              │        ▼        │
                                              │ ┌─────────────┐  │
                                              │ │StrOutput    │  │
                                              │ │Parser       │  │
                                              │ └─────────────┘  │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ResponseGenerator│
                                              │                 │
                                              │ ┌─────────────┐ │
                                              │ │ChatPrompt   │ │
                                              │ │Template     │ │
                                              │ └─────────────┘ │
                                              │        │        │
                                              │        ▼        │
                                              │ ┌─────────────┐ │
                                              │ │LLM (Chat   │ │
                                              │ │OpenAI/     │ │
                                              │ │GigaChat)   │ │
                                              │ └─────────────┘ │
                                              │        │        │
                                              │        ▼        │
                                              │ ┌─────────────┐ │
                                              │ │StrOutput    │ │
                                              │ │Parser       │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │ Natural Language│
                                              │    Response     │
                                              └─────────────────┘
```

### Enhanced LangGraph Architecture

```
                    ┌─────────────────┐
                    │   get_schema    │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  generate_sql   │
                    └─────────┬───────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  validate_sql   │
                    └─────────┬───────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
           ┌─────────────────┐   ┌─────────────────┐
           │  execute_sql    │   │  refine_sql     │
           └─────────┬───────┘   └─────────┬───────┘
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
    └─────────┬───────┘  └─────────┬───────┘
              │                     │
              │         ┌───────────┘
              │         │
              ▼         ▼
    ┌─────────────────┐ │
    │ execute_wider_  │ │
    │ _search         │◄┘
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
│             │  │                 │
└─────────────┘  └─────────────────┘
         │                  │
         └──────────────────┘
                    │
                    ▼
           ┌────────────┐
           │   END      │
           └────────────┘
```

## Conclusion

This AI Agent project demonstrates a practical implementation of LangChain's LCEL for creating a multi-step AI workflow. The project includes both a traditional linear architecture using LangChain's LCEL for simple, sequential operations and an enhanced architecture using LangGraph for complex, stateful workflows with conditional logic, error recovery, iterative refinement, and wider search strategies. The system effectively leverages LangChain's core components to create a robust natural language to SQL conversion system with configurable LLM providers and advanced security features.