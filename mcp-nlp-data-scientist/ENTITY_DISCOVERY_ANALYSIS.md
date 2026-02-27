# Entity Discovery Analysis Results

## Analysis Date
2026-02-27

## Documents Analyzed
1. gost-r-50922-2006.pdf (12 pages)
2. gost-r-34_1.pdf (16 pages)  
3. r-1323565.1_18.pdf (36 pages)

## Method
- Extracted text samples from PDFs
- Sent to LLM (qwen3-4b via LM Studio) with entity discovery prompt
- Received structured JSON with entity type recommendations

---

## LLM-Recommended Entity Types

### Priority 1: HIGH Importance

| Entity Type | Description | Examples | Frequency |
|-------------|-------------|----------|-----------|
| **STANDARD_REFERENCE** | Technical standards (GOST, ISO, etc.) with specific numbering formats | "ГОСТ Р 50922-2006", "ГОСТ Р 34.12—2015" | Common |
| **REGULATORY_DOCUMENT** | Laws, decrees, and official documents with numerical identifiers | "Федеральный закон № 152-ФЗ", "Приказ № 749-ст" | Common |
| **TECHNICAL_SYSTEM** | Cybersecurity systems and cryptographic infrastructure | "СКЗИ", "шифрование", "электронная подпись" | Common |
| **DATE_RU** | Russian formatted dates with specific calendar patterns | "27 декабря 2006", "19 июня 2015" | Common |
| **ORGANIZATION_RU** | Government and industry organizations with specific naming conventions | "Федеральное агентство", "ФСБ России" | Common |

### Priority 2: MEDIUM Importance

| Entity Type | Description | Examples | Frequency |
|-------------|-------------|----------|-----------|
| **CRYPTO_TERM** | Cybersecurity terminology related to encryption and digital signatures | "криптографическая защита", "блоки шифрования" | Common |
| **PROCESS_STAGE** | Technical process stages in cybersecurity workflows | "формирование подписи", "проверка ключа" | Occasional |
| **VULNERABILITY** | Security vulnerabilities and technical flaws | "критическая ошибка", "уязвимость" | Occasional |
| **DOCUMENT_SECTION** | Document sections and appendices with numerical identifiers | "Раздел 3", "Приложение А" | Common |
| **MEASUREMENT** | Technical measurements and units in cybersecurity contexts | "256 бит", "10 КБ", "5 лет" | Occasional |

---

## Recommended Implementation Order

1. **STANDARD_REFERENCE** - Most frequent, critical for document classification
2. **REGULATORY_DOCUMENT** - Essential for compliance tracking
3. **TECHNICAL_SYSTEM** - Core domain terminology
4. **DATE_RU** - Critical for validity periods and timelines
5. **ORGANIZATION_RU** - Important for document provenance

---

## Pattern Recommendations from LLM

### STANDARD_REFERENCE Patterns
```regex
^ГОСТ\s[Р]\s\d{4}-\d{4}$
^\w+\s\d{4}-\d{4}$
```

### REGULATORY_DOCUMENT Patterns
```regex
^Федеральный\sзакон\s№\s\d+-\d+$
^Приказ\s№\s\d+-\d+$
```

### DATE_RU Patterns
```regex
^\d{1,2}\s[А-Я]{3}\s\d{4}$
^\d{1,2}\.\d{1,2}\.\d{4}$
```

### ORGANIZATION_RU Patterns
```regex
^Федеральное\s[А-Я]+$
^([А-Я]+\s){2,}[А-Я]+$
```

---

## Key Observations

1. **Structured Numbering**: Documents consistently use numerical identifiers for standards and regulatory documents

2. **Date Format**: Russian dates follow specific month-year patterns (e.g., "27 декабря 2006")

3. **Organization Naming**: Government bodies frequently include "Россия", "агентство", "Федеральное" in names

4. **Technical Terms**: Cryptographic terms are often combined with technical processes

5. **Document Structure**: Strict hierarchical structure with standardized section numbering

---

## Files Generated

| File | Purpose |
|------|---------|
| `pdf_samples.json` | Raw text samples from PDFs |
| `entity_discovery_results.json` | Full LLM analysis results |
| `ENTITY_DISCOVERY_ANALYSIS.md` | This summary document |

---

## Next Steps

1. Update `custom_entity_types.py` with LLM-recommended patterns
2. Test new entity types on sample documents
3. Measure precision/recall improvements
4. Iterate based on results

---

## Prompt Used

The entity discovery prompt is stored at:
`mcp_nlp_server/nlp_tools/prompts/entity_discovery_prompt.txt`

This prompt can be reused for analyzing additional documents in the future.
