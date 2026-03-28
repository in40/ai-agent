#!/usr/bin/env python3
"""
Test smart chunking with new prompt and LaTeX formulas
Text: Random text with LaTeX formulas
"""
import sys
import os
sys.path.insert(0, '/root/qwen/ai_agent')

from backend.services.rag.smart_ingestion_enhanced import chunk_document_with_llm_sync
import tempfile

# Create temp file with test text containing LaTeX formulas
test_text = """
Section 1: Introduction

The water tank system uses the following formula to calculate pressure:

$$P = \\rho g h$$

where:
- P is pressure in Pascals
- ρ (rho) is water density (1000 kg/m³)
- g is gravitational acceleration (9.81 m/s²)
- h is water height in meters

Section 2: Flow Rate

The flow rate Q is calculated as:

$$Q = A \\cdot v = \\pi r^2 v$$

For a tank with radius r = 0.5m and velocity v = 2 m/s:

$$Q = \\pi (0.5)^2 \\cdot 2 = 1.57 \\text{ m}^3/\\text{s}$$

Section 3: Temperature Effects

The temperature correction factor is:

$$\\alpha = \\frac{T - T_0}{T_0}$$

where T₀ = 20°C is the reference temperature.

The final corrected pressure is:

$$P_{corrected} = P \\cdot (1 + \\alpha)$$
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
    f.write(test_text)
    temp_file = f.name

try:
    print("=" * 80)
    print("TESTING SMART CHUNKING - PHASE 3 ONLY (NLP LLM)")
    print("=" * 80)
    print(f"\nInput text: {len(test_text)} chars with LaTeX formulas")
    print(f"\nLLM Config (from .env):")
    print(f"  NLP_LLM_BASE_URL={os.getenv('NLP_LLM_BASE_URL')}")
    print(f"  NLP_LLM_MODEL={os.getenv('NLP_LLM_MODEL')}")
    print("\nCalling chunk_document_with_llm_sync()...")
    print("(This may take 30-90 seconds for LLM to respond)\n")
    
    # Call chunking function - EXACT same call as web UI uses
    success, chunks, error, cleaning_method = chunk_document_with_llm_sync(
        file_path=temp_file,
        prompt="",  # Use DEFAULT_SMART_CHUNKING_PROMPT
        filename="test_latex.txt",
        timeout=900  # 15 minutes (from LLM_CHUNKING_TIMEOUT in .env)
    )
    
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"\nSuccess: {success}")
    print(f"Cleaning method: {cleaning_method}")
    
    if success:
        print(f"\n✅ Chunks generated: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            print(f"\n{'='*60}")
            print(f"CHUNK {i}")
            print(f"{'='*60}")
            for key, value in chunk.items():
                if key == 'content':
                    # Show first 200 chars of content
                    content_preview = value[:200] + "..." if len(value) > 200 else value
                    print(f"  {key}: \"{content_preview}\"")
                else:
                    print(f"  {key}: {value}")
    else:
        print(f"\n❌ Error: {error}")
        
finally:
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)
        print(f"\n✅ Temp file cleaned up")
