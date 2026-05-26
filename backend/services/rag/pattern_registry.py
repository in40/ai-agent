"""
Pattern Registry for Dynamic Entity Extraction Patterns

This module manages regex patterns discovered through LLM extraction.
Patterns are stored in JSON and compiled at runtime for fast entity extraction.
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Pattern registry file path
PATTERN_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), 'entity_patterns.json')


class PatternRegistry:
    """
    Manages regex patterns for entity extraction.
    
    Patterns are discovered through LLM analysis of documents and stored
    for fast regex-based extraction on future documents.
    """
    
    def __init__(self, registry_path: str = None):
        """
        Initialize pattern registry.
        
        Args:
            registry_path: Path to patterns JSON file (default: same directory)
        """
        self.registry_path = registry_path or PATTERN_REGISTRY_PATH
        self.patterns = self._load_patterns()
        self._compiled_cache: Dict[str, List[Dict]] = {}
    
    def _load_patterns(self) -> Dict[str, List[Dict]]:
        """Load patterns from JSON file or create default structure"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} pattern categories from registry")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load pattern registry: {e}. Using defaults.")
        
        # Default empty structure
        default_patterns = {
            'standards': [],        # ГОСТ, ISO, etc.
            'organizations': [],    # ТК, committees, agencies
            'abbreviations': [],    # Abbreviation → full name mappings
            'technical_terms': [],  # Domain-specific technical terms
            'concepts': []          # General concepts
        }
        
        # Save default patterns
        self._save_patterns(default_patterns)
        return default_patterns
    
    def _save_patterns(self, patterns: Dict[str, List[Dict]] = None):
        """Save patterns to JSON file"""
        patterns = patterns or self.patterns
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(patterns, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(patterns)} pattern categories to registry")
        except IOError as e:
            logger.error(f"Failed to save pattern registry: {e}")
    
    def add_pattern(self, category: str, pattern: str, example: str, 
                    description: str, metadata: Dict[str, Any] = None):
        """
        Add new discovered pattern to registry.
        
        Args:
            category: Pattern category (standards, organizations, etc.)
            pattern: Regex pattern string
            example: Example text that matches this pattern
            description: Human-readable description
            metadata: Additional metadata (optional)
        """
        if category not in self.patterns:
            self.patterns[category] = []
        
        # Check if pattern already exists
        for existing in self.patterns[category]:
            if existing['pattern'] == pattern:
                logger.info(f"Pattern already exists in {category}: {pattern}")
                return
        
        pattern_entry = {
            'pattern': pattern,
            'example': example,
            'description': description,
            'discovered_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.patterns[category].append(pattern_entry)
        self._compiled_cache.clear()  # Clear cache to force recompilation
        self._save_patterns()
        
        logger.info(f"Added pattern to {category}: {pattern[:50]}...")
    
    def remove_pattern(self, category: str, pattern: str):
        """Remove pattern from registry"""
        if category in self.patterns:
            self.patterns[category] = [
                p for p in self.patterns[category] 
                if p['pattern'] != pattern
            ]
            self._compiled_cache.clear()
            self._save_patterns()
    
    def get_compiled_patterns(self) -> Dict[str, List[Dict]]:
        """
        Get all patterns with compiled regex objects.
        
        Returns:
            Dict mapping category names to list of pattern dicts with 'regex' key
        """
        if not self._compiled_cache:
            self._compiled_cache = {}
            
            for category, pattern_list in self.patterns.items():
                self._compiled_cache[category] = []
                
                for p in pattern_list:
                    try:
                        compiled_regex = re.compile(p['pattern'], re.IGNORECASE)
                        self._compiled_cache[category].append({
                            'regex': compiled_regex,
                            'pattern': p['pattern'],
                            'example': p['example'],
                            'description': p['description'],
                            'discovered_at': p.get('discovered_at', '')
                        })
                    except re.error as e:
                        logger.warning(f"Invalid regex in {category}: {p['pattern']} - {e}")
        
        return self._compiled_cache
    
    def extract_entities_from_text(self, text: str) -> List[Dict]:
        """
        Extract entities from text using all registered patterns.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entity dicts with name, type, and source info
        """
        entities = []
        patterns = self.get_compiled_patterns()
        
        # Standards
        for p in patterns.get('standards', []):
            for match in p['regex'].finditer(text):
                entities.append({
                    'name': match.group(0),
                    'type': 'STANDARD',
                    'source': f"regex:{p['example']}",
                    'match_text': match.group(0)
                })
        
        # Organizations
        for p in patterns.get('organizations', []):
            for match in p['regex'].finditer(text):
                entities.append({
                    'name': match.group(0),
                    'type': 'ORGANIZATION',
                    'source': f"regex:{p['example']}",
                    'match_text': match.group(0)
                })
        
        # Abbreviations (may have synonyms)
        for p in patterns.get('abbreviations', []):
            for match in p['regex'].finditer(text):
                # Handle patterns with capture groups for abbreviations
                if match.lastindex and match.lastindex >= 1:
                    abbreviation = match.group(1)
                    full_form = match.group(0)
                else:
                    abbreviation = match.group(0)
                    full_form = match.group(0)
                
                entities.append({
                    'name': abbreviation,
                    'type': 'ABBREVIATION',
                    'synonyms': [full_form] if full_form != abbreviation else [],
                    'source': f"regex:{p['example']}",
                    'match_text': match.group(0)
                })
        
        # Technical terms
        for p in patterns.get('technical_terms', []):
            for match in p['regex'].finditer(text):
                entities.append({
                    'name': match.group(0),
                    'type': 'TECHNICAL_TERM',
                    'source': f"regex:{p['example']}",
                    'match_text': match.group(0)
                })
        
        # Concepts
        for p in patterns.get('concepts', []):
            for match in p['regex'].finditer(text):
                entities.append({
                    'name': match.group(0),
                    'type': 'CONCEPT',
                    'source': f"regex:{p['example']}",
                    'match_text': match.group(0)
                })
        
        # Remove duplicates (same name + type)
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity['name'], entity['type'])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about patterns in registry"""
        stats = {
            'total_categories': len(self.patterns),
            'categories': {}
        }
        
        for category, pattern_list in self.patterns.items():
            stats['categories'][category] = {
                'count': len(pattern_list),
                'patterns': [p['pattern'] for p in pattern_list]
            }
        
        return stats
    
    def export_patterns(self) -> str:
        """Export all patterns as JSON string"""
        return json.dumps(self.patterns, ensure_ascii=False, indent=2)
    
    def import_patterns(self, json_string: str):
        """Import patterns from JSON string"""
        try:
            imported = json.loads(json_string)
            self.patterns.update(imported)
            self._compiled_cache.clear()
            self._save_patterns()
            logger.info(f"Imported patterns from JSON")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to import patterns: {e}")


# Global instance
pattern_registry = PatternRegistry()


def get_pattern_registry() -> PatternRegistry:
    """Get or create global pattern registry instance"""
    return pattern_registry


if __name__ == '__main__':
    # Test the pattern registry
    logging.basicConfig(level=logging.INFO)
    
    registry = PatternRegistry()
    
    # Add some test patterns
    registry.add_pattern(
        category='organizations',
        pattern=r'(ТК|Технический комитет)\s*\d+',
        example='ТК 26',
        description='Technical Committee with number'
    )
    
    registry.add_pattern(
        category='abbreviations',
        pattern=r'(ТК\s*(\d+))|(Технический комитет\s*\2)',
        example='ТК 26 ↔ Технический комитет 26',
        description='Abbreviation and full form'
    )
    
    # Test extraction
    test_text = "Разработаны подкомитетом ТК 26 Технического комитета по стандартизации"
    entities = registry.extract_entities_from_text(test_text)
    
    print(f"\nExtracted {len(entities)} entities:")
    for entity in entities:
        print(f"  - {entity['name']} ({entity['type']})")
    
    # Show statistics
    stats = registry.get_statistics()
    print(f"\nPattern Statistics:")
    for category, info in stats['categories'].items():
        print(f"  {category}: {info['count']} patterns")
