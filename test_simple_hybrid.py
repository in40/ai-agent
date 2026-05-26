#!/usr/bin/env python3
import sys, json, requests
sys.path.insert(0, 'backend/services/rag')
from nlp_tools.entity_extractor import EntityExtractor

print("Loading...")
extractor = EntityExtractor(use_custom_types=True)

with open('document-store-mcp-server/data/ingested/job_job_3ad1455bec52_rst_gov_ru:8443/documents/gost-r-52069_2c53c42c.chunks.json', 'r') as f:
    doc = json.load(f)

print(f"Loaded {len(doc['chunks'])} chunks")
chunk = doc['chunks'][0]
text = chunk['content'][:1500]

print(f"Extracting from {len(text)} chars...")
entities = extractor.extract_all_entities(text, use_spacy=True, use_patterns=True)
print(f"Pattern: {len(entities)} entities")

print("LLM validation...")
prompt = f'Extract entities. JSON only: {{"entities": [{{"text": "...", "type": "..."}}]}}\n\nText: {text}'

response = requests.post('http://fedora:8081/v1/chat/completions',
    json={'model': 'Qwen3.5-2B-UD-Q4_K_XL.gguf', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 500},
    timeout=60)

llm_output = response.json()['choices'][0]['message']['content']
print(f"LLM: {llm_output[:200]}...")
