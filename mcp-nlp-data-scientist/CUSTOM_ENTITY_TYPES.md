# Custom Entity Types Guide

## Overview

The NLP Data Scientist MCP server supports **custom entity types** in addition to standard spaCy entities. This allows you to extract domain-specific terms relevant to your use case (e.g., GOST standards, regulatory documents, technical terms).

---

## Available Custom Entity Types

| Entity Type | Description | Example |
|-------------|-------------|---------|
| **GOST_STANDARD** | GOST standards (Russian national standards) | "ГОСТ Р 50922-2006" |
| **REGULATORY_DOC** | Regulatory documents (laws, decrees, orders) | "Федеральный закон № 152-ФЗ" |
| **TECHNICAL_TERM** | Technical terms (cryptography, security) | "электронная подпись" |
| **ORGANIZATION_RU** | Russian government organizations | "Федеральное агентство" |
| **DOCUMENT_SECTION** | Document sections, appendices, articles | "Раздел 3", "Приложение А" |
| **DATE_RU** | Russian format dates | "27 декабря 2006" |
| **MEASUREMENT** | Measurements and units | "256 бит", "10 КБ" |
| **SOFTWARE_PRODUCT** | Software products and systems | "СКЗИ", "система защиты" |

---

## How It Works

Custom entity types are implemented using **spaCy's EntityRuler** component, which uses rule-based pattern matching:

1. **Patterns are defined** in `custom_entity_types.py`
2. **EntityRuler is added** to the spaCy pipeline before the NER component
3. **Patterns are matched** during text processing
4. **Custom entities are extracted** alongside standard spaCy entities

---

## Adding Your Own Custom Entity Types

### Step 1: Edit `custom_entity_types.py`

Add your custom entity type to the `CUSTOM_ENTITY_PATTERNS` dictionary:

```python
CUSTOM_ENTITY_PATTERNS = {
    "MY_CUSTOM_TYPE": {
        "patterns": [
            # Pattern 1: Match exact words
            [{"TEXT": "exact_word"}],
            
            # Pattern 2: Match with regex
            [{"TEXT": {"REGEX": r"pattern_here"}}],
            
            # Pattern 3: Match multiple words
            [{"TEXT": "first"}, {"TEXT": "second"}],
        ],
        "description": "Description of my custom type"
    }
}
```

### Step 2: Add to `CUSTOM_ENTITY_TYPES`

```python
CUSTOM_ENTITY_TYPES = {
    "MY_CUSTOM_TYPE": "Description of my custom type"
}
```

### Step 3: Restart the Server

```bash
./stop_nlp_server.sh
./start_nlp_server.sh
```

---

## Pattern Syntax

### Exact Word Matching

```python
{"TEXT": "ГОСТ"}  # Matches exact word "ГОСТ"
```

### Regex Matching

```python
{"TEXT": {"REGEX": r"\d{4}"}}  # Matches 4 digits
{"TEXT": {"REGEX": r"[А-Я][а-я]+"}}  # Matches capitalized words
```

### Multi-Word Patterns

```python
[{"TEXT": "Федеральный"}, {"TEXT": "закон"}]  # Matches "Федеральный закон"
```

### Optional Words

```python
[{"TEXT": "ГОСТ"}, {"TEXT": {"REGEX": r"[Рр]?"}}, {"TEXT": {"REGEX": r"\d+"}}]
# Matches: "ГОСТ 1234", "ГОСТ Р 1234", "ГОСТ р 1234"
```

---

## Usage Examples

### Example 1: Extract Entities with Custom Types

```bash
curl -X POST http://localhost:3065/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "extract_entities",
      "arguments": {
        "text": "ГОСТ Р 50922-2006 утверждает Федеральный закон № 152-ФЗ"
      }
    }
  }'
```

**Response:**
```json
{
  "entities": [
    {
      "text": "ГОСТ Р 50922-2006",
      "label": "STANDARD"
    },
    {
      "text": "Федеральный закон № 152-ФЗ",
      "label": "REGULATORY_DOC"
    }
  ]
}
```

### Example 2: Get Available Entity Types

```bash
curl -X POST http://localhost:3065/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "get_entity_types",
      "arguments": {}
    }
  }'
```

---

## Disabling Custom Entity Types

If you want to use only standard spaCy entities:

```python
# In entity_extractor.py initialization
extractor = EntityExtractor(use_custom_types=False)
```

Or via API:
```json
{
  "name": "extract_entities",
  "arguments": {
    "text": "...",
    "use_custom_types": false
  }
}
```

---

## Pattern Examples for Common Use Cases

### Company Names
```python
{"patterns": [
    [{"TEXT": {"REGEX": r"[А-Я][а-я]+(ООО|АО|ЗАО|ОOO)"}},]
]}
```

### Product Versions
```python
{"patterns": [
    [{"TEXT": {"REGEX": r"верси[яию]\s+\d+\.\d+"}},]
]}
```

### Currency Amounts
```python
{"patterns": [
    [{"TEXT": {"REGEX": r"\d+\s*(рублей|долларов|евро)"}},]
]}
```

### Person Titles
```python
{"patterns": [
    [{"TEXT": "господин"}, {"TEXT": {"REGEX": r"[А-Я][а-я]+"}},],
    [{"TEXT": "доктор"}, {"TEXT": {"REGEX": r"[А-Я][а-я]+"}},],
]}
```

---

## Troubleshooting

### Issue: "bad character range" Error

**Cause:** Regex character class has invalid range (e.g., `[\s-–—]`)

**Fix:** Escape the hyphen or put it at the end: `[\s\-–—]` or `[\s–—-]`

### Issue: Custom Types Not Appearing

**Check:**
1. Server logs for "Added X custom entity patterns" message
2. Pattern syntax is correct
3. Entity type is in both `CUSTOM_ENTITY_PATTERNS` and `CUSTOM_ENTITY_TYPES`

### Issue: Low Precision

**Solution:** Make patterns more specific:
```python
# Too broad
{"TEXT": {"REGEX": r"\d+"}}

# More specific
{"TEXT": {"REGEX": r"№\s*\d+-\w+"}}
```

---

## Best Practices

1. **Start with specific patterns** - Don't make them too broad
2. **Test with real documents** - Verify patterns match expected text
3. **Use regex for variations** - Handle case differences, optional words
4. **Document your patterns** - Add clear descriptions
5. **Monitor false positives** - Adjust patterns if too many incorrect matches

---

## Files to Modify

| File | Purpose |
|------|---------|
| `mcp_nlp_server/nlp_tools/custom_entity_types.py` | Define custom patterns and types |
| `mcp_nlp_server/nlp_tools/entity_extractor.py` | EntityExtractor class (auto-loads custom types) |

---

## Additional Resources

- [spaCy EntityRuler Documentation](https://spacy.io/usage/rule-based-matching#entityruler)
- [spaCy Token Attributes](https://spacy.io/usage/rule-based-matching#token-properties)
- [Regex Testing Tool](https://regex101.com/)
