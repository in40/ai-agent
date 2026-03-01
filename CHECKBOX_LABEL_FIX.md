# Checkbox Label Fix

**Date:** February 28, 2026  
**Status:** ✅ Complete  

---

## Changes Made

### 1. Updated Checkbox Label

**Before:**
```
☑️ Show Raw Results (context sent to LLM)
```

**After:**
```
☑️ Show Raw Results (retrieved documents)
```

**Why:** More accurate - shows retrieval results with metadata, not the actual formatted prompt sent to LLM.

---

### 2. Mode-Aware Checkbox Behavior

**Hybrid/Vector Mode:**
- ✅ Checkbox enabled
- Label: "Show Raw Results (retrieved documents)"
- User can toggle raw JSON display

**Retrieve Only Mode:**
- ⚪ Checkbox grayed out (disabled)
- Label: "Show Raw Results (always shown for Retrieve Only)"
- Raw JSON always displayed (no need for checkbox)

---

### 3. Visual Changes

**When "Retrieve Only" selected:**
```
┌─────────────────────────────────────────┐
│ [🔷 Hybrid] [Vector] [🔍 Retrieve Only] │
│                                         │
│ [Query Input] [📨 Query]                │
│                                         │
│ ☐ Show Raw Results (always shown...)    │  ← Grayed out
│                                         │
│ [Raw JSON ALWAYS SHOWN below]           │
└─────────────────────────────────────────┘
```

**When "Hybrid/Vector" selected:**
```
┌─────────────────────────────────────────┐
│ [🔷 Hybrid] [Vector] [🔍 Retrieve Only] │
│                                         │
│ [Query Input] [📨 Query]                │
│                                         │
│ ☑️ Show Raw Results (retrieved docs)    │  ← Enabled
│                                         │
│ [Raw JSON shown if checked]             │
└─────────────────────────────────────────┘
```

---

## Code Changes

### HTML (`index.html`)

**Added IDs for dynamic control:**
```html
<div class="form-check mt-2" id="show-raw-results-container">
    <input class="form-check-input" type="checkbox" id="show-raw-results">
    <label class="form-check-label" for="show-raw-results">
        <i class="fas fa-code"></i> 
        <span id="show-raw-results-label">
            Show Raw Results (retrieved documents)
        </span>
    </label>
</div>
```

### JavaScript (`index.html`)

**Mode selection handler:**
```javascript
ragModeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        
        if (mode === 'retrieve') {
            // Gray out checkbox
            showRawResultsContainer.style.opacity = '0.5';
            showRawResultsContainer.style.pointerEvents = 'none';
            document.getElementById('show-raw-results').disabled = true;
            showRawResultsLabel.textContent = 
                'Show Raw Results (always shown for Retrieve Only)';
        } else {
            // Enable checkbox
            showRawResultsContainer.style.opacity = '1';
            showRawResultsContainer.style.pointerEvents = 'auto';
            document.getElementById('show-raw-results').disabled = false;
            showRawResultsLabel.textContent = 
                'Show Raw Results (retrieved documents)';
        }
    });
});
```

**Query handler simplified:**
```javascript
// Removed confusing logic
const showRawResults = showRawResultsCheckbox.checked;  // Simple!

// Retrieve mode always shows raw results
if (ragMode === 'retrieve') {
    rawResultsContent.textContent = JSON.stringify(result.documents, null, 2);
    rawResultsContainer.style.display = 'block';
}
```

---

## Behavior Matrix

| Mode | Checkbox State | Label | Raw JSON Display |
|------|----------------|-------|------------------|
| **Hybrid** | ✅ Enabled | "retrieved documents" | When checked |
| **Vector** | ✅ Enabled | "retrieved documents" | When checked |
| **Retrieve Only** | ⚪ Disabled (gray) | "always shown" | Always |

---

## User Experience

### Before (Confusing)
```
User selects "Retrieve Only"
    ↓
Checkbox still enabled
    ↓
Label says "context sent to LLM"
    ↓
But NO LLM is called! ❌
    ↓
User confused
```

### After (Clear)
```
User selects "Retrieve Only"
    ↓
Checkbox grays out
    ↓
Label changes to "always shown"
    ↓
Raw JSON always displayed
    ↓
User understands ✅
```

---

## Testing

### Test Checkbox Behavior

```bash
# Via UI:
# 1. Go to Query RAG tab
# 2. Select "Hybrid" - checkbox enabled, normal label
# 3. Select "Vector" - checkbox enabled, normal label
# 4. Select "Retrieve Only" - checkbox grayed, different label
# 5. Switch back to "Hybrid" - checkbox re-enabled
```

### Expected Results

**Hybrid/Vector:**
- Checkbox clickable
- Label: "Show Raw Results (retrieved documents)"
- Raw JSON shown/hidden based on checkbox

**Retrieve Only:**
- Checkbox grayed out (disabled)
- Label: "Show Raw Results (always shown for Retrieve Only)"
- Raw JSON always shown

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/web_client/index.html` | Added IDs, updated label, added mode-aware logic |

---

## Summary

**Problem:** Checkbox label was misleading ("context sent to LLM") and checkbox behavior was confusing for Retrieve Only mode.

**Solution:** 
1. Renamed label to "retrieved documents" (accurate)
2. Gray out checkbox for Retrieve Only (always shows raw results)
3. Dynamic label changes based on mode

**Result:** Clear, intuitive UI that matches user expectations.
