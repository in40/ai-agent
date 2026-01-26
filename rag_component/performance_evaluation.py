"""
Performance evaluation script for PDF to Markdown conversion in the RAG component.
This script compares the performance of the original PyPDFLoader approach with the new
PDF-to-Markdown conversion approach.
"""
import time
import os
import sys
from pathlib import Path
import tempfile

# Add the current directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from document_loader import DocumentLoader
from pdf_converter import PDFToMarkdownConverter
from config import (
    RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED,
    RAG_USE_FALLBACK_ON_CONVERSION_ERROR
)


def create_sample_pdf(file_path):
    """
    Create a sample PDF file for testing.
    This is a minimal valid PDF with some text content.
    """
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 55
>>
stream
BT
/F1 12 Tf
72 720 Td
(This is a sample PDF for testing purposes.) Tj
T* (It contains multiple lines of text to test) Tj
T* (the PDF to Markdown conversion functionality.) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000125 00000 n 
0000000207 00000 n 
0000000283 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
387
%%EOF"""
    
    with open(file_path, 'wb') as f:
        f.write(pdf_content)


def benchmark_pdf_loading(loader, pdf_path, num_iterations=5):
    """
    Benchmark the PDF loading performance.
    
    Args:
        loader: DocumentLoader instance
        pdf_path: Path to the PDF file to load
        num_iterations: Number of iterations to run
    
    Returns:
        Average time taken to load the PDF
    """
    total_time = 0
    
    for i in range(num_iterations):
        start_time = time.time()
        try:
            docs = loader.load_document(pdf_path)
            end_time = time.time()
            total_time += (end_time - start_time)
        except Exception as e:
            print(f"Error loading document in iteration {i+1}: {e}")
            continue
    
    return total_time / num_iterations if num_iterations > 0 else 0


def evaluate_performance():
    """
    Evaluate the performance of PDF loading with and without conversion.
    """
    print("Starting performance evaluation of PDF to Markdown conversion...")
    
    # Create a temporary PDF for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        create_sample_pdf(temp_pdf.name)
        pdf_path = temp_pdf.name
    
    try:
        print(f"Created test PDF: {pdf_path}")
        
        # Test with PDF conversion disabled (baseline)
        print("\n1. Testing with PDF conversion DISABLED (baseline)...")
        os.environ['RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED'] = 'false'
        
        # Reload the config module to pick up the new setting
        import importlib
        import config
        importlib.reload(config)
        
        baseline_loader = DocumentLoader()
        baseline_avg_time = benchmark_pdf_loading(baseline_loader, pdf_path)
        
        print(f"   Baseline average loading time: {baseline_avg_time:.4f} seconds")
        
        # Test with PDF conversion enabled
        print("\n2. Testing with PDF conversion ENABLED...")
        os.environ['RAG_PDF_TO_MARKDOWN_CONVERSION_ENABLED'] = 'true'
        
        # Reload the config module to pick up the new setting
        importlib.reload(config)
        
        conversion_loader = DocumentLoader()
        conversion_avg_time = benchmark_pdf_loading(conversion_loader, pdf_path)
        
        print(f"   Conversion average loading time: {conversion_avg_time:.4f} seconds")
        
        # Calculate performance difference
        time_diff = conversion_avg_time - baseline_avg_time
        time_ratio = conversion_avg_time / baseline_avg_time if baseline_avg_time > 0 else 0
        
        print(f"\n3. Performance Comparison:")
        print(f"   Time difference: {time_diff:.4f} seconds {'(slower)' if time_diff > 0 else '(faster)'}")
        print(f"   Time ratio: {time_ratio:.2f}x")
        
        if time_ratio < 1:
            print(f"   PDF conversion is {(1 - time_ratio)*100:.2f}% faster")
        elif time_ratio > 1:
            print(f"   PDF conversion is {(time_ratio - 1)*100:.2f}% slower")
        else:
            print("   No performance difference")
        
        # Test conversion quality and permanent storage
        print("\n4. Testing conversion quality and permanent storage...")
        try:
            converter = PDFToMarkdownConverter()
            markdown_content = converter.convert_pdf_to_markdown(pdf_path)

            if markdown_content:
                print(f"   Conversion successful - Markdown length: {len(markdown_content)} characters")
                print(f"   Sample content: {markdown_content[:100]}...")

                # Test permanent storage
                markdown_file_path = converter.convert_pdf_to_markdown_file(pdf_path)
                if markdown_file_path:
                    print(f"   Permanent Markdown file created: {markdown_file_path}")
                    print(f"   File exists: {os.path.exists(markdown_file_path)}")

                    # Verify the content was saved correctly
                    with open(markdown_file_path, 'r', encoding='utf-8') as f:
                        saved_content = f.read()
                        print(f"   Saved content matches: {saved_content == markdown_content}")
                else:
                    print("   Failed to create permanent Markdown file")
            else:
                print("   Conversion returned empty content")
        except ImportError:
            print("   Marker library not available - skipping quality test")
        
    finally:
        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)
    
    print("\nPerformance evaluation complete.")


if __name__ == "__main__":
    evaluate_performance()