#!/usr/bin/env python3
"""
REAL LaTeX to Natural Language Conversion Test
Uses actual LLM calls with proper configuration
"""
import re
import json
from openai import OpenAI

# Read EXACT config from .env
with open('/root/qwen/ai_agent/.env', 'r') as f:
    env_content = f.read()

model_match = re.search(r'^NLP_LLM_MODEL=(.+)$', env_content, re.MULTILINE)
url_match = re.search(r'^NLP_LLM_BASE_URL=(.+)$', env_content, re.MULTILINE)

llm_model = model_match.group(1).strip()
llm_base_url = url_match.group(1).strip()

print("=" * 100)
print("REAL LATEX TO NATURAL LANGUAGE CONVERSION TEST")
print("=" * 100)
print(f"\nLLM Configuration (from .env):")
print(f"  Model: {llm_model}")
print(f"  URL: {llm_base_url}\n")

# Test formulas from your actual .md files
TEST_FORMULAS = [
    r"S^C_{MAC} = KDF(K_{in}, label, seed)",
    r"ICV_i^C = E_{S_{MAC}^C}[C-MAC_{i-1} || '0x80']",
    r"C-MAC = MAC(S_{MAC}^C) [ICV^C || M]",
]

client = OpenAI(base_url=llm_base_url, api_key="not-needed")

results = []

for i, latex in enumerate(TEST_FORMULAS, 1):
    print(f"\n{'='*100}")
    print(f"FORMULA {i}/{len(TEST_FORMULAS)}")
    print(f"{'='*100}")
    print(f"\n📝 ORIGINAL LATEX:\n{latex}\n")
    
    prompt = f"Convert this LaTeX formula to plain English ONLY, no explanations, no reasoning:\n{latex}"
    
    print(f"🔄 Calling LLM (this may take 30-60 seconds for thinking)...")
    
    try:
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": "Convert LaTeX to plain English. Return ONLY the conversion."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=300  # 5 minutes for thinking
        )
        
        # Get content (Qwen returns both content and reasoning_content)
        message = response.choices[0].message
        conversion = message.content if message.content else message.reasoning_content
        
        print(f"\n✅ LLM CONVERSION:\n{conversion[:500]}{'...' if len(conversion) > 500 else ''}\n")
        
        results.append({
            'formula_id': i,
            'original_latex': latex,
            'llm_conversion': conversion,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        results.append({
            'formula_id': i,
            'original_latex': latex,
            'error': str(e),
            'status': 'failed'
        })

# Save results
output_file = "/root/qwen/ai_agent/latex_conversion_REAL_test_results.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n{'='*100}")
print(f"📁 Results saved to: {output_file}")
print(f"{'='*100}\n")

# Summary
successful = sum(1 for r in results if r['status'] == 'success')
print(f"📊 SUMMARY: {successful}/{len(TEST_FORMULAS)} formulas converted successfully")
