# Background Job Processing - Smart Ingestion

## Overview

The Smart Ingestion system now supports **background job processing** for large document sets. When processing more than 50 documents (configurable), the system automatically creates a background job that processes documents asynchronously.

## Key Features

### Automatic Background Processing
- **Threshold**: Documents > 50 → Background job (configurable via `SMART_INGESTION_BACKGROUND_THRESHOLD`)
- **Synchronous**: Documents ≤ 50 → Immediate processing
- **Manual Override**: Can force background mode with `use_background: true`

### Job Queue System
- **Redis-backed** (with in-memory fallback)
- **24-hour retention** for job data
- **Real-time progress** tracking (0-100%)
- **Stage tracking**: queued → downloading → chunking → ingesting → completed

### Job Status Dashboard
- View all your jobs
- Real-time progress updates
- Cancel pending jobs
- Access results when complete

## API Endpoints

### Create Background Job
```bash
POST /api/rag/jobs
{
  "user_id": "username",
  "job_type": "web_page",
  "parameters": {
    "url": "https://example.com/docs",
    "prompt": "...",
    "ingest_chunks": true,
    "document_urls": [...]
  }
}

Response:
{
  "job_id": "job_abc123",
  "status": "pending",
  "check_status_url": "/api/rag/jobs/job_abc123"
}
```

### Get Job Status
```bash
GET /api/rag/jobs/<job_id>

Response:
{
  "job_id": "job_abc123",
  "status": "processing",
  "progress": 45,
  "current_stage": "chunking",
  "documents_total": 100,
  "documents_processed": 30,
  "chunks_generated": 450,
  "result": null,
  "error": null
}
```

### Get User's Jobs
```bash
GET /api/rag/jobs/user/<user_id>?limit=20

Response:
{
  "jobs": [
    {
      "job_id": "job_abc123",
      "job_type": "web_page",
      "status": "completed",
      "progress": 100,
      "created_at": "2026-02-22T14:00:00",
      "documents_processed": 100,
      "chunks_generated": 1500
    }
  ],
  "total": 5
}
```

### Cancel Job
```bash
POST /api/rag/jobs/<job_id>/cancel

Response:
{
  "message": "Job cancelled successfully"
}
```

## Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job queued, waiting for worker |
| `processing` | Job actively being processed |
| `completed` | Job finished successfully |
| `failed` | Job failed with error |
| `cancelled` | Job was cancelled by user |

## Progress Stages

| Stage | Progress Range | Description |
|-------|---------------|-------------|
| `queued` | 0% | Job waiting in queue |
| `initializing` | 0-5% | Setting up job |
| `downloading` | 5-30% | Downloading documents via MCP |
| `chunking` | 30-70% | LLM-based semantic chunking |
| `ingesting` | 70-100% | Adding chunks to vector DB |
| `completed` | 100% | Job finished |

## Configuration

### Environment Variables

```bash
# Redis configuration (optional, falls back to in-memory)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Background processing threshold
SMART_INGESTION_BACKGROUND_THRESHOLD=50

# Parallelism settings
PARALLELISM=8
DOWNLOAD_PARALLELISM=8
CHUNKING_PARALLELISM=4
INGESTION_PARALLELISM=4
```

## Frontend Integration

### Polling for Status Updates

```javascript
// After submitting a job
const jobId = response.job_id;

// Poll every 3 seconds
const pollInterval = setInterval(async () => {
  const status = await fetch(`/api/rag/jobs/${jobId}`, {
    headers: {'Authorization': `Bearer ${token}`}
  }).then(r => r.json());
  
  console.log(`Progress: ${status.progress}% - ${status.current_stage}`);
  
  if (status.status === 'completed' || status.status === 'failed') {
    clearInterval(pollInterval);
    // Show results or error
  }
}, 3000);
```

### Job Dashboard UI

Create a dashboard page at `/rag/jobs` that:
1. Lists all user jobs (sorted by created_at)
2. Shows real-time status badges
3. Displays progress bars
4. Allows cancelling pending jobs
5. Shows results/errors on completion

## Error Handling

### Common Errors

**"No documents were successfully downloaded"**
- Check Download MCP server status
- Verify URLs are accessible
- Check network connectivity

**"Failed to parse LLM response"**
- LLM service unavailable
- Invalid JSON from LLM
- Try smaller documents

**"Redis not available"**
- System falls back to in-memory storage
- Jobs lost on service restart
- Install/configure Redis for production

## Performance Considerations

### Resource Usage

| Document Count | Processing Mode | Est. Time | Memory |
|---------------|-----------------|-----------|--------|
| 1-50 | Synchronous | 1-5 min | Low |
| 51-200 | Background | 5-20 min | Medium |
| 201-500 | Background | 20-60 min | High |
| 500+ | Background (batched) | 1-3 hrs | Very High |

### Best Practices

1. **Use Redis** for production (jobs persist across restarts)
2. **Set reasonable limits** (max 1000 documents per job)
3. **Monitor queue length** (avoid overwhelming system)
4. **Clean up old jobs** (24-hour retention is default)
5. **Provide user feedback** (show progress, not just spinner)

## Future Enhancements

Potential improvements:
1. **Job priorities** (premium users get faster processing)
2. **Scheduled jobs** (process at off-peak hours)
3. **Webhook notifications** (notify when complete)
4. **Job templates** (save common configurations)
5. **Batch operations** (process multiple URLs at once)
6. **Export results** (download chunks as JSON/CSV)
