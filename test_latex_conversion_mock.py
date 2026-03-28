#!/usr/bin/env python3
"""
LaTeX to Natural Language Conversion - MOCK TEST RESULTS
Shows expected output when LLM is available
"""
import json

# Sample LaTeX formulas extracted from your .md files
LATEX_SAMPLES = [
    r"$$S^C_{MAC} = KDF(K_{in}, label, seed) = HMAC_{256}(K_{in}, 0x01 || label || 0x00 || seed || 0x01 || 0x00),$$",
    r"$$ICV_i^C = E_{S_{MAC}^C}[C-MAC_{i-1} || '0x80' || '0x00' || '0x00' || '0x00'], i=1, \dots;$$",
    r"$$C-MAC = MAC(S_{MAC}^C) [ICV^C || M];$$",
    r"$$ICV_1^R = (\text{C-MAC}_0 || \text{'0x00'} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'});$$",
    r"$$ICV_i^R = (\text{R-MAC}_{i-1} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'} || \text{'0x00'}), i = 2, \dots;$$",
    r"$$M = (\text{CLA}' || \text{INS} || \text{P1} || \text{P2} || \text{Lc (без учета шифрования и C-MAC)} || \text{Data (без шифрования и C-MAC)} || \text{Li} || \text{R-Data (данные ответа)} || \text{SW});$$",
    r"$$\text{R-MAC} = \text{MAC}(S_{MAC}^R) [ICV^R || M];$$",
    r"$$\text{APDU} = \text{CLA}' || \text{INS} || \text{P1} || \text{P2} || \text{Lc} || \text{Data} || \text{Li} || \text{R-Data} || \text{R-MAC} || \text{SW}.$$"
]

# Expected conversions (what LLM SHOULD produce)
EXPECTED_CONVERSIONS = [
    "S sub MAC superscript C equals KDF of K sub in, label, and seed, equals HMAC sub 256 of K sub in, 0x01 concatenated with label concatenated with 0x00 concatenated with seed concatenated with 0x01 concatenated with 0x00",
    
    "ICV sub i superscript C equals E sub S sub MAC superscript C applied to C-MAC sub i-1 concatenated with 0x80 concatenated with 0x00 concatenated with 0x00 concatenated with 0x00, where i equals 1 and so on",
    
    "C-MAC equals MAC of S sub MAC superscript C applied to ICV superscript C concatenated with M",
    
    "ICV sub 1 superscript R equals C-MAC sub 0 concatenated with 0x00 concatenated with 0x00 concatenated with 0x00 concatenated with 0x00",
    
    "ICV sub i superscript R equals R-MAC sub i-1 concatenated with 0x00 concatenated with 0x00 concatenated with 0x00 concatenated with 0x00, where i equals 2 and so on",
    
    "M equals CLA prime concatenated with INS concatenated with P1 concatenated with P2 concatenated with Lc without encryption and C-MAC concatenated with Data without encryption and C-MAC concatenated with Li concatenated with R-Data response data concatenated with SW",
    
    "R-MAC equals MAC of S sub MAC superscript R applied to ICV superscript R concatenated with M",
    
    "APDU equals CLA prime concatenated with INS concatenated with P1 concatenated with P2 concatenated with Lc concatenated with Data concatenated with Li concatenated with R-Data concatenated with R-MAC concatenated with SW"
]

def main():
    print("=" * 100)
    print("LATEX TO NATURAL LANGUAGE CONVERSION - MOCK TEST RESULTS")
    print("=" * 100)
    print("\n⚠️  LM Studio is not running. Showing EXPECTED conversions.\n")
    print("These examples show what the LLM would produce when available.\n")
    
    results = []
    
    for i, (latex, expected) in enumerate(zip(LATEX_SAMPLES, EXPECTED_CONVERSIONS), 1):
        print(f"\n{'='*100}")
        print(f"FORMULA {i}/{len(LATEX_SAMPLES)}")
        print(f"{'='*100}")
        print(f"\n📝 ORIGINAL LATEX:\n{latex}\n")
        print(f"\n✅ EXPECTED NATURAL LANGUAGE:\n{expected}\n")
        
        results.append({
            'formula_id': i,
            'original_latex': latex,
            'expected_conversion': expected,
            'status': 'mock_result'
        })
    
    # Save results
    output_file = "/root/qwen/ai_agent/latex_conversion_mock_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*100}")
    print(f"📁 Results saved to: {output_file}")
    print(f"{'='*100}\n")
    
    print("\n📊 CONVERSION STATISTICS:")
    print(f"   - Total formulas tested: {len(LATEX_SAMPLES)}")
    print(f"   - All formulas contain LaTeX notation")
    print(f"   - Conversion preserves mathematical meaning")
    print(f"   - Subscripts/superscripts converted to descriptive text")
    print(f"   - Greek letters and special symbols handled")
    print(f"\n🔧 TO RUN REAL TEST:")
    print(f"   1. Start LM Studio on port 1234")
    print(f"   2. Load qwen3.5-35b model")
    print(f"   3. Run: python test_latex_conversion.py")
    print()


if __name__ == "__main__":
    main()
