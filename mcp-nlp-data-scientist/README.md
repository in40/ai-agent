# NLP Data Scientist MCP Server

An MCP server providing NLP entity extraction and document analysis tools using spaCy, NLTK, and LLM (LM Studio).

## Features

### Entity Extraction Tools

1. **extract_entities** - Extract entities using spaCy + pattern matching
   - Supports 15+ entity types (PERSON, ORG, STANDARD, TECHNOLOGY, etc.)
   - Pattern-based extraction for technical standards (GOST, ISO, RFC)
   - Technology term extraction

2. **extract_entities_llm** - Extract entities using LLM (LM Studio)
   - Better for domain-specific entities
   - Context-aware extraction
   - Model: qwen3-4b via LM Studio

3. **analyze_document** - Comprehensive document analysis
   - Entity extraction with statistics
   - Entity grouping by type
   - Support for both spaCy and LLM methods

4. **filter_entities** - Filter entities by type
   - Keep only specific entity types (e.g., STANDARD, ORGANIZATION)

5. **extract_standards** - Extract technical standards
   - GOST, ISO, IEC, RFC, NIST patterns
   - High accuracy for known standard formats

6. **compare_extraction_methods** - Compare spaCy vs LLM extraction
   - Overlap analysis
   - Jaccard similarity

### Entity Types Supported

| Type | Description | Examples |
|------|-------------|----------|
| STANDARD | Technical standards | GOST R 34.10-2012, ISO 27001 |
| ORGANIZATION | Companies, agencies | FSB Russia, ISO/IEC |
| TECHNOLOGY | Technical terms | elliptic curve cryptography |
| LOCATION | Geographical entities | Russian Federation |
| CONCEPT | Domain concepts | digital signature |
| PERSON | People | John Smith |
| DATE | Dates, times | 2012, January 2023 |
| LAW | Laws, regulations | GDPR, 152-FZ |

## Installation

```bash
cd mcp-nlp-data-scientist
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

## Usage

### Start Server

```bash
./start_nlp_server.sh
```

Or manually:
```bash
python -m mcp_nlp_server.server --port 3065 --register-with-registry
```

### Stop Server

```bash
./stop_nlp_server.sh
```

### Configuration

| Argument | Default | Description |
|----------|---------|-------------|
| --host | 127.0.0.1 | Server host |
| --port | 3065 | Server port |
| --registry-host | 127.0.0.1 | Registry server host |
| --registry-port | 3031 | Registry server port |
| --register-with-registry | true | Register with registry |
| --no-register | false | Don't register with registry |

## API Examples

### Extract Entities (spaCy)

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "extract_entities",
    "arguments": {
      "text": "GOST R 34.10-2012 was developed by FSB Russia using elliptic curve cryptography."
    }
  }
}
```

### Extract Entities (LLM)

```json
{
  "jsonrpc": "2.0",
  "id": "2",
  "method": "tools/call",
  "params": {
    "name": "extract_entities_llm",
    "arguments": {
      "text": "ISO 27001 defines requirements for information security management systems."
    }
  }
}
```

### Analyze Document

```json
{
  "jsonrpc": "2.0",
  "id": "3",
  "method": "tools/call",
  "params": {
    "name": "analyze_document",
    "arguments": {
      "text": "Full document text here...",
      "method": "both"
    }
  }
}
```

### Filter Entities

```json
{
  "jsonrpc": "2.0",
  "id": "4",
  "method": "tools/call",
  "params": {
    "name": "filter_entities",
    "arguments": {
      "entities": [...],
      "entity_types": ["STANDARD", "ORGANIZATION"]
    }
  }
}
```

## Architecture

```
mcp_nlp_server/
├── server.py              # Main server implementation
├── handlers/
│   └── nlp_handlers.py    # NLP tool handlers
├── nlp_tools/
│   ├── entity_extractor.py       # spaCy/NLTK extraction
│   └── llm_entity_extractor.py   # LLM extraction
├── transports/
│   └── streamable_http.py # HTTP transport
└── utils/
    ├── json_rpc.py       # JSON-RPC handling
    └── notifications.py  # Notification management
```

## LLM Configuration

Default LM Studio configuration:
- URL: http://192.168.51.237:1234/v1
- Model: qwen3-4b
- Auth: None

To change, edit `mcp_nlp_server/handlers/nlp_handlers.py`.

## Registry Integration

This server automatically registers with the MCP registry on port 3031.

Registered capabilities:
- 8 NLP tools
- 2 resources
- 2 prompt templates

## Testing

See `test_nlp_server.py` for AI agent simulation tests.

## License

Same as parent project (ai-orchestration)
