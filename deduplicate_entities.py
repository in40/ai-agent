#!/usr/bin/env python3
"""
Entity Deduplication for GOST Documents

Merges duplicate/variant entity names into canonical forms.
Examples:
  "ФСТЭК" + "ФСТЭК России" → "ФСТЭК России"
  "ГОСТ Р 52633-2014" + "ГОСТ Р 52633—2014" → "ГОСТ Р 52633-2014"

Usage:
    python deduplicate_entities.py [--threshold 0.8] [--review-only] [--output-dir OUTPUT_DIR]
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import re

# Try to import fuzzy matching libraries
try:
    from difflib import SequenceMatcher
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False
    print("Warning: difflib not available, using simple string matching")

# Configuration
DEFAULT_THRESHOLD = 0.85  # Similarity threshold for merging
MIN_LENGTH_DIFF = 3  # Minimum character difference to consider as variant


class EntityDeduplicator:
    """Deduplicate entities using fuzzy matching and domain rules"""
    
    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold
        self.merges = {}  # variant → canonical
        self.canonical_forms = {}  # canonical name → entity data
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        if not name:
            return ""
        
        # Lowercase and strip
        normalized = name.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove common punctuation variations
        normalized = normalized.replace('—', '-').replace('–', '-')
        
        return normalized
    
    def similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity between two entity names"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        if HAS_FUZZY:
            ratio = SequenceMatcher(None, norm1, norm2).ratio()
            
            # Boost score if one is substring of another
            if norm1 in norm2 or norm2 in norm1:
                ratio = max(ratio, 0.85)
            
            return ratio
        else:
            # Simple fallback: check if one contains the other
            if norm1 in norm2 or norm2 in norm1:
                return 0.85
            return 0.0
    
    def is_variant(self, name1: str, name2: str) -> bool:
        """Check if name1 is a variant of name2 (shorter form)"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        # Check if one is substring of another
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check common abbreviation patterns
        abbreviations = {
            'фстэк': ['фстэк россии', 'федеральная служба по техническому и экспортному контролю'],
            'гост': ['гост р', 'государственный стандарт'],
            'фса': ['федеральное агентство'],
            'гниии': ['государственный научно-исследовательский испытательный институт'],
        }
        
        for abbrev, full_forms in abbreviations.items():
            if abbrev in norm1 and any(f in norm2 for f in full_forms):
                return True
            if abbrev in norm2 and any(f in norm1 for f in full_forms):
                return True
        
        return False
    
    def find_canonical(self, name: str, candidates: List[str]) -> str:
        """Find the best canonical name from candidates"""
        if not candidates:
            return name
        
        # Prefer longer, more complete names
        # Sort by length (descending) and pick longest
        sorted_candidates = sorted(candidates, key=len, reverse=True)
        
        # Return longest one that's similar enough
        for candidate in sorted_candidates:
            if self.similarity_score(name, candidate) >= self.threshold:
                return candidate
        
        return sorted_candidates[0] if sorted_candidates else name
    
    def group_similar_entities(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar entities together"""
        groups = defaultdict(list)
        
        # Sort entities by name length (longest first)
        sorted_entities = sorted(entities, key=lambda e: len(e.get('text', '')), reverse=True)
        
        for entity in sorted_entities:
            name = entity.get('text', '')
            if not name:
                continue
            
            # Find existing group or create new one
            found_group = None
            for canonical_name, group in groups.items():
                if self.similarity_score(name, canonical_name) >= self.threshold:
                    found_group = canonical_name
                    break
            
            if found_group:
                groups[found_group].append(entity)
            else:
                groups[name].append(entity)
        
        return groups
    
    def deduplicate(self, entities: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Deduplicate entities and return merged list with statistics
        
        Returns:
            Tuple of (merged_entities, dedup_stats)
        """
        print(f"\nDeduplicating {len(entities)} entities...")
        
        # Group similar entities
        groups = self.group_similar_entities(entities)
        
        print(f"  Found {len(groups)} unique entity groups")
        
        merged_entities = []
        stats = {
            'total_before': len(entities),
            'total_after': 0,
            'merged_count': 0,
            'groups': []
        }
        
        for canonical_name, group in groups.items():
            if len(group) == 1:
                # No merging needed
                merged_entities.append(group[0])
                stats['total_after'] += 1
            else:
                # Merge multiple variants
                merged = self._merge_group(canonical_name, group)
                merged_entities.append(merged)
                stats['total_after'] += 1
                stats['merged_count'] += len(group) - 1
                
                # Record merge details
                stats['groups'].append({
                    'canonical': canonical_name,
                    'variants': [e.get('text', '') for e in group if e.get('text', '') != canonical_name],
                    'count': len(group)
                })
        
        print(f"  Merged {stats['merged_count']} duplicates into {stats['total_after']} unique entities")
        
        return merged_entities, stats
    
    def _merge_group(self, canonical_name: str, group: List[Dict]) -> Dict:
        """Merge a group of similar entities into one"""
        
        # Use the longest/most complete name as canonical
        merged = {
            'text': canonical_name,
            'type': group[0].get('type', 'UNKNOWN'),
            'source': 'merged',
            'confidence': max(e.get('confidence', 0.5) for e in group),
            'aliases': list(set(e.get('text', '') for e in group if e.get('text', '') != canonical_name)),
            'doc_names': list(set(
                e.get('doc', e.get('doc_name', '')) 
                for e in group 
                if e.get('doc', e.get('doc_name', ''))
            )),
            'merge_count': len(group)
        }
        
        return merged
    
    def find_specific_duplicates(self, entities: List[Dict], search_terms: List[str]) -> List[Dict]:
        """Find specific duplicates for given search terms"""
        results = []
        
        for term in search_terms:
            matches = []
            for entity in entities:
                name = entity.get('text', '')
                if self.similarity_score(term, name) >= 0.7:
                    matches.append({
                        'name': name,
                        'type': entity.get('type', ''),
                        'similarity': self.similarity_score(term, name)
                    })
            
            if matches:
                results.append({
                    'search_term': term,
                    'matches': sorted(matches, key=lambda x: -x['similarity'])
                })
        
        return results


def load_entities(file_path: str) -> List[Dict]:
    """Load entities from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('entities', [])


def save_entities(entities: List[Dict], output_path: str):
    """Save deduplicated entities to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total': len(entities),
            'entities': entities
        }, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Deduplicate GOST entities')
    parser.add_argument('--input', default='/root/qwen/ai_agent/extraction_results_final/all_entities.json',
                       help='Input entities JSON file')
    parser.add_argument('--output-dir', default='/root/qwen/ai_agent/deduplicated_entities',
                       help='Output directory')
    parser.add_argument('--threshold', type=float, default=0.85,
                       help='Similarity threshold (default: 0.85)')
    parser.add_argument('--review-only', action='store_true',
                       help='Only show duplicates, do not merge')
    parser.add_argument('--search', nargs='+',
                       help='Search for specific entity duplicates (e.g., --search "ФСТЭК" "ГОСТ")')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ENTITY DEDUPLICATION")
    print("=" * 80)
    
    # Load entities
    print(f"\nLoading entities from {args.input}...")
    entities = load_entities(args.input)
    print(f"  Loaded {len(entities)} entities")
    
    # Create deduplicator
    deduplicator = EntityDeduplicator(threshold=args.threshold)
    
    # Search for specific duplicates if requested
    if args.search:
        print(f"\nSearching for duplicates of: {args.search}")
        search_results = deduplicator.find_specific_duplicates(entities, args.search)
        
        for result in search_results:
            print(f"\n  '{result['search_term']}':")
            for match in result['matches'][:10]:
                print(f"    - {match['name']} (similarity: {match['similarity']:.2f})")
        
        return
    
    # Perform deduplication
    if args.review_only:
        print("\n[REVIEW MODE] Showing duplicate groups...")
        groups = deduplicator.group_similar_entities(entities)
        
        duplicate_groups = [(name, group) for name, group in groups.items() if len(group) > 1]
        duplicate_groups.sort(key=lambda x: -len(x[1]))
        
        print(f"\nFound {len(duplicate_groups)} groups with duplicates:")
        for i, (canonical, group) in enumerate(duplicate_groups[:20], 1):
            print(f"\n{i}. Canonical: {canonical}")
            print(f"   Variants ({len(group)} total):")
            for entity in group:
                print(f"     - {entity.get('text', '')} (type: {entity.get('type', '')})")
    else:
        # Actually deduplicate
        merged_entities, stats = deduplicator.deduplicate(entities)
        
        # Create output directory
        Path(args.output_dir).mkdir(exist_ok=True)
        
        # Save deduplicated entities
        output_file = Path(args.output_dir) / "all_entities_deduplicated.json"
        save_entities(merged_entities, str(output_file))
        print(f"\n  Saved deduplicated entities to {output_file}")
        
        # Save merge statistics
        stats_file = Path(args.output_dir) / "deduplication_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"  Saved statistics to {stats_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("DEDUPLICATION COMPLETE")
        print("=" * 80)
        print(f"\nBefore: {stats['total_before']} entities")
        print(f"After:  {stats['total_after']} entities")
        print(f"Merged: {stats['merged_count']} duplicates")
        print(f"Reduction: {(1 - stats['total_after']/stats['total_before'])*100:.1f}%")
        
        # Show top merged groups
        if stats['groups']:
            print("\nTop merged groups:")
            for group in sorted(stats['groups'], key=lambda x: -x['count'])[:10]:
                print(f"\n  {group['canonical']}")
                print(f"    Variants: {', '.join(group['variants'][:5])}")
                if len(group['variants']) > 5:
                    print(f"    ... and {len(group['variants']) - 5} more")


if __name__ == "__main__":
    main()
