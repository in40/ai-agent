#!/usr/bin/env python3
"""
Entity Deduplication for GOST Documents - CONSERVATIVE APPROACH

Only merges TRUE variants (abbreviations, typos) - NEVER different entities.
Rules:
- "ФСТЭК" + "ФСТЭК России" → "ФСТЭК России" ✓
- "ГОСТ Р 34.11-2012" + "ГОСТ Р 34.12-2015" → NO MERGE ✓
- "Стандартинформ" + "Москва Стандартинформ 2018" → NO MERGE ✓
- "29 июня 2015 г." + "№ 162-ФЗ" → NO MERGE ✓

Usage:
    python deduplicate_entities_strict.py [--threshold 0.9] [--review-only]
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


class StrictEntityDeduplicator:
    """Strict entity deduplication - only merge true variants"""
    
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self.merges = {}
        
        # Patterns that should NEVER be merged (different entities)
        self.no_merge_patterns = [
            # Different GOST standards
            r'ГОСТ\s+R?\s*\d+\.\d+',  # GOST numbers
            r'ГОСТ\s+Р\s*\d+',         # GOST R numbers
            # Different law numbers
            r'№\s*\d+-\w+',            # Law numbers like № 162-ФЗ
            r'\d{4}-\d{2}-\d{2}',      # Dates in ISO format
            r'\d+\s*июнь[аыя]*\s*\d+', # Dates like "29 июня 2015"
            # Different years
            r'\b(20\d{2}|19\d{2})\b',  # Years
        ]
        
        # Abbreviation patterns - these CAN be merged
        self.abbreviation_rules = {
            'фстэк': ['фстэк россии', 'федеральная служба по техническому и экспортному контролю'],
            'гост': ['гост р', 'государственный стандарт'],
            'ооо': ['общество с ограниченной ответственностью'],
            'ао': ['акционерное общество', 'открытый акционерное общество'],
            'зao': ['закрытый акционерное общество'],
            'тк': ['технический комитет'],
            'гос': ['государственный'],
            'фгбу': ['федеральное государственное бюджетное учреждение'],
            'фгу': ['федеральное государственное учреждение'],
            'фгуп': ['федеральное государственное унитарное предприятие'],
        }
    
    def extract_entity_type(self, name: str) -> str:
        """Determine entity type for stricter matching"""
        name_lower = name.lower()
        
        if re.search(r'гост\s+r?\s*\d+', name_lower):
            return 'STANDARD'
        elif re.search(r'№\s*\d+-\w+', name_lower):
            return 'LAW_NUMBER'
        elif re.search(r'\d+\s*июнь[аыя]*', name_lower) or re.search(r'\d{4}-\d{2}-\d{2}', name_lower):
            return 'DATE'
        elif re.search(r'\b(20\d{2}|19\d{2})\b', name_lower):
            return 'YEAR'
        elif 'фстэк' in name_lower:
            return 'ORGANIZATION_FSTEK'
        elif any(org in name_lower for org in ['ооо', 'ао', 'зao', 'фгбу', 'фгу']):
            return 'ORGANIZATION_COMPANY'
        elif 'институт' in name_lower or 'служба' in name_lower:
            return 'ORGANIZATION_INSTITUTION'
        else:
            return 'OTHER'
    
    def should_never_merge(self, name1: str, name2: str) -> bool:
        """Check if two entities should NEVER be merged"""
        # Extract key identifiers
        id1 = self.extract_identifiers(name1)
        id2 = self.extract_identifiers(name2)
        
        # If both have different standard numbers, never merge
        std1 = re.search(r'(гост\s+r?\s*[\d\.]+[\d-]*)', name1.lower())
        std2 = re.search(r'(гост\s+r?\s*[\d\.]+[\d-]*)', name2.lower())
        if std1 and std2 and std1.group(1) != std2.group(1):
            return True
        
        # If both have different law numbers, never merge
        law1 = re.search(r'(№\s*\d+-\w+)', name1.lower())
        law2 = re.search(r'(№\s*\d+-\w+)', name2.lower())
        if law1 and law2 and law1.group(1) != law2.group(1):
            return True
        
        # If both have different dates, never merge
        date1 = re.search(r'(\d+\s*июнь[аыя]*\s*\d{4})', name1.lower())
        date2 = re.search(r'(\d+\s*июнь[аыя]*\s*\d{4})', name2.lower())
        if date1 and date2 and date1.group(1) != date2.group(1):
            return True
        
        # Same entity type but completely different content
        type1 = self.extract_entity_type(name1)
        type2 = self.extract_entity_type(name2)
        
        if type1 == type2 and type1 in ['STANDARD', 'LAW_NUMBER', 'DATE']:
            # Different standards/dates/laws should never merge
            if name1.lower() != name2.lower():
                return True
        
        return False
    
    def extract_identifiers(self, name: str) -> Set[str]:
        """Extract key identifiers from entity name"""
        identifiers = set()
        
        # Extract numbers
        numbers = re.findall(r'\b(\d{3,})\b', name)
        identifiers.update(numbers)
        
        # Extract law numbers
        laws = re.findall(r'(№\s*\d+-\w+)', name, re.IGNORECASE)
        identifiers.update(laws)
        
        # Extract GOST numbers
        gosts = re.findall(r'(гост\s+r?\s*[\d\.]+[\d-]*)', name, re.IGNORECASE)
        identifiers.update(gosts)
        
        return identifiers
    
    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison"""
        if not name:
            return ""
        
        normalized = name.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.replace('—', '-').replace('–', '-')
        normalized = normalized.replace('"', '"').replace('"', '"')
        
        return normalized
    
    def is_abbreviation(self, short_name: str, long_name: str) -> bool:
        """Check if short_name is an abbreviation of long_name"""
        short_norm = self.normalize_name(short_name)
        long_norm = self.normalize_name(long_name)
        
        # Short must be significantly shorter
        if len(short_norm) > len(long_norm) * 0.7:
            return False
        
        # Check if short is contained in long
        if short_norm in long_norm:
            return True
        
        # Check abbreviation rules
        for abbrev, full_forms in self.abbreviation_rules.items():
            if abbrev in short_norm:
                if any(form in long_norm for form in full_forms):
                    return True
        
        return False
    
    def similarity_score(self, name1: str, name2: str) -> float:
        """Calculate similarity with strict rules"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Check if should never merge
        if self.should_never_merge(name1, name2):
            return 0.0
        
        # One must be abbreviation of another
        if not (self.is_abbreviation(name1, name2) or self.is_abbreviation(name2, name1)):
            # For exact same words but different order/case, give moderate score
            words1 = set(norm1.split())
            words2 = set(norm2.split())
            
            # If they share few words, don't merge
            if len(words1 & words2) < min(len(words1), len(words2)) * 0.5:
                return 0.0
        
        # Use SequenceMatcher for fuzzy matching
        if HAS_FUZZY:
            ratio = SequenceMatcher(None, norm1, norm2).ratio()
            
            # Boost score if one is substring of another
            if norm1 in norm2 or norm2 in norm1:
                ratio = max(ratio, 0.90)
            
            return ratio
        
        return 0.0
    
    def find_canonical(self, name: str, candidates: List[str]) -> str:
        """Find the best canonical name - prefer complete forms"""
        if not candidates:
            return name
        
        # Sort by length (longest first) and completeness
        sorted_candidates = sorted(candidates, key=lambda x: (-len(x), x))
        
        for candidate in sorted_candidates:
            if self.similarity_score(name, candidate) >= self.threshold:
                return candidate
        
        return sorted_candidates[0] if sorted_candidates else name
    
    def group_similar_entities(self, entities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group similar entities with strict rules"""
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
                score = self.similarity_score(name, canonical_name)
                
                # Only join group if similarity is high AND no "never merge" rules apply
                if score >= self.threshold and not self.should_never_merge(name, canonical_name):
                    found_group = canonical_name
                    break
            
            if found_group:
                groups[found_group].append(entity)
            else:
                groups[name].append(entity)
        
        return groups
    
    def deduplicate(self, entities: List[Dict]) -> Tuple[List[Dict], Dict]:
        """Deduplicate entities with strict rules"""
        print(f"\nDeduplicating {len(entities)} entities (strict mode)...")
        
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
                merged_entities.append(group[0])
                stats['total_after'] += 1
            else:
                merged = self._merge_group(canonical_name, group)
                merged_entities.append(merged)
                stats['total_after'] += 1
                stats['merged_count'] += len(group) - 1
                
                stats['groups'].append({
                    'canonical': canonical_name,
                    'variants': [e.get('text', '') for e in group if e.get('text', '') != canonical_name],
                    'count': len(group)
                })
        
        print(f"  Merged {stats['merged_count']} duplicates into {stats['total_after']} unique entities")
        print(f"  Reduction: {(1 - stats['total_after']/stats['total_before'])*100:.1f}%")
        
        return merged_entities, stats
    
    def _merge_group(self, canonical_name: str, group: List[Dict]) -> Dict:
        """Merge a group of similar entities"""
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
    parser = argparse.ArgumentParser(description='Strict entity deduplication for GOST documents')
    parser.add_argument('--input', default='/root/qwen/ai_agent/extraction_results_final/all_entities.json',
                       help='Input entities JSON file')
    parser.add_argument('--output-dir', default='/root/qwen/ai_agent/deduplicated_entities_strict',
                       help='Output directory')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='Similarity threshold (default: 0.95 - very strict)')
    parser.add_argument('--review-only', action='store_true',
                       help='Only show duplicate groups, do not merge')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("STRICT ENTITY DEDUPLICATION")
    print("=" * 80)
    print(f"\nThreshold: {args.threshold} (higher = more conservative)")
    print("Rules:")
    print("  ✓ Merge: 'ФСТЭК' → 'ФСТЭК России'")
    print("  ✗ NO MERGE: Different GOST numbers, dates, law numbers")
    print("  ✗ NO MERGE: 'Стандартинформ' ≠ 'Москва Стандартинформ 2018'")
    print()
    
    # Load entities
    print(f"Loading entities from {args.input}...")
    entities = load_entities(args.input)
    print(f"  Loaded {len(entities)} entities")
    
    # Create deduplicator
    deduplicator = StrictEntityDeduplicator(threshold=args.threshold)
    
    # Perform deduplication
    if args.review_only:
        print("\n[REVIEW MODE] Showing potential duplicate groups...")
        groups = deduplicator.group_similar_entities(entities)
        
        duplicate_groups = [(name, group) for name, group in groups.items() if len(group) > 1]
        duplicate_groups.sort(key=lambda x: -len(x[1]))
        
        print(f"\nFound {len(duplicate_groups)} groups with duplicates:")
        for i, (canonical, group) in enumerate(duplicate_groups[:30], 1):
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
        output_file = Path(args.output_dir) / "all_entities_strict.json"
        save_entities(merged_entities, str(output_file))
        print(f"\n  Saved deduplicated entities to {output_file}")
        
        # Save merge statistics
        stats_file = Path(args.output_dir) / "deduplication_stats_strict.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"  Saved statistics to {stats_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("STRICT DEDUPLICATION COMPLETE")
        print("=" * 80)
        print(f"\nBefore: {stats['total_before']} entities")
        print(f"After:  {stats['total_after']} entities")
        print(f"Merged: {stats['merged_count']} duplicates")
        
        # Show top merged groups
        if stats['groups']:
            print("\nTop merged groups (should be TRUE variants only):")
            for group in sorted(stats['groups'], key=lambda x: -x['count'])[:15]:
                print(f"\n  {group['canonical']}")
                print(f"    Variants ({len(group['variants'])}): {', '.join(group['variants'][:3])}")
                if len(group['variants']) > 3:
                    print(f"    ... and {len(group['variants']) - 3} more")


if __name__ == "__main__":
    main()
