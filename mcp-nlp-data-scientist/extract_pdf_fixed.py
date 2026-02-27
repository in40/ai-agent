#!/usr/bin/env python3
"""
Extract text from PDFs with proper Cyrillic encoding
Uses pdfminer.six for better encoding handling
"""
import json
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams

def extract_text_from_pdf(pdf_path, pages_to_extract=3):
    """Extract text from PDF with proper encoding"""
    try:
        # Use pdfminer with proper encoding settings
        laparams = LAParams(
            detect_vertical=True,
            all_texts=True,
            line_margin=0.5
        )
        
        full_text = extract_text(
            pdf_path, 
            laparams=laparams,
            maxpages=pages_to_extract
        )
        
        # Clean up text - remove extra spaces between Cyrillic characters
        import re
        # Remove spaces between single Cyrillic characters that form words
        cleaned = re.sub(r'([А-Яа-яЁё])\s+([А-Яа-яЁё])', r'\1\2', full_text)
        # Normalize multiple spaces
        cleaned = re.sub(r'\s{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
        
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
        return None

# PDF files to analyze
pdf_files = [
    "/root/qwen/ai_agent/downloads/gost-r-50922-2006.pdf",
    "/root/qwen/ai_agent/downloads/gost-r-34_1.pdf",
    "/root/qwen/ai_agent/downloads/r-1323565.1_18.pdf"
]

print("=" * 70)
print("PDF Text Extraction with Proper Encoding")
print("=" * 70)

all_text = []

for pdf_path in pdf_files:
    print(f"\n📄 Processing: {pdf_path.split('/')[-1]}")
    
    text = extract_text_from_pdf(pdf_path, pages_to_extract=3)
    
    if text:
        # Count actual pages using pdfplumber (already installed)
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
        
        all_text.append({
            "file": pdf_path.split("/")[-1],
            "text": text[:3000],  # First 3000 chars
            "pages": page_count,
            "extracted_chars": len(text)
        })
        
        print(f"   ✓ Pages: {page_count}")
        print(f"   ✓ Extracted: {len(text)} chars")
        print(f"   ✓ First 150 chars: {text[:150]}...")
    else:
        print(f"   ✗ Failed to extract text")

# Save with proper UTF-8 encoding
with open("/root/qwen/ai_agent/mcp-nlp-data-scientist/pdf_samples_fixed.json", "w", encoding="utf-8") as f:
    json.dump(all_text, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"✓ Saved {len(all_text)} document samples to pdf_samples_fixed.json")
print(f"{'='*70}")

# Show sample
if all_text:
    print(f"\n📋 Sample from first document:")
    print(f"   {all_text[0]['text'][:300]}...")
