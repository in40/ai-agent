#!/usr/bin/env python3
"""Quick LaTeX conversion test - single formula"""
import re
from openai import OpenAI

# Read .env
with open('/root/qwen/ai_agent/.env', 'r') as f:
    env_content = f.read()

model_match = re.search(r'^NLP_LLM_MODEL=(.+)$', env_content, re.MULTILINE)
url_match = re.search(r'^NLP_LLM_BASE_URL=(.+)$', env_content, re.MULTILINE)

llm_model = model_match.group(1).strip()
llm_base_url = url_match.group(1).strip()

print(f"Using: {llm_base_url} / {llm_model}\n")

client = OpenAI(base_url=llm_base_url, api_key="not-needed")

latex = r"$$S^C_{MAC} = KDF(K_{in}, label, seed) = HMAC_{256}(K_{in}, 0x01 || label || 0x00 || seed || 0x01 || 0x00),$$"

print(f"Original LaTeX:\n{latex}\n")

prompt = f"Convert to natural language, return ONLY the conversion:\n{latex}"

print("Calling LLM...")
response = client.chat.completions.create(
    model=llm_model,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.1,
    timeout=60
)

print(f"\nLLM Response:\n{response.choices[0].message.content}\n")
