#!/usr/bin/env python3
"""
Analyze PDF samples with LLM to discover optimal entity types
"""
import json
import requests
import sys

# Load PDF samples (use the good encoding version)
with open("/root/qwen/ai_agent/mcp-nlp-data-scientist/pdf_samples_good.json", "r", encoding="utf-8") as f:
    pdf_samples = json.load(f)

# Load the entity discovery prompt
with open("/root/qwen/ai_agent/mcp-nlp-data-scientist/mcp_nlp_server/nlp_tools/prompts/entity_discovery_prompt.txt", "r") as f:
    prompt_template = f.read()

# Prepare document samples text
document_text = "\n\n".join([
    f"Document: {doc['file']}\nPages: {doc['pages']}\nContent:\n{doc['text'][:2000]}"
    for doc in pdf_samples
])

# Format the prompt
prompt = prompt_template.replace("{document_samples}", document_text)

print("=" * 70)
print("Sending documents to LLM for entity type discovery...")
print("=" * 70)
print(f"Documents: {[doc['file'] for doc in pdf_samples]}")
print(f"Total text length: {len(document_text)} chars")
print()

# Send to LM Studio
llm_url = "http://192.168.51.237:1234/v1/chat/completions"

payload = {
    "model": "qwen3-4b",
    "messages": [
        {
            "role": "system",
            "content": "You are an expert NLP entity extraction specialist for Russian technical standards and cybersecurity documents. Return ONLY valid JSON."
        },
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.1,
    "max_tokens": 4000
}

print("Calling LLM...")
try:
    response = requests.post(llm_url, json=payload, timeout=300)
    response.raise_for_status()
    
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    
    # Extract JSON from response
    import re
    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        content = json_match.group(0)
    
    # Parse JSON
    analysis = json.loads(content)
    
    # Save results with proper UTF-8 encoding (ensure_ascii=False)
    output_file = "/root/qwen/ai_agent/mcp-nlp-data-scientist/entity_discovery_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analysis complete!")
    print(f"✓ Results saved to: {output_file}")
    print()
    print("=" * 70)
    print("LLM Entity Discovery Results")
    print("=" * 70)
    
    print(f"\n📊 Analyzed {len(analysis.get('analyzed_documents', []))} documents")
    print(f"\n📋 Recommended {len(analysis.get('recommended_entity_types', []))} entity types:")
    
    for entity in analysis.get('recommended_entity_types', []):
        importance = entity.get('importance', 'medium')
        icon = "🔴" if importance == 'high' else "🟡" if importance == 'medium' else "🟢"
        print(f"  {icon} {entity.get('name', 'UNKNOWN')}: {entity.get('description', '')[:60]}...")
    
    print(f"\n🎯 Priority implementation ({len(analysis.get('priority_implementation', []))} types):")
    for i, entity_name in enumerate(analysis.get('priority_implementation', []), 1):
        print(f"  {i}. {entity_name}")
    
    if 'additional_observations' in analysis:
        print(f"\n💡 Additional observations:")
        print(f"  {analysis['additional_observations'][:200]}...")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    print(f"Raw response: {content[:500] if 'content' in dir() else 'N/A'}")
    sys.exit(1)

print("\n" + "=" * 70)
print("Next step: Review results and update custom_entity_types.py")
print("=" * 70)
