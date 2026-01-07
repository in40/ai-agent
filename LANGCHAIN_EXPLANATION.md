# LangChain Implementation in AI Agent

## Overview

This AI Agent project utilizes LangChain for creating language model chains that process natural language requests into SQL queries and then into natural language responses. The implementation uses LangChain's Expression Language (LCEL) to create composable chains of prompts, models, and output parsers.

**Important Note**: This project does NOT use LangGraph. Instead, it uses LangChain's LCEL (LangChain Expression Language) for creating simple, linear chains of operations.

## Architecture

The system is built around three main LangChain-based components:

1. **SQLGenerator**: Converts natural language to SQL queries
2. **PromptGenerator**: Creates prompts for the response generation
3. **ResponseGenerator**: Generates natural language responses from database results

Each component follows the same pattern:
- ChatPromptTemplate → LLM → OutputParser → Chain

## Detailed Component Analysis

### 1. SQLGenerator

The SQLGenerator is responsible for converting natural language requests into SQL queries.

#### Code Structure:
```python
class SQLGenerator:
    def __init__(self):
        # Initialize LLM based on configuration
        if SQL_LLM_PROVIDER.lower() == 'gigachat':
            self.llm = GigaChatModel(...)
        else:
            self.llm = ChatOpenAI(...)
        
        # Define the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL developer..."""),
            ("human", "{user_request}")
        ])
        
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def generate_sql(self, user_request, schema_dump):
        response = self.chain.invoke({
            "user_request": user_request,
            "schema_dump": schema_str
        })
        # Clean up the response to extract SQL
        return self.clean_sql_response(response)
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
```

### 3. ResponseGenerator

The ResponseGenerator creates natural language responses based on the generated prompt.

#### Code Structure:
```python
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
        
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def generate_natural_language_response(self, generated_prompt):
        response = self.chain.invoke({
            "generated_prompt": generated_prompt
        })
        return response
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
    # ... other fields
    
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Convert LangChain messages to GigaChat format
        gigachat_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                gigachat_messages.append(Messages(role="user", content=msg.content))
            # ... handle other message types
        
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

## Diagram

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
                       │ │StrOutput    │  │    │ └─────────────┘ │
                       │ │Parser       │  │    │        │        │
                       │ └─────────────┘  │    │        ▼        │
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

## Conclusion

This AI Agent project demonstrates a practical implementation of LangChain's LCEL for creating a multi-step AI workflow. While it doesn't use LangGraph for complex stateful workflows, it effectively leverages LangChain's core components to create a robust natural language to SQL conversion system with configurable LLM providers.