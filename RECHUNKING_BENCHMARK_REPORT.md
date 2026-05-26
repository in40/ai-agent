# Chunking Strategy Benchmark Report

## Research Background

Based on 2026 benchmarks (FloTorch, Vectara NAACL, NVIDIA):
- **Recursive character splitting at 512 tokens** outperformed LLM/semantic chunking
- FloTorch 2026: Recursive 69% accuracy vs Semantic (LLM) 54%
- Key issue with semantic/LLM chunking: produces tiny fragments (avg 43 tokens) that lack context
- **Recommended**: 512 tokens (~2000 chars) with 10% overlap, min 500 chars, max 8000 chars

## Documents Selected for Testing

| Document | Size | Original Chunks | Issue |
|----------|------|-----------------|-------|
| gost-r-52069_2c53c42c | 296K chars | 49 | Had 149K char chunk (diluted embedding) |
| r-1323565.1_78b35e61 | 283K chars | 145 | Had 34K char chunks |

## Chunking Results

### gost-r-52069_2c53c42c
| Metric | Before (LLM) | After (Recursive) | Improvement |
|--------|--------------|-------------------|-------------|
| Total chunks | 49 | 151 | +208% |
| Min chunk size | 66 chars | 1,051 chars | +1,492% |
| Max chunk size | 149,254 chars | 2,249 chars | -98.5% |
| Avg chunk size | 6,982 chars | 2,163 chars | Better distribution |
| Chunks >8K | 3 | 0 | ✅ Fixed |

### r-1323565.1_78b35e61
| Metric | Before (LLM) | After (Recursive) | Improvement |
|--------|--------------|-------------------|-------------|
| Total chunks | 145 | 140 | -3% |
| Min chunk size | 52 chars | 278 chars | +435% |
| Max chunk size | 34,250 chars | 8,000 chars | -76.6% |
| Avg chunk size | 1,728 chars | 2,200 chars | Better distribution |
| Chunks >8K | 6 | 0 | ✅ Fixed |

## Search Score Baselines (Before Re-indexing)

| Query | Top 5 Scores (Current Qdrant) |
|-------|-------------------------------|
| криптография | 0.5692, 0.5394, 0.5394, 0.5394, 0.5394 |
| защита информации | 0.8267, 0.8267, 0.8267, 0.8267, 0.6785 |
| шифрование ключи | 0.6508, 0.6356, 0.6213, 0.6210, 0.6186 |

## Next Steps Required

### 1. Clear Qdrant Collection
Qdrant currently has auth issues. Need to:
- Stop RAG service
- Clear Qdrant collection manually or via API with proper auth
- Restart services

### 2. Re-ingest Re-chunked Documents
Use RAG service ingestion endpoint:
```bash
curl -X POST http://localhost:5000/api/rag/ingest \
  -H "Authorization: Bearer TOKEN" \
  -F "files=@gost-r-52069_2c53c42c.txt" \
  -F "files=@r-1323565.1_78b35e61.txt"
```

### 3. Re-run Search Benchmark
After re-indexing, run same queries:
- криптография
- защита информации  
- шифрование ключи

### 4. Expected Improvements
Based on benchmark research:
- **Higher top scores**: Should see 0.7-0.9+ for relevant documents
- **Better ranking**: Re-chunked documents should appear in top results
- **More consistent scores**: Less variance between top results

## Files Created

1. `/root/qwen/ai_agent/rechunk_recursive.py` - Recursive chunking script
2. `/root/qwen/ai_agent/chunk_backups/` - Backup of original chunks
3. `/root/qwen/ai_agent/search_benchmark_results.json` - Before scores
4. `/root/qwen/ai_agent/search_benchmark_after.json` - After scores (pending re-index)

## Recommendation

The chunking improvements are **significant**:
- Eliminated giant chunks (149K → 2K max)
- Fixed tiny chunks (52 → 278 min)
- Better size distribution for embeddings

**Expected outcome**: Once re-indexed, search quality should improve measurably, especially for queries targeting content in these 2 documents.

