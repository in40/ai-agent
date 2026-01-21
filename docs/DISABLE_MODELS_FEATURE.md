# Disable Models Feature Documentation

## Overview

This feature allows users to selectively disable different LLM model components in the AI agent system. This is useful for:
- Reducing computational costs when certain capabilities aren't needed
- Improving response times by bypassing unnecessary processing
- Testing and development purposes
- Compliance with resource constraints

## Configuration Options

The following environment variables can be set to control which models are disabled:

### `DISABLE_PROMPT_GENERATION`
- Type: Boolean (`true`/`false` or `1`/`0`)
- Default: `false`
- When set to `true`, disables the prompt generation LLM model

### `DISABLE_RESPONSE_GENERATION`
- Type: Boolean (`true`/`false` or `1`/`0`)
- Default: `false`
- When set to `true`, disables the response generation LLM model

## Behavior

### When `DISABLE_PROMPT_GENERATION` is enabled:
- The system will skip the specialized prompt generation step
- A default prompt will be used instead: `"Based on the user request '{user_request}' and the following database results, generate a natural language response:"`
- The workflow will continue to the response generation step

### When `DISABLE_RESPONSE_GENERATION` is enabled:
- The system will skip the response generation LLM model
- Raw database results will be formatted as a simple response
- If database results exist, they will be returned in JSON format
- If no results exist, the response will be "No results found for the query."

### When both are disabled:
- The system will skip both prompt and response generation
- It will proceed directly to the final response step with MCP-capable model response

### When neither is disabled:
- The system operates normally with both prompt and response generation enabled

## Example Usage

### Using Environment Variables
```bash
# Disable only prompt generation
export DISABLE_PROMPT_GENERATION=true

# Disable only response generation
export DISABLE_RESPONSE_GENERATION=true

# Disable both
export DISABLE_PROMPT_GENERATION=true
export DISABLE_RESPONSE_GENERATION=true
```

### Using .env file
```env
# In your .env file
DISABLE_PROMPT_GENERATION=true
DISABLE_RESPONSE_GENERATION=false
```

## Implementation Details

The feature is implemented in the following components:

1. **Configuration**: Defined in `config/settings.py` with `str_to_bool` conversion
2. **Prompt Generation**: Modified in `langgraph_agent/langgraph_agent.py` in the `generate_prompt_node` function
3. **Response Generation**: Modified in `langgraph_agent/langgraph_agent.py` in the `generate_response_node` function
4. **Workflow Logic**: Updated conditional logic handles the different combinations of enabled/disabled models

## Testing

The feature includes comprehensive tests in `core/tests/test_disable_models.py` that verify:
- Configuration options are properly defined
- Agent state has required fields
- Workflow nodes exist and function correctly
- Both prompt and response generation logic work as expected