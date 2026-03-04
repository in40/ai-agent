#!/usr/bin/env python3
from models.response_generator import ResponseGenerator
from config.settings import RESPONSE_LLM_PROVIDER, RESPONSE_LLM_MODEL

rg = ResponseGenerator()
llm = rg._get_llm_instance(provider=RESPONSE_LLM_PROVIDER, model=RESPONSE_LLM_MODEL)

# Test with simple message
try:
    response = llm.invoke("Hello, respond with JSON: {\"test\": 1}")
    print(f"Response: {response.content if hasattr(response, 'content') else response}")
except Exception as e:
    print(f"Error: {e}")
