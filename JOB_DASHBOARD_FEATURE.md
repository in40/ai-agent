# Job Dashboard - Smart Ingestion

## Overview

The **Job Dashboard** provides a web interface for monitoring background processing jobs. When processing large document sets (>50 documents), jobs run asynchronously and can be tracked in real-time through this dashboard.

## Features

### Job Dashboard Tab

Located in the **RAG Functions** section, the new **Job Dashboard** tab shows:

- **All your jobs** (last 20)
- **Real-time status** with auto-refresh every 3 seconds
- **Progress bars** showing completion percentage
- **Stage indicators** (queued → downloading → chunking → ingesting → completed)
- **Cancel button** for running jobs
- **View Results** button for completed jobs
- **Pending jobs badge** on the tab showing count of active jobs

### Automatic Background Processing

When you submit a web page for processing:
- **≤50 documents**: Processed immediately (synchronous)
- **>50 documents**: Background job created automatically
- **Job ID returned**: Can track progress in dashboard

## Usage

### 1. Submit Job via Smart Ingestion

```
1. Go to RAG Functions → Smart Ingestion
2. Select "Process Web Page" mode
3. Enter URL with many documents (>50)
4. Click "Process Web Page"
5. Receive job ID and redirect info
```

### 2. Monitor Progress

```
1. Click "Job Dashboard" tab
2. See all jobs with status badges
3. Progress updates automatically every 3 seconds
4. Watch as status changes:
   - pending → processing → completed
```

### 3. View Results

```
1. When job shows "completed" status
2. Click "View Results" button
3. See summary:
   - Documents processed
   - Chunks generated
   - Documents ingested
```

### 4. Cancel Job (if needed)

```
1. Find running job in dashboard
2. Click "Cancel" button
3. Confirm cancellation
4. Job status changes to "cancelled"
```

## UI Components

### Job Card

Each job displays as a card showing:

```
┌─────────────────────────────────────────────────┐
│ ⏱️ Web Page Processing (job_abc123)             │
│ Created: 2026-02-22 14:00 | Status: processing │
│                                                  │
│ Progress: 45%          Stage: chunking         │
│ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░ [45%]   │
│                                                  │
│ Documents: 45/100    Chunks: 675    Updated... │
│                                      [Cancel]   │
└─────────────────────────────────────────────────┘
```

### Status Badges

| Status | Color | Icon |
|--------|-------|------|
| pending | Gray | 🕐 clock |
| processing | Blue | 🔄 spinner |
| completed | Green | ✅ check |
| failed | Red | ❌ times |
| cancelled | Yellow | 🚫 ban |

### Pending Jobs Badge

The Job Dashboard tab shows a badge with count of active jobs:

```
📋 Job Dashboard [3]
```

## Real-time Updates

### Auto-refresh Mechanism

- **Polling interval**: 3 seconds
- **Active jobs only**: Stops polling when completed/failed
- **Automatic badge update**: Shows current pending count
- **Cleanup on page unload**: Stops polling to save resources

### Visual Indicators

- **Spinning icon**: Job is actively processing
- **Progress bar animation**: Shows activity
- **Stage updates**: Reflects current processing phase
- **Timestamp updates**: Shows last update time

## API Integration

### Endpoints Used

```javascript
// Load user's jobs
GET /api/rag/jobs/user/{userId}?limit=20

// Get single job status
GET /api/rag/jobs/{jobId}

// Cancel job
POST /api/rag/jobs/{jobId}/cancel
```

### Frontend Code

```javascript
// Load jobs when tab clicked
jobsTab.addEventListener('click', loadUserJobs);

// Poll for updates every 3 seconds
setInterval(async () => {
  const job = await fetch(`/api/rag/jobs/${jobId}`);
  updateJobCard(job);
}, 3000);

// Stop polling when done
if (job.status === 'completed' || job.status === 'failed') {
  clearInterval(pollInterval);
}
```

## Files Modified

### Created
- None (all integrated into existing files)

### Modified
- `/backend/web_client/index.html`
  - Added Job Dashboard tab with badge
  - Added Job Dashboard panel HTML
  - Added JavaScript for job management
  - Added polling mechanism
  - Added cancel/view results functionality

## Configuration

No additional configuration needed. Uses existing:
- `API_BASE_URL` - For API endpoints
- `AUTH_TOKEN` - For authentication
- `REDIS_HOST` - For job storage (optional)

## Browser Compatibility

- **Modern browsers**: Chrome, Firefox, Safari, Edge
- **Features used**:
  - `fetch()` API
  - `setInterval()` / `clearInterval()`
  - `atob()` for token decoding
  - ES6 template literals
  - Optional chaining (`?.`)

## Performance Considerations

### Client-side

- **Polling**: Max 20 jobs × 3 second interval = ~7 requests/minute
- **DOM updates**: Only updates changed job cards
- **Memory**: Cleans up intervals on page unload

### Server-side

- **Redis**: Fast job status lookups
- **In-memory fallback**: Works without Redis
- **Job expiration**: 24-hour retention prevents buildup

## Future Enhancements

Potential improvements:

1. **WebSocket support** - Real-time push updates instead of polling
2. **Filtering** - Show only completed/failed/running jobs
3. **Sorting** - Sort by date, status, progress
4. **Pagination** - Load more than 20 jobs
5. **Detailed results view** - Modal with full results
6. **Download results** - Export as JSON/CSV
7. **Job grouping** - Group by date or type
8. **Notifications** - Browser notifications on completion

## Troubleshooting

### Jobs not appearing

**Check:**
- Authentication token is valid
- User ID matches token
- API endpoint is accessible
- Browser console for errors

### Progress not updating

**Check:**
- JavaScript console for polling errors
- Network tab for failed requests
- Job actually running (not stuck)
- Redis connection (if using)

### Cancel not working

**Check:**
- Job still in processing state
- Permissions (WRITE_RAG required)
- Network connectivity
- Server logs for errors

## Example Workflow

```
1. User submits URL with 150 documents
   ↓
2. System creates background job_abc123
   ↓
3. User clicks "Job Dashboard" tab
   ↓
4. Sees job with status: pending, progress: 0%
   ↓
5. Job starts: status → processing, progress → 5%
   ↓
6. Downloads complete: progress → 30%, stage → chunking
   ↓
7. Chunking done: progress → 70%, stage → ingesting
   ↓
8. Ingestion done: progress → 100%, status → completed
   ↓
9. User clicks "View Results"
   ↓
10. Sees: 150 docs processed, 2250 chunks generated
```

## Summary

The Job Dashboard provides:
- ✅ **Visibility** into background processing
- ✅ **Control** to cancel jobs if needed
- ✅ **Feedback** with real-time progress
- ✅ **Convenience** to return later for results
- ✅ **Scalability** to handle large document sets

No more wondering "is it done yet?" - just check the dashboard!
