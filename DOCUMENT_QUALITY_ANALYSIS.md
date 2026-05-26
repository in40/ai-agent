# Document Quality Analysis Report

**Date**: March 29, 2026  
**Scope**: All .md files in document store  
**Total Files**: 115

---

## Executive Summary

**68.7% of documents have significant PDF extraction garbage** that will prevent proper smart chunking.

| Quality | Count | Percentage | Status |
|---------|-------|------------|--------|
| GOOD (< 30% garbage) | 38 | 33.0% | ✅ Ready for chunking |
| ACCEPTABLE (30-50%) | 41 | 35.7% | ⚠️ May work |
| POOR (50-70%) | 28 | 24.3% | ❌ Needs re-extraction |
| GARBAGE (> 70%) | 8 | 7.0% | ❌ Useless |

---

## Root Cause

The PDF extraction process is generating **garbage output** for table of contents and other formatted sections:

**Example of garbage pattern:**
```
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 
```

This is the **table of contents** where the PDF extractor couldn't properly extract text, so it output dots/lines instead.

**Impact on Smart Chunking:**
- LLMs cannot process garbage content
- LLMs stop processing after hitting garbage sections
- Coverage drops to 15-30% instead of 100%

---

## Documents Ready for Smart Chunking (GOOD Quality)

These 38 documents have < 30% garbage and should work well:

| Document | Garbage % | Size | Pages |
|----------|-----------|------|-------|
| gost-r-71753-2024_e6ab5a68.md | 29.6% | 137K | 40 |
| gost-r-53113_9f37aa3e.md | 29.3% | 45K | 12 |
| r-1323565.1_6667160c.md | 28.5% | 96K | 40 |
| r-1323565.1_881b0329.md | 27.7% | 46K | 20 |
| gost-r-56938-2016=edt2018_86a0c3ab.md | 27.6% | 81K | 32 |
| gost-r-56545-2015=edt2018_0efaf655.md | 27.2% | 24K | 12 |
| r-1323565.1_12ff4b7a.md | 26.1% | 77K | 28 |
| r-1323565.1_0cdebced.md | 26.0% | 98K | 32 |
| r-1323565.1_1c653cc5.md | 25.9% | 76K | 32 |
| r-1323565.1_58194614.md | 25.8% | 19K | 12 |
| r-1323565.1_99b55685.md | 25.3% | 211K | 74 |
| r-1323565.1_8a84396d.md | 24.7% | 58K | 24 |
| r-1323565.1_8e67ba17.md | 23.5% | 223K | 74 |
| r-1323565.1_a670037e.md | 23.1% | 102K | 46 |
| gost-r-iso-iec-27002-2021_a33a8fa4.md | 23.1% | 296K | 74 |
| ... and 23 more |

**Full list**: See `garbage_document_analysis.json`

---

## Documents That Need Re-extraction (POOR + GARBAGE)

These 36 documents have > 50% garbage and will fail smart chunking:

### GARBAGE (> 70% garbage) - 8 documents

| Document | Garbage % | Issue |
|----------|-----------|-------|
| gost-r-52633_93230662.md | 98.5% | Almost entirely dots |
| gost-r-59453_be4409ed.md | 89.8% | Repeated characters |
| r-1323565.1_ab155d71.md | 82.2% | Table of contents garbage |
| r-1323565.1_1e73f3e7.md | 81.9% | Extraction failure |
| r-1323565.1_395de1a8.md | 80.9% | **This was the failing test document** |
| r-50.1_9cdb3670.md | 75.8% | Dots everywhere |
| gost-r-58412-2019_91a63deb.md | 75.7% | Repeated chars |
| gost-r-54582-2011=edt2019_c6add81e.md | 75.5% | 344K of mostly garbage |

### POOR (50-70% garbage) - 28 documents

| Document | Garbage % |
|----------|-----------|
| gost-r-70262_4fe87085.md | 68.7% |
| gost-r-59710-2022_11db7995.md | 67.3% |
| gost-r-52633_8de4b632.md | 66.9% |
| gost-r-59162-2020_115cf792.md | 66.7% |
| ... and 24 more |

---

## Recommendations

### Immediate Actions

1. **Use GOOD documents for smart chunking tests**
   - 38 documents are ready to use
   - These have proper text extraction

2. **Fix PDF extraction process**
   - The current extraction is broken for table of contents
   - Need better PDF parsing that handles dotted leaders

3. **Re-extract POOR and GARBAGE documents**
   - 36 documents need to be re-processed
   - Consider using different PDF extraction tool

### Long-term Solutions

1. **Add quality check to ingestion pipeline**
   - Scan for garbage patterns during extraction
   - Flag documents that need manual review

2. **Improve PDF extraction**
   - Use better PDF parsing library
   - Handle table of contents specially
   - Preserve formatting better

3. **Add garbage detection to smart chunking**
   - Warn users if document has > 30% garbage
   - Skip obviously corrupted documents

---

## Technical Details

### Garbage Patterns Detected

1. **Repeated character lines** (most common)
   - Lines with < 15% unique characters
   - Typically dots, spaces, or underscores

2. **Dot sequences**
   - 10+ consecutive dots (table of contents leaders)
   - Often hundreds per document

3. **Space-heavy lines**
   - Lines that are 80%+ spaces
   - Formatting artifacts

### Detection Algorithm

```python
# A line is "garbage" if:
unique_chars / total_chars < 0.15  # Less than 15% unique

# Document garbage ratio:
garbage_chars / total_chars

# Quality thresholds:
GOOD:       < 30% garbage
ACCEPTABLE: 30-50% garbage
POOR:       50-70% garbage
GARBAGE:    > 70% garbage
```

---

## Files Generated

- `/root/qwen/ai_agent/garbage_document_analysis.json` - Full analysis data
- `/root/qwen/ai_agent/DOCUMENT_QUALITY_ANALYSIS.md` - This report

---

**Conclusion**: The smart chunking failures were NOT caused by LLM limitations or prompt issues. The root cause is **corrupted PDF extraction output**. Fix the extraction process, and smart chunking will work properly.
