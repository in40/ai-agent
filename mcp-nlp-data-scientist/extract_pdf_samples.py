#!/usr/bin/env python3
"""Extract text samples from PDFs for LLM entity analysis"""
import pdfplumber
import json

# Analyze 2-3 different PDFs
pdf_files = [
    "/root/qwen/ai_agent/downloads/gost-r-50922-2006.pdf",
    "/root/qwen/ai_agent/downloads/gost-r-34_1.pdf",
    "/root/qwen/ai_agent/downloads/r-1323565.1_18.pdf"
]

print("=" * 70)
print("PDF Document Analysis for Entity Discovery")
print("=" * 70)

all_text = []

for pdf_path in pdf_files:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:3]:  # First 3 pages
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            all_text.append({
                "file": pdf_path.split("/")[-1],
                "text": text[:3000],  # First 3000 chars
                "pages": len(pdf.pages)
            })
            
            print(f"\n📄 {pdf_path.split('/')[-1]}")
            print(f"   Pages: {len(pdf.pages)}")
            print(f"   Text extracted: {len(text)} chars")
            print(f"   First 200 chars: {text[:200]}...")
    except Exception as e:
        print(f"\n✗ Error reading {pdf_path}: {e}")

# Save for LLM analysis with proper UTF-8 encoding
with open("/root/qwen/ai_agent/mcp-nlp-data-scientist/pdf_samples.json", "w", encoding="utf-8") as f:
    json.dump(all_text, f, indent=2, ensure_ascii=False)

print(f"\n✓ Saved {len(all_text)} document samples to pdf_samples.json")
