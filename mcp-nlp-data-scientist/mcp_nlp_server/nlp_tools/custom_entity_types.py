"""
Custom Entity Types Configuration
Define your own entity types for domain-specific extraction
"""

# Custom entity patterns for Russian technical standards
CUSTOM_ENTITY_PATTERNS = {
    # GOST-specific entity types
    "GOST_STANDARD": {
        "patterns": [
            [{"TEXT": {"REGEX": r"ГОСТ\s*[Рр]?\s*\d+[\s\-–—]+\d{4}"}}],
            [{"TEXT": {"REGEX": r"GOST\s*[Rr]?\s*\d+[\s\-–—]+\d{4}"}}],
        ],
        "description": "GOST standards (Russian national standards)"
    },
    
    "REGULATORY_DOC": {
        "patterns": [
            [{"TEXT": "Федеральный"}, {"TEXT": "закон"}, {"TEXT": {"REGEX": r"№\s*\d+-\w+"}}],
            [{"TEXT": "Постановление"}, {"TEXT": {"REGEX": r"№\s*\d+"}}],
            [{"TEXT": "Приказ"}, {"TEXT": {"REGEX": r"№\s*\d+"}}],
        ],
        "description": "Regulatory documents (laws, decrees, orders)"
    },
    
    "TECHNICAL_TERM": {
        "patterns": [
            [{"TEXT": {"REGEX": r"(криптографическ|шифрован|дешифрован|хэш)[а-яё]*"}}],
            [{"TEXT": {"REGEX": r"(электронн|цифров)[а-яё]*\s+(подпис|печат)"}},],
            [{"TEXT": {"REGEX": r"(ключ|сертификат)\s+(проверк|подпис)"}},],
        ],
        "description": "Technical terms specific to cryptography and security"
    },
    
    "ORGANIZATION_RU": {
        "patterns": [
            [{"TEXT": {"REGEX": r"Федеральн[ао]я?\s+агентств[оа]"}},],
            [{"TEXT": {"REGEX": r"Министерств[оа]\s+"}},],
            [{"TEXT": {"REGEX": r"Федеральн[ао]я?\s+служб[аы]"}},],
        ],
        "description": "Russian government organizations"
    },
    
    "DOCUMENT_SECTION": {
        "patterns": [
            [{"TEXT": {"REGEX": r"Раздел\s+\d+"}},],
            [{"TEXT": {"REGEX": r"Приложени[ея]\s+[А-Я]"}},],
            [{"TEXT": {"REGEX": r"Пункт\s+\d+"}},],
            [{"TEXT": {"REGEX": r"Стать[яю]\s+\d+"}},],
        ],
        "description": "Document sections, appendices, articles"
    },
    
    "DATE_RU": {
        "patterns": [
            [{"TEXT": {"REGEX": r"\d{1,2}\s+(январ[яь]|феврал[яь]|март[ау]|апрел[яь]|ма[яь]|июн[яь]|июл[яь]|август[ау]|сентябр[яь]|октябр[яь]|ноябр[яь]|декабр[яь])\s+\d{4}"}}],
        ],
        "description": "Russian format dates"
    },
    
    "MEASUREMENT": {
        "patterns": [
            [{"TEXT": {"REGEX": r"\d+[\s,\.]?\d*\s*(бит|байт|КБ|МБ|ГБ|ТБ|секунд|минут|час)"}},],
        ],
        "description": "Measurements and units"
    },
    
    "SOFTWARE_PRODUCT": {
        "patterns": [
            [{"TEXT": {"REGEX": r"[A-Z][a-zA-Z0-9_-]+\s+(систем|программ|приложен|сервис)"}},],
            [{"TEXT": {"REGEX": r"СКЗИ"}}],  # Средства криптографической защиты информации
        ],
        "description": "Software products and systems"
    }
}

# Custom entity types to add to the standard spaCy types
CUSTOM_ENTITY_TYPES = {
    "GOST_STANDARD": "GOST standards (Russian national standards)",
    "REGULATORY_DOC": "Regulatory documents (laws, decrees, orders)",
    "TECHNICAL_TERM": "Technical terms (cryptography, security)",
    "ORGANIZATION_RU": "Russian government organizations",
    "DOCUMENT_SECTION": "Document sections, appendices, articles",
    "DATE_RU": "Russian format dates",
    "MEASUREMENT": "Measurements and units",
    "SOFTWARE_PRODUCT": "Software products and systems"
}


def get_custom_patterns():
    """Get all custom patterns for EntityRuler"""
    patterns = []
    
    for entity_type, config in CUSTOM_ENTITY_PATTERNS.items():
        for pattern in config["patterns"]:
            patterns.append({
                "label": entity_type,
                "pattern": pattern
            })
    
    return patterns


def add_custom_entity_types_to_extractor(extractor):
    """
    Add custom entity types to an EntityExtractor instance
    
    Args:
        extractor: EntityExtractor instance to modify
    """
    # Add custom types to ENTITY_TYPES
    extractor.ENTITY_TYPES.update(CUSTOM_ENTITY_TYPES)
    
    print(f"Added {len(CUSTOM_ENTITY_TYPES)} custom entity types:")
    for entity_type, description in CUSTOM_ENTITY_TYPES.items():
        print(f"  - {entity_type}: {description}")


# Example usage and testing
if __name__ == "__main__":
    print("Custom Entity Types Configuration")
    print("=" * 60)
    print()
    print("Available custom entity types:")
    for entity_type, description in CUSTOM_ENTITY_TYPES.items():
        print(f"\n{entity_type}:")
        print(f"  Description: {description}")
        if entity_type in CUSTOM_ENTITY_PATTERNS:
            print(f"  Patterns: {len(CUSTOM_ENTITY_PATTERNS[entity_type]['patterns'])} patterns defined")
