"""
NLP Entity Extraction Tools
Provides entity extraction functionality using multiple NLP libraries
"""
import spacy
import nltk
from typing import Dict, List, Any, Optional
from collections import Counter
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('maxent_ne_chunker')
    nltk.data.find('words')
except LookupError:
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)


class EntityExtractor:
    """
    Multi-library entity extraction supporting spaCy (English + Russian), NLTK, pattern-based extraction, and custom entity types
    """
    
    # Standard entity types based on industry standards
    ENTITY_TYPES = {
        # Generic (spaCy/NLTK standard)
        "PERSON": "People, including fictional",
        "ORG": "Companies, agencies, institutions",
        "GPE": "Countries, cities, states (Geo-Political Entity)",
        "LOC": "Non-GPE locations",
        "DATE": "Absolute or relative dates or periods",
        "TIME": "Times smaller than a day",
        "PERCENT": "Percentage (e.g., 'twenty percent')",
        "MONEY": "Monetary values",
        "QUANTITY": "Measurements (weight, distance)",
        "CARDINAL": "Numerals that do not fall under another type",
        "ORDINAL": "Ordinal numbers (first, second, etc.)",
        
        # Domain-specific for Technical Standards
        "STANDARD": "Technical standards (GOST, ISO, IEC, RFC)",
        "TECHNOLOGY": "Technical terms, algorithms, protocols",
        "CONCEPT": "Domain-specific concepts",
        "LAW": "Laws, regulations, policies",
        "PRODUCT": "Products, services, software",
        "EVENT": "Named events, conferences, incidents",
        "WORK_OF_ART": "Titles of books, songs, etc.",
        "LANGUAGE": "Named languages",
        "NORP": "Nationalities, religious or political groups"
    }
    
    def __init__(self, model_name: str = "en_core_web_sm", russian_model: str = "ru_core_news_sm", use_custom_types: bool = True):
        """
        Initialize entity extractor with specified models
        
        Args:
            model_name: spaCy English model to use (default: en_core_web_sm)
            russian_model: spaCy Russian model to use (default: ru_core_news_sm)
            use_custom_types: Enable custom entity types (default: True)
        """
        self.model_name = model_name
        self.russian_model = russian_model
        self.use_custom_types = use_custom_types
        self.nlp_en = None
        self.nlp_ru = None
        self.ruler = None  # EntityRuler for custom patterns
        self._load_spacy_models()
        
        # Add custom entity types if enabled
        if self.use_custom_types:
            self._add_custom_entity_types()
        
    def _load_spacy_models(self):
        """Load spaCy English and Russian models"""
        # Load English model
        try:
            self.nlp_en = spacy.load(self.model_name)
            print(f"Loaded spaCy English model: {self.model_name}")
        except OSError:
            print(f"Model {self.model_name} not found. Please install it:")
            print(f"  python -m spacy download {self.model_name}")
            self.nlp_en = None
        
        # Load Russian model
        try:
            self.nlp_ru = spacy.load(self.russian_model)
            print(f"Loaded spaCy Russian model: {self.russian_model}")
        except OSError:
            print(f"Model {self.russian_model} not found. Please install it:")
            print(f"  python -m spacy download {self.russian_model}")
            self.nlp_ru = None
    
    def _add_custom_entity_types(self):
        """Add custom entity types using spaCy's EntityRuler"""
        try:
            from .custom_entity_types import get_custom_patterns, CUSTOM_ENTITY_TYPES
            
            # Add custom types to ENTITY_TYPES dict
            self.ENTITY_TYPES.update(CUSTOM_ENTITY_TYPES)
            
            # Create EntityRuler for Russian model
            if self.nlp_ru:
                # Add EntityRuler before NER component
                if "entity_ruler" not in self.nlp_ru.pipe_names:
                    ruler = self.nlp_ru.add_pipe("entity_ruler", before="ner")
                    patterns = get_custom_patterns()
                    ruler.add_patterns(patterns)
                    self.ruler = ruler
                    print(f"Added {len(patterns)} custom entity patterns to Russian model")
            
            # Create EntityRuler for English model
            if self.nlp_en:
                if "entity_ruler" not in self.nlp_en.pipe_names:
                    ruler_en = self.nlp_en.add_pipe("entity_ruler", before="ner")
                    patterns = get_custom_patterns()
                    ruler_en.add_patterns(patterns)
                    print(f"Added {len(patterns)} custom entity patterns to English model")
            
            print(f"Loaded {len(CUSTOM_ENTITY_TYPES)} custom entity types")
            
        except ImportError as e:
            print(f"Warning: Could not load custom entity types: {e}")
        except Exception as e:
            print(f"Warning: Error adding custom entity types: {e}")
    
    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on Cyrillic characters
        
        Args:
            text: Input text
            
        Returns:
            'ru' if Russian detected, 'en' otherwise
        """
        # Count Cyrillic characters
        cyrillic_count = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        total_chars = len(text.replace(' ', ''))
        
        # If more than 30% Cyrillic, consider it Russian
        if total_chars > 0 and (cyrillic_count / total_chars) > 0.3:
            return 'ru'
        return 'en'
    
    def extract_entities_spacy(self, text: str, auto_detect_language: bool = True) -> List[Dict[str, Any]]:
        """
        Extract entities using spaCy (English or Russian model)
        
        Args:
            text: Input text
            auto_detect_language: Automatically detect language (default: True)
            
        Returns:
            List of entity dictionaries with text, label, start, end, confidence
        """
        entities = []
        
        # Determine which model to use
        if auto_detect_language:
            lang = self._detect_language(text)
            nlp = self.nlp_ru if lang == 'ru' and self.nlp_ru else self.nlp_en
            print(f"Auto-detected language: {'Russian' if lang == 'ru' else 'English'}")
        else:
            nlp = self.nlp_en  # Default to English
        
        if not nlp:
            print("No spaCy model loaded")
            return []
        
        doc = nlp(text)
        
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "label_description": self.ENTITY_TYPES.get(ent.label_, "Unknown"),
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.9,  # spaCy doesn't provide confidence scores
                "language": "ru" if nlp == self.nlp_ru else "en"
            })
        
        return entities
    
    def extract_entities_nltk(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities using NLTK
        
        Args:
            text: Input text
            
        Returns:
            List of entity dictionaries
        """
        try:
            # Tokenize and POS tag
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            
            # Named entity chunking
            ne_chunks = nltk.ne_chunk(pos_tags)
            
            entities = []
            current_entity = []
            current_label = None
            
            for chunk in ne_chunks:
                if hasattr(chunk, 'label'):
                    if current_label and current_entity:
                        entities.append({
                            "text": " ".join(current_entity),
                            "label": current_label,
                            "label_description": self.ENTITY_TYPES.get(current_label, "Unknown"),
                            "start": text.find(" ".join(current_entity)),
                            "end": text.find(" ".join(current_entity)) + len(" ".join(current_entity)),
                            "confidence": 0.8
                        })
                    current_label = chunk.label()
                    current_entity = [leaf[0] for leaf in chunk.leaves()]
                else:
                    if current_label and current_entity:
                        entities.append({
                            "text": " ".join(current_entity),
                            "label": current_label,
                            "label_description": self.ENTITY_TYPES.get(current_label, "Unknown"),
                            "start": text.find(" ".join(current_entity)),
                            "end": text.find(" ".join(current_entity)) + len(" ".join(current_entity)),
                            "confidence": 0.8
                        })
                    current_label = None
                    current_entity = []
            
            return entities
        except Exception as e:
            print(f"NLTK entity extraction error: {e}")
            return []
    
    def extract_standards_pattern(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract technical standards using regex patterns
        
        Args:
            text: Input text
            
        Returns:
            List of standard entities
        """
        patterns = {
            # GOST formats (including split across lines)
            "GOST_R": r'ГОСТ\s*Р\s*\d+\s*[-–—]\s*\d{4}',
            "GOST_R_ALT": r'ГОСТ\s*\d+\s*[-–—]\s*\d{4}',
            "GOST": r'GOST\s*R?\s*\d+\s*[-–—]\s*\d{4}',
            # ISO formats
            "ISO": r'ISO\s*\d+(-\d+)?',
            # IEC formats
            "IEC": r'IEC\s*\d+(-\d+)?',
            # RFC formats
            "RFC": r'RFC\s*\d+',
            # NIST formats
            "NIST": r'NIST\s*(SP|FIPS)\s*\d+(-\d+)?',
            # Generic standard with year
            "STANDARD_YEAR": r'\d{4,5}\s*[-–—]\s*\d{4}',
        }
        
        entities = []
        for std_type, pattern in patterns.items():
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                entities.append({
                    "text": match.group(),
                    "label": "STANDARD",
                    "label_description": f"{std_type} Standard",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.95,
                    "standard_type": std_type
                })
        
        return entities
    
    def extract_technologies(self, text: str, custom_terms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract technical terms and technologies
        
        Args:
            text: Input text
            custom_terms: Optional list of custom technical terms
            
        Returns:
            List of technology entities
        """
        # Common cryptography and security terms
        default_terms = [
            "elliptic curve cryptography", "digital signature", "hash function",
            "encryption", "decryption", "public key", "private key",
            "symmetric encryption", "asymmetric encryption", "block cipher",
            "stream cipher", "authentication", "authorization", "integrity",
            "non-repudiation", "key exchange", "certificate", "PKI",
            "SHA-256", "SHA-512", "AES", "RSA", "ECDSA", "EdDSA"
        ]
        
        terms = custom_terms if custom_terms else default_terms
        
        entities = []
        text_lower = text.lower()
        
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(text):
                entities.append({
                    "text": match.group(),
                    "label": "TECHNOLOGY",
                    "label_description": "Technical term or technology",
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.85
                })
        
        return entities
    
    def extract_all_entities(self, text: str, use_spacy: bool = True, 
                            use_nltk: bool = False, use_patterns: bool = True,
                            extract_technologies: bool = True) -> List[Dict[str, Any]]:
        """
        Extract all entities using multiple methods
        
        Args:
            text: Input text
            use_spacy: Use spaCy for NER
            use_nltk: Use NLTK for NER
            use_patterns: Use regex patterns for standards
            extract_technologies: Extract technical terms

        Returns:
            Combined list of all entities (deduplicated)
        """
        all_entities = []

        if use_spacy and (self.nlp_en or self.nlp_ru):
            all_entities.extend(self.extract_entities_spacy(text))

        if use_nltk:
            all_entities.extend(self.extract_entities_nltk(text))

        if use_patterns:
            all_entities.extend(self.extract_standards_pattern(text))

        if extract_technologies:
            all_entities.extend(self.extract_technologies(text))
        
        # Deduplicate entities (same text and label)
        seen = set()
        unique_entities = []
        for entity in all_entities:
            key = (entity["text"], entity["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        # Sort by position in text
        unique_entities.sort(key=lambda x: x["start"])
        
        return unique_entities
    
    def get_entity_statistics(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about extracted entities
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with entity statistics
        """
        label_counts = Counter([e["label"] for e in entities])
        
        return {
            "total_entities": len(entities),
            "by_label": dict(label_counts),
            "unique_labels": len(label_counts),
            "entity_types_found": list(label_counts.keys())
        }
    
    def filter_entities_by_type(self, entities: List[Dict[str, Any]], 
                                entity_types: List[str]) -> List[Dict[str, Any]]:
        """
        Filter entities by type
        
        Args:
            entities: List of entities
            entity_types: List of entity types to keep
            
        Returns:
            Filtered list of entities
        """
        return [e for e in entities if e["label"] in entity_types]
    
    def analyze_document(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive document analysis
        
        Args:
            text: Document text
            
        Returns:
            Analysis results with entities and statistics
        """
        entities = self.extract_all_entities(text)
        stats = self.get_entity_statistics(entities)
        
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            label = entity["label"]
            if label not in entities_by_type:
                entities_by_type[label] = []
            entities_by_type[label].append(entity)
        
        return {
            "text_length": len(text),
            "entities": entities,
            "statistics": stats,
            "entities_by_type": entities_by_type,
            "entity_types_available": list(self.ENTITY_TYPES.keys())
        }


# Singleton instance for reuse
_extractor_instance: Optional[EntityExtractor] = None

def get_entity_extractor(model_name: str = "en_core_web_sm") -> EntityExtractor:
    """Get or create entity extractor instance"""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = EntityExtractor(model_name)
    return _extractor_instance
