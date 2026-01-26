# Memory Usage Analysis: PDF Conversion with Marker Library

## High Memory Usage Explained

The 16GB RAM usage during PDF conversion is caused by the marker library's architecture and processing methodology. Here's a breakdown of what's consuming memory:

## 1. Machine Learning Model Loading

The `create_model_dict()` function in the marker library loads several machine learning models into memory:

- **Layout detection models**: For identifying document structure (text, tables, images, etc.)
- **OCR models**: For extracting text from scanned documents or complex layouts
- **Table recognition models**: For properly parsing tabular data
- **Image segmentation models**: For handling embedded images in PDFs

These models can collectively consume several gigabytes of RAM when loaded.

## 2. Document Processing Architecture

During PDF conversion, the marker library:

- Loads the entire PDF document into memory for analysis
- Creates internal representations of each page
- Processes images and graphics separately
- Maintains multiple buffers for intermediate processing steps
- Generates layout trees for each page

## 3. Known Memory Issues with Marker Library

According to GitHub issues and documentation:

- Marker can use up to 5GB of VRAM per worker at peak usage
- Average usage is around 3.5GB
- For large PDFs with many pages, memory usage scales significantly
- Processing involves rendering images for every page, which increases memory consumption
- Memory usage increases substantially during conversion of long PDFs

## 4. Specific Memory-Intensive Operations

In the `_perform_conversion` method:

1. `create_model_dict()` - Loads ML models into memory
2. `PdfConverter` instantiation - Creates processing pipeline
3. `converter(pdf_path)` - Processes the entire document in memory
4. All intermediate representations are held in memory during processing

## 5. Mitigation Strategies

To address the high memory usage:

1. **Batch Processing**: Process PDFs one at a time rather than in parallel
2. **Memory Monitoring**: Monitor memory usage during processing
3. **Timeout Management**: Use appropriate timeouts to prevent runaway processes
4. **Resource Limits**: Consider running on systems with sufficient RAM
5. **Alternative Libraries**: For simple text extraction, PyPDFLoader uses significantly less memory

## 6. Expected Behavior

The 16GB RAM usage is within expected parameters for the marker library when processing complex PDFs with:
- Multiple pages
- Embedded images
- Complex layouts
- Tables and figures

This is the trade-off for the high-quality markdown conversion that marker provides compared to simpler extraction methods like PyPDFLoader.