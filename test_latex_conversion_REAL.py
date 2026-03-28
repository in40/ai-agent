#!/usr/bin/env python3
"""
Real LaTeX to Natural Language Conversion Test
Uses the RAG service's LLM connection for actual conversion
"""
import os
import sys
import json
import requests

# Add backend to path
sys.path.insert(0, '/root/qwen/ai_agent')

# Sample LaTeX formulas from your .md files
LATEX_SAMPLES = [
    r"$$S^C_{MAC} = KDF(K_{in}, label, seed) = HMAC_{256}(K_{in}, 0x01 || label || 0x00 || seed || 0x01 || 0x00),$$",
    r"$$ICV_i^C = E_{S_{MAC}^C}[C-MAC_{i-1} || '0x80' || '0x00' || '0x00' || '0x00'], i=1, \dots;$$",
    r"$$C-MAC = MAC(S_{MAC}^C) [ICV^C || M];$$",
    r"$$ICV_1^R = (\text{C-MAC}_0 || \text{'0x00'} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'});$$",
]

def convert_with_rag_llm(latex_text):
    """Use the RAG service's LLM for conversion - reads EXACT config from .env"""
    
    from openai import OpenAI
    
    # Read EXACT values from .env file - DO NOT HARDCODE
    # These MUST match what's in /root/qwen/ai_agent/.env
    with open('/root/qwen/ai_agent/.env', 'r') as f:
        env_content = f.read()
    
    # Parse NLP_LLM_MODEL and NLP_LLM_BASE_URL from .env
    import re
    model_match = re.search(r'^NLP_LLM_MODEL=(.+)$', env_content, re.MULTILINE)
    url_match = re.search(r'^NLP_LLM_BASE_URL=(.+)$', env_content, re.MULTILINE)
    
    if not model_match or not url_match:
        return "ERROR: Could not read NLP_LLM config from .env"
    
    llm_model = model_match.group(1).strip()
    llm_base_url = url_match.group(1).strip()
    
    print(f"  → Reading from .env:")
    print(f"     NLP_LLM_BASE_URL={llm_base_url}")
    print(f"     NLP_LLM_MODEL={llm_model}")
    
    prompt = f"""Convert this LaTeX formula to natural language. Return ONLY the conversion, no explanations:

{latex_text}

Rules:
- Subscripts: X_i → "X sub i"
- Superscripts: X^2 → "X squared"  
- Greek: \\alpha → "alpha"
- Operators: || → "concatenated with"
- Keep hex values: 0x01 stays as is
- Keep acronyms: KDF, MAC, ICV stay uppercase
"""
    
    try:
        client = OpenAI(base_url=llm_base_url, api_key="not-needed")
        
        response = client.chat.completions.create(
            model=llm_model,  # Use EXACT model from .env
            messages=[
                {"role": "system", "content": "Convert LaTeX to natural language. Return ONLY the conversion."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=120
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    print("=" * 100)
    print("REAL LATEX TO NATURAL LANGUAGE CONVERSION TEST")
    print("=" * 100)
    print(f"\nTesting {len(LATEX_SAMPLES)} formulas with REAL LLM calls\n")
    
    results = []
    
    for i, latex in enumerate(LATEX_SAMPLES, 1):
        print(f"\n{'='*100}")
        print(f"FORMULA {i}/{len(LATEX_SAMPLES)}")
        print(f"{'='*100}")
        print(f"\n📝 ORIGINAL LATEX:\n{latex}\n")
        
        print("🔄 Calling LLM for conversion...")
        natural_lang = convert_with_rag_llm(latex)
        
        print(f"\n✅ REAL LLM CONVERSION:\n{natural_lang}\n")
        
        results.append({
            'formula_id': i,
            'original_latex': latex,
            'real_conversion': natural_lang,
            'status': 'real_result' if not natural_lang.startswith('ERROR') else 'failed'
        })
    
    # Save results
    output_file = "/root/qwen/ai_agent/latex_conversion_REAL_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*100}")
    print(f"📁 REAL results saved to: {output_file}")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    main()
