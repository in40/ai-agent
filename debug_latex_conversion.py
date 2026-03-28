#!/usr/bin/env python3
"""Debug LaTeX conversion - mimics production code exactly"""
import re
import json
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read .env config
with open('/root/qwen/ai_agent/.env', 'r') as f:
    env_content = f.read()

model_match = re.search(r'^NLP_LLM_MODEL=(.+)$', env_content, re.MULTILINE)
url_match = re.search(r'^NLP_LLM_BASE_URL=(.+)$', env_content, re.MULTILINE)

llm_model = model_match.group(1).strip()
llm_base_url = url_match.group(1).strip()

logger.info(f"Using: {llm_base_url} / {llm_model}")

# Simulate problematic JSON from LLM chunking
cleaned_response = '''
[
    {"chunk_id": 1, "content": "Test with LaTeX: S^C_{MAC} = KDF(K_{in})"}
]
'''

latex_conversion_prompt = f"""You are a LaTeX to natural language converter. Convert LaTeX formulas to plain English descriptions.

IMPORTANT:
- Return ONLY valid JSON, no explanations or reasoning
- Keep the conversion direct and concise - do not overthink
- Preserve mathematical meaning but use simple language

Problematic JSON (convert LaTeX to natural language):

{cleaned_response}
"""

logger.info("Calling LLM for LaTeX conversion...")

if "1234" in llm_base_url:
    client = OpenAI(base_url=llm_base_url, api_key="not-needed")
else:
    client = OpenAI(base_url=llm_base_url)

logger.info(f"Client created, sending request...")

try:
    latex_response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "Convert LaTeX to natural language. Return ONLY valid JSON. Be direct, do not overthink."},
            {"role": "user", "content": latex_conversion_prompt}
        ],
        temperature=0.1,
        timeout=900  # 15 minutes for complex formulas
    )
    
    logger.info(f"Response received!")
    logger.info(f"Usage: {latex_response.usage}")
    
    message = latex_response.choices[0].message
    logger.info(f"Message content length: {len(message.content or '')}")
    logger.info(f"Message reasoning length: {len(message.reasoning_content or '')}")
    
    converted_json = message.content if message.content else message.reasoning_content
    
    logger.info(f"\n=== CONVERTED JSON (first 500 chars) ===\n{converted_json[:500]}...")
    
    # Clean and parse
    converted_json = converted_json.strip()
    if converted_json.startswith('```json'):
        converted_json = converted_json[7:]
    if converted_json.endswith('```'):
        converted_json = converted_json[:-3]
    converted_json = converted_json.strip()
    
    chunking_result = json.loads(converted_json)
    logger.info(f"\n✅ SUCCESS! Parsed {len(chunking_result)} chunks")
    
except Exception as e:
    logger.error(f"❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
