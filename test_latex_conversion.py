#!/usr/bin/env python3
"""
Test LaTeX to Natural Language Conversion
Extracts real formulas from .md files and tests conversion with LLM
"""
import os
import re
import json
from openai import OpenAI

# Sample LaTeX formulas extracted from your .md files
LATEX_SAMPLES = [
    # KDF formulas
    r"$$S^C_{MAC} = KDF(K_{in}, label, seed) = HMAC_{256}(K_{in}, 0x01 || label || 0x00 || seed || 0x01 || 0x00),$$",
    
    # ICV formulas
    r"$$ICV_i^C = E_{S_{MAC}^C}[C-MAC_{i-1} || '0x80' || '0x00' || '0x00' || '0x00'], i=1, \dots;$$",
    
    # MAC formulas
    r"$$C-MAC = MAC(S_{MAC}^C) [ICV^C || M];$$",
    
    # R-MAC formulas
    r"$$ICV_1^R = (\text{C-MAC}_0 || \text{'0x00'} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'});$$",
    
    r"$$ICV_i^R = (\text{R-MAC}_{i-1} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'}), i = 2, \dots;$$",
    
    # APDU formula
    r"$$M = (\text{CLA}' || \text{INS} || \text{P1} || \text{P2} || \text{Lc (без учета шифрования и C-MAC)} || \text{Data (без шифрования и C-MAC)} || \text{Li} || \text{R-Data (данные ответа)} || \text{SW});$$",
    
    # R-MAC computation
    r"$$\text{R-MAC} = \text{MAC}(S_{MAC}^R) [ICV^R || M];$$",
    
    # Full APDU
    r"$$\text{APDU} = \text{CLA}' || \text{INS} || \text{P1} || \text{P2} || \text{Lc} || \text{Data} || \text{Li} || \text{R-Data} || \text{R-MAC} || \text{SW}.$$"
]

def convert_latex_to_natural_language(latex_text):
    """Send LaTeX to LLM for conversion to natural language"""
    
    prompt = f"""You are a LaTeX to natural language converter. Your task is to convert mathematical formulas with LaTeX notation into clear, readable natural language while preserving the exact mathematical meaning.

CONVERSION RULES:
1. Convert subscripts: "X_i" → "X sub i", "S^C_{{MAC}}" → "S sub MAC superscript C"
2. Convert Greek letters: "\\alpha" → "alpha", "\\delta" → "delta"
3. Convert operators: "\\dots" → "and so on", "\\text{{...}}" → just the text inside
4. Convert math notation: "||" → "concatenated with", "=" → "equals"
5. Keep hex values intact: '0x01' stays as '0x01'
6. Keep variable names intact: KDF, HMAC, MAC, ICV, C-MAC, R-MAC
7. Convert subscripts/superscripts descriptively

EXAMPLES:
- "S^C_{{MAC}}" → "S sub MAC superscript C"
- "KDF(K_{{in}}, label, seed)" → "KDF of K sub in, label, and seed"
- "HMAC_{{256}}" → "HMAC sub 256"
- "i=1, \\dots" → "i equals 1 and so on"
- "\\text{{C-MAC}}_0" → "C-MAC sub 0"
- "E_{{S_{{MAC}}^C}}" → "E sub S sub MAC superscript C"

Convert the following LaTeX formula to natural language. Return ONLY the converted text, no explanations:

{latex_text}
"""
    
    try:
        # Use LM Studio local LLM
        client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
        
        response = client.chat.completions.create(
            model="qwen3.5-35b",  # Or your configured model
            messages=[
                {"role": "system", "content": "You are a LaTeX to natural language converter. Return ONLY the converted natural language text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=60
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"ERROR: {str(e)}"


def main():
    print("=" * 80)
    print("LATEX TO NATURAL LANGUAGE CONVERSION TEST")
    print("=" * 80)
    print(f"\nTesting {len(LATEX_SAMPLES)} formulas from your .md files...\n")
    
    results = []
    
    for i, latex in enumerate(LATEX_SAMPLES, 1):
        print(f"\n{'='*80}")
        print(f"FORMULA {i}/{len(LATEX_SAMPLES)}")
        print(f"{'='*80}")
        print(f"\n📝 ORIGINAL LATEX:\n{latex}\n")
        
        # Convert
        natural_lang = convert_latex_to_natural_language(latex)
        
        print(f"\n✅ CONVERTED TO NATURAL LANGUAGE:\n{natural_lang}\n")
        
        results.append({
            'original': latex,
            'converted': natural_lang
        })
    
    # Save results
    output_file = "/root/qwen/ai_agent/latex_conversion_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print(f"✅ Results saved to: {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
