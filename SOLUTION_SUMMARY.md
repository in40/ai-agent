# MCP Service Result Source Information Preservation - Complete Solution

## Problem Identified
The system was showing "(Unknown source)" in the final output instead of proper source information like "GOST_R_52633.3-2011" or specific domain names from search results. This occurred because:

1. Search results from the MCP search service had nested structures that weren't being properly parsed to extract source information
2. The normalization function was defaulting to generic service IDs instead of extracting meaningful source information from the actual search results
3. RAG documents had source information in metadata but it wasn't being properly mapped to the unified format

## Root Cause Analysis
The issue was in the `utils/result_normalizer.py` file in the `_normalize_search_result` function. The function was:
- Setting a generic "Web Search" or service ID as the source
- Not properly navigating the nested structure of search results to extract individual document sources
- Not extracting domain information from URLs in search results
- Not considering multiple sources when there were multiple search results

## Solution Implemented

### 1. Enhanced Search Result Normalization (`utils/result_normalizer.py`)
Updated the `_normalize_search_result` function to:
- Properly navigate nested structures: `result.result.results`
- Extract source information from individual search result URLs
- Extract domain names from URLs using `urllib.parse`
- Handle multiple search results by showing source diversity
- Prioritize meaningful source information over generic service IDs

### 2. Improved Source Extraction Logic
The updated function now:
- Checks for nested result structures from search services
- Extracts domains from multiple search result URLs
- Creates descriptive source labels like "Search (2 results from 2 sources: docs.cntd.ru, cyberleninka.ru)"
- Falls back to service information only if no meaningful sources can be extracted

### 3. Preserved RAG Document Source Information
Ensured that RAG documents continue to properly extract source information from metadata fields like "source", "filename", "title", etc.

## Key Changes Made

### Before (Problematic Format):
```
Document 1 (Unknown source):
Content from search result...

Document 2 (Unknown source): 
Content from RAG document...
```

### After (Fixed Format):
```
Document 1 (Search (2 results from 2 sources: docs.cntd.ru, cyberleninka.ru)):
Content from search results...

Document 2 (GOST_R_52633.3-2011):
Content from RAG document...
```

## Verification Results
✅ Search results now show proper domain information instead of "Unknown source"  
✅ RAG documents continue to show proper source names from metadata  
✅ Multiple search results show source diversity information  
✅ Final output contains meaningful source labels for all document types  
✅ Both search and RAG results are properly differentiated in the output  

## Files Modified
- `/root/qwen/ai_agent/utils/result_normalizer.py` - Enhanced search result normalization with proper source extraction

The fix ensures that when users receive results from both search and RAG services, they will see proper source information (like document names, domain names, etc.) instead of generic "Unknown source" labels, making the information much more useful and traceable.