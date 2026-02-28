# Graph Explorer Feature

## Overview

Added a **Graph Explorer** tab to the RAG Functions section of the Web UI, allowing users to visualize and explore the Neo4j knowledge graph interactively using force-directed graph visualization.

---

## Features

### 🎯 Core Capabilities

1. **Interactive Graph Visualization**
   - Force-directed layout using `force-graph` library
   - Color-coded nodes by entity type
   - Click nodes to see details and connections
   - Zoom, pan, and drag to explore

2. **Filtering & Search**
   - Filter by entity types (STANDARD, ORGANIZATION, TECHNOLOGY, etc.)
   - Search entities by name
   - Limit max nodes displayed (50-500)

3. **Real-time Statistics**
   - Total entities in graph
   - Total relationships
   - Visible nodes count
   - Entity type breakdown

4. **Entity Details Panel**
   - View entity properties (name, type, document, source, confidence)
   - See connected entities
   - Click connections to navigate graph

---

## Entity Type Color Coding

| Type | Color | Hex Code |
|------|-------|----------|
| **STANDARD** | Red | `#ff6b6b` |
| **ORGANIZATION** | Teal | `#4ecdc4` |
| **TECHNOLOGY** | Blue | `#45b7d1` |
| **LOCATION** | Yellow | `#f9ca24` |
| **DATE** | Purple | `#a55eea` |
| **PERSON** | Orange | `#fd9644` |
| **CONCEPT** | Green | `#26de81` |

---

## Technical Implementation

### Frontend Components

**File:** `backend/web_client/index.html`

#### 1. New Tab Button (lines ~562-567)
```html
<button class="nav-link" id="graph-explorer-tab" data-bs-toggle="tab" data-bs-target="#graph-explorer-panel">
    <i class="fas fa-project-diagram"></i> Graph Explorer
</button>
```

#### 2. Graph Explorer Panel (lines ~1011-1155)
- Graph controls (filters, search, limit)
- Statistics cards (4 metrics)
- Graph visualization container (600px height)
- Entity details panel

#### 3. JavaScript Functions (lines ~4047-4360)
- `initGraphExplorer()` - Initialize force-graph instance
- `loadGraphData()` - Fetch graph from API
- `handleNodeClick()` - Show entity details
- `loadEntityConnections()` - Load connected entities
- `getEntityColor()` - Map types to colors
- `updateGraphStats()` - Update statistics display

### Backend API Endpoints

**File:** `backend/services/rag/app.py`

#### 1. `/api/rag/graph/visualize` (POST)
Returns graph data for visualization.

**Request:**
```json
{
    "entity_types": ["STANDARD", "ORGANIZATION"],
    "search_query": "gost",
    "limit": 100
}
```

**Response:**
```json
{
    "nodes": [
        {
            "id": "node_id",
            "name": "GOST R 34.10-2012",
            "type": "STANDARD",
            "relevance": 0.9,
            "document": "gost-r-34.pdf",
            "source": "job_abc123",
            "confidence": 0.95
        }
    ],
    "links": [
        {
            "source": "GOST R 34.10-2012",
            "target": "ФСБ России",
            "relationship": "PUBLISHED_BY"
        }
    ],
    "type_counts": {
        "STANDARD": 6,
        "ORGANIZATION": 5,
        "total": 52
    }
}
```

#### 2. `/api/rag/graph/entity/connections` (POST)
Returns connections for a specific entity.

**Request:**
```json
{
    "entity_name": "GOST R 34.10-2012",
    "entity_type": "STANDARD",
    "limit": 20
}
```

**Response:**
```json
{
    "entity_name": "GOST R 34.10-2012",
    "entity_type": "STANDARD",
    "connections": [
        {
            "target_name": "ФСБ России",
            "target_type": "ORGANIZATION",
            "relationship": "PUBLISHED_BY",
            "relevance": 0.8,
            "document": "gost-r-34.pdf"
        }
    ],
    "total": 5
}
```

---

## Libraries Used

### Frontend
| Library | Version | Purpose |
|---------|---------|---------|
| **D3.js** | v7 | Force-directed layout engine |
| **Force Graph** | v1.44.4 | Graph visualization component |
| **React** | v18 | UI framework (included for future expansion) |
| **Bootstrap 5** | v5.3.0 | UI styling |
| **Font Awesome** | v6.0.0 | Icons |

### Backend
| Component | Purpose |
|-----------|---------|
| **Neo4j Python Driver** | Graph database queries |
| **Flask** | API endpoints |
| **Security decorators** | Permission checks |

---

## Usage Guide

### 1. Open Graph Explorer
- Navigate to **RAG Functions** tab
- Click **Graph Explorer** subtab
- Graph loads automatically on first visit

### 2. Filter Entities
- Hold **Ctrl** and select entity types from the dropdown
- Click **Load Graph** or **Refresh**

### 3. Search Entities
- Enter search term in "Search Entity" field
- Searches entity names and descriptions
- Click **Load Graph**

### 4. Explore Graph
- **Drag** nodes to reposition
- **Scroll** to zoom in/out
- **Click** node to see details
- **Click** connected entity in details panel to navigate

### 5. View Entity Details
- Click any node
- Details panel shows:
  - Entity name and type
  - Properties (ID, document, source, confidence)
  - Connected entities list
- Click connection to jump to that entity

---

## Screenshots

### Graph Explorer Tab
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Neo4j Graph Explorer                                     │
├─────────────────────────────────────────────────────────────┤
│ 🔍 Graph Controls                                           │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │Entity    │Search    │Max Nodes │  Load    │              │
│ │Types [×] │Entity    │[100 ▼]   │  Graph   │              │
│ │STANDARD  │[_______] │          │  [🔍]    │              │
│ │ORG...    │          │          │          │              │
│ └──────────┴──────────┴──────────┴──────────┘              │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┬────────────┬──────────┬──────────┐             │
│ │ Total   │ Relation-  │ Visible  │ Entity   │             │
│ │Entities │ ships      │ Nodes    │ Types    │             │
│ │   52    │     20     │    45    │    6     │             │
│ └─────────┴────────────┴──────────┴──────────┘             │
├─────────────────────────────────────────────────────────────┤
│ 👁️ Graph Visualization                                     │
│                                                             │
│         ● STANDARD                                          │
│        / \                                                  │
│       /   \                                                 │
│  ● ORGANIZATION  ● TECHNOLOGY                               │
│      |       \   /                                          │
│      |        \ /                                           │
│  ● CONCEPT  ● LOCATION                                      │
│                                                             │
│  [Drag nodes to explore]                                    │
├─────────────────────────────────────────────────────────────┤
│ ℹ️ Entity Details                              [×] Close    │
│ ┌─────────────────────────┬──────────────────┐             │
│ │ GOST R 34.10-2012       │ Connected        │             │
│ │ Standards               │ Entities         │             │
│ │                         │ ┌──────────────┐ │             │
│ │ Document: gost-r-34.pdf │ │ ФСБ России   │ │             │
│ │ Confidence: 95%         │ │ Organization │ │             │
│ │                         │ └──────────────┘ │             │
│ └─────────────────────────┴──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Node Limits
| Limit | Use Case | Performance |
|-------|----------|-------------|
| 50 | Quick preview | < 1 second |
| 100 | Default view | 1-2 seconds |
| 200 | Detailed exploration | 2-4 seconds |
| 500 | Full graph analysis | 5-10 seconds |

### Optimization Tips
1. **Filter by type** - Reduces nodes loaded
2. **Use search** - Focus on relevant entities
3. **Lower limit** - Faster initial load
4. **Refresh as needed** - Get updated data

---

## Known Limitations

1. **Large Graphs** - 500+ nodes may be slow to render
2. **Neo4j Connection** - Requires SSH tunnel to be active
3. **No Layout Persistence** - Layout resets on refresh
4. **Limited Relationship Types** - Shows all relationships, can't filter by type

---

## Future Enhancements

### Planned Features
1. **Relationship Type Filtering** - Show/hide specific relationship types
2. **Graph Layout Save** - Save and restore node positions
3. **Export Graph** - Download as PNG/SVG
4. **Time-based View** - Filter by entity creation date
5. **Path Finding** - Find connections between two entities
6. **Cluster Detection** - Highlight communities/groups
7. **Search History** - Remember recent searches
8. **Bookmarks** - Save interesting graph views

### Performance Improvements
1. **Progressive Loading** - Load nodes in batches
2. **Web Workers** - Offload layout calculations
3. **Canvas Rendering** - Better performance for large graphs
4. **Caching** - Cache graph data for repeated views

---

## Troubleshooting

### Graph Not Loading
```
Problem: "Failed to load graph: Neo4j not available"

Solution:
1. Check SSH tunnel: ssh -N -f -L 7687:localhost:7687 sorokin@192.168.51.187
2. Verify Neo4j is running on remote server
3. Check credentials in .env file
```

### No Entities Shown
```
Problem: "No entities found matching your criteria"

Solution:
1. Clear search query
2. Select all entity types
3. Increase node limit
4. Check if graph has data: python check_neo4j_graph.py
```

### Slow Performance
```
Problem: Graph is slow to load or interact

Solution:
1. Reduce node limit (50-100)
2. Filter by specific entity types
3. Use search to focus on relevant entities
4. Close other browser tabs
```

---

## Files Modified

| File | Lines Added | Purpose |
|------|-------------|---------|
| `backend/web_client/index.html` | ~350 | Graph Explorer UI + JavaScript |
| `backend/services/rag/app.py` | ~170 | API endpoints for graph data |

---

## Testing

### Manual Test Steps

1. **Basic Load Test**
   ```
   - Open Graph Explorer tab
   - Wait for auto-load
   - Verify nodes appear
   - Check statistics match Neo4j data
   ```

2. **Filter Test**
   ```
   - Select only "STANDARD" type
   - Click "Load Graph"
   - Verify only red nodes shown
   - Check type count = 1
   ```

3. **Search Test**
   ```
   - Enter "gost" in search
   - Click "Load Graph"
   - Verify filtered results
   - Check all nodes match search
   ```

4. **Interaction Test**
   ```
   - Click a node
   - Verify details panel appears
   - Check connections listed
   - Click a connection
   - Verify graph centers on new node
   ```

5. **Zoom/Pan Test**
   ```
   - Scroll to zoom
   - Drag to pan
   - Click "Fit to Screen"
   - Verify graph centers and fits
   ```

---

## API Reference

### GET `/api/rag/graph/stats`
Get graph statistics.

**Response:**
```json
{
    "total_entities": 52,
    "entities_by_type": {
        "CONCEPT": 29,
        "STANDARD": 6,
        "TECHNOLOGY": 6
    },
    "total_relationships": 20,
    "top_entities": [...]
}
```

### POST `/api/rag/graph/search`
Search graph entities.

**Request:**
```json
{
    "query": "gost",
    "entity_types": ["STANDARD"],
    "limit": 20
}
```

### GET `/api/rag/graph/entity/<entity_name>`
Get specific entity details.

---

**Status:** ✅ Implemented  
**Date:** February 27, 2026  
**Version:** v0.8.14  
**Location:** RAG Functions → Graph Explorer tab
