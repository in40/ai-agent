#!/usr/bin/env python3
"""Analyze largest PDF for token count vs Qwen3 context window"""
import pdfplumber

# Check the largest PDF
largest_pdf = "/root/qwen/ai_agent/preprod_backup_20260227_124257/downloads/gost_25347-82.pdf"

print(f"Analyzing: {largest_pdf}")
print("=" * 60)

with pdfplumber.open(largest_pdf) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    
    # Extract all text
    full_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    # Count characters and estimate tokens
    char_count = len(full_text)
    
    # Token estimation (rough): 1 token ≈ 4 characters for English/Russian
    estimated_tokens = char_count // 4
    
    # Also count words
    word_count = len(full_text.split())
    
    print(f"\nText Statistics:")
    print(f"  Characters: {char_count:,}")
    print(f"  Words: {word_count:,}")
    print(f"  Estimated tokens: ~{estimated_tokens:,}")
    print(f"\nQwen3 Context Window: 32,000 tokens")
    print(f"\nFits in 32k context: {'✅ YES' if estimated_tokens < 32000 else '❌ NO'}")
    
    if estimated_tokens > 32000:
        print(f"\n⚠️  EXCEEDS by: ~{estimated_tokens - 32000:,} tokens")
        print(f"   Need to split into {estimated_tokens // 32000 + 1} chunks")
    
    # Show page-by-page breakdown
    print(f"\nPage-by-page breakdown:")
    for i, page in enumerate(pdf.pages[:10]):  # First 10 pages
        text = page.extract_text() or ""
        page_tokens = len(text) // 4
        print(f"  Page {i+1}: ~{page_tokens:,} tokens")
    
    if len(pdf.pages) > 10:
        print(f"  ... and {len(pdf.pages) - 10} more pages")

# Also check a few more large PDFs
print("\n" + "=" * 60)
print("Other Large PDFs Analysis:")
print("=" * 60)

large_pdfs = [
    "/root/qwen/ai_agent/preprod_backup_20260227_124257/downloads/r-1323565.1_51.pdf",
    "/root/qwen/ai_agent/preprod_backup_20260227_124257/downloads/r-1323565.1_17.pdf",
    "/root/qwen/ai_agent/preprod_backup_20260227_124257/downloads/r-1323565.1_36.pdf",
]

for pdf_path in large_pdfs:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            tokens = len(full_text) // 4
            fits = "✅" if tokens < 32000 else "❌"
            print(f"\n{pdf_path.split('/')[-1]}:")
            print(f"  Pages: {len(pdf.pages)}, Tokens: ~{tokens:,} {fits}")
    except Exception as e:
        print(f"\n{pdf_path.split('/')[-1]}: Error - {e}")
