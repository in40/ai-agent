#!/usr/bin/env python3
"""
Extract text from PDFs with proper Cyrillic encoding using PyMuPDF
"""
import json
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path, pages_to_extract=3):
    """Extract text from PDF with PyMuPDF (better Cyrillic support)"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(min(pages_to_extract, len(doc))):
            page = doc[page_num]
            # Use dict option for better text extraction
            page_text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            if page_text:
                text += page_text + "\n"
        
        doc.close()
        return text.strip()
        
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
print("PDF Text Extraction with PyMuPDF (Cyrillic Support)")
print("=" * 70)

all_text = []

for pdf_path in pdf_files:
    print(f"\n📄 Processing: {pdf_path.split('/')[-1]}")
    
    text = extract_text_from_pdf(pdf_path, pages_to_extract=3)
    
    if text:
        # Count actual pages
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        
        all_text.append({
            "file": pdf_path.split("/")[-1],
            "text": text[:3000],  # First 3000 chars
            "pages": page_count,
            "extracted_chars": len(text)
        })
        
        print(f"   ✓ Pages: {page_count}")
        print(f"   ✓ Extracted: {len(text)} chars")
        print(f"   ✓ First 200 chars: {text[:200]}...")
    else:
        print(f"   ✗ Failed to extract text")

# Save with proper UTF-8 encoding
with open("/root/qwen/ai_agent/mcp-nlp-data-scientist/pdf_samples_pymupdf.json", "w", encoding="utf-8") as f:
    json.dump(all_text, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"✓ Saved {len(all_text)} document samples to pdf_samples_pymupdf.json")
print(f"{'='*70}")

# Show sample
if all_text:
    print(f"\n📋 Sample from first document:")
    print(f"   {all_text[0]['text'][:400]}...")
