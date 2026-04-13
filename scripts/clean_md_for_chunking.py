#!/usr/bin/env python3
"""
Pre-process .md files from Document Store for LLM chunking.

Converts LaTeX formulas to Unicode inline code blocks and removes
formatting noise so the LLM treats all content as regular text.

Usage:
    python scripts/clean_md_for_chunking.py                     # Process all files
    python scripts/clean_md_for_chunking.py --dry-run            # Show what would change
    python scripts/clean_md_for_chunking.py --file path/to.md   # Process single file
"""
import os
import re
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DOCSTORE = "/root/qwen/ai_agent/document-store-mcp-server/data/ingested"

# ============================================================================
# LaTeX → Unicode mapping table
# ============================================================================
LATEX_TO_UNICODE = {
    # Greek letters
    r'\alpha': 'α',   r'\beta': 'β',    r'\gamma': 'γ',   r'\delta': 'δ',
    r'\epsilon': 'ε', r'\zeta': 'ζ',    r'\eta': 'η',     r'\theta': 'θ',
    r'\iota': 'ι',    r'\kappa': 'κ',   r'\lambda': 'λ',  r'\mu': 'μ',
    r'\nu': 'ν',      r'\xi': 'ξ',      r'\pi': 'π',      r'\rho': 'ρ',
    r'\sigma': 'σ',   r'\tau': 'τ',     r'\upsilon': 'υ', r'\phi': 'φ',
    r'\chi': 'χ',     r'\psi': 'ψ',     r'\omega': 'ω',
    r'\Gamma': 'Γ',   r'\Delta': 'Δ',   r'\Theta': 'Θ',   r'\Lambda': 'Λ',
    r'\Xi': 'Ξ',      r'\Pi': 'Π',      r'\Sigma': 'Σ',   r'\Phi': 'Φ',
    r'\Psi': 'Ψ',     r'\Omega': 'Ω',

    # Operators
    r'\times': '×',   r'\cdot': '·',    r'\div': '÷',     r'\pm': '±',
    r'\mp': '∓',      r'\oplus': '⊕',   r'\otimes': '⊗',
    r'\parallel': '∥', r'\mid': '|',    r'\nmid': '∤',

    # Relations
    r'\leq': '≤',     r'\le': '≤',      r'\geq': '≥',     r'\ge': '≥',
    r'\neq': '≠',     r'\ne': '≠',      r'\approx': '≈',  r'\equiv': '≡',
    r'\in': '∈',      r'\notin': '∉',   r'\subset': '⊂',  r'\supset': '⊃',
    r'\subseteq': '⊆', r'\supseteq': '⊇',

    # Set/logic
    r'\cup': '∪',     r'\cap': '∩',     r'\land': '∧',    r'\lor': '∨',
    r'\neg': '¬',     r'\forall': '∀',  r'\exists': '∃',  r'\nexists': '∄',
    r'\emptyset': '∅', r'\varnothing': '∅',

    # Calculus/analysis
    r'\infty': '∞',   r'\partial': '∂',  r'\nabla': '∇',   r'\sum': 'Σ',
    r'\prod': 'Π',    r'\int': '∫',

    # Arrows
    r'\to': '→',      r'\rightarrow': '→',   r'\leftarrow': '←',
    r'\leftrightarrow': '↔',  r'\implies': '⇒',

    # Misc
    r'\dots': '…',    r'\ldots': '…',    r'\cdots': '…',
    r'\backslash': ' ',  # Line continuation → space
    r'\prime': '′',   r'\backprime': '‵',
}

# Commands that wrap content but have no Unicode equivalent
# \text{foo} → foo, \mathrm{foo} → foo, \mathbf{foo} → foo
STRIP_CMDS = ['text', 'mathrm', 'mathbf', 'mathit', 'mathsf', 'mathtt',
              'operatorname', 'mathbb', 'mathcal', 'mathfrak']

# ============================================================================
# Formula conversion
# ============================================================================

def convert_latex_to_unicode(text: str) -> str:
    """Convert LaTeX commands to Unicode equivalents."""
    result = text
    for latex_cmd, unicode_char in LATEX_TO_UNICODE.items():
        result = result.replace(latex_cmd, unicode_char)
    return result


def strip_latex_wrappers(text: str) -> str:
    """Remove LaTeX wrapper commands, keeping inner content."""
    for cmd in STRIP_CMDS:
        pattern = rf'\\{cmd}\{{([^}}]*)\}}'
        text = re.sub(pattern, r'\1', text)
    return text


def convert_frac(match) -> str:
    """Convert \frac{a}{b} to a/b."""
    num = match.group(1)
    den = match.group(2)
    return f"{num}/{den}"


def convert_formula(formula: str) -> str:
    """
    Convert a single LaTeX formula (without $ delimiters) to inline code.
    E.g. "K_{MAC} = abc123 \backslash \backslash" → "K_MAC = abc123"
    """
    text = formula

    # Convert \frac{a}{b} → a/b (before other processing)
    text = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', convert_frac, text)

    # Strip wrapper commands
    text = strip_latex_wrappers(text)

    # Convert LaTeX commands to Unicode
    text = convert_latex_to_unicode(text)

    # Convert subscripts: _{text} → _text, _x → _x
    text = re.sub(r'_\{([^}]*)\}', r'_\1', text)

    # Convert superscripts: ^{text} → ^text, ^x → ^x
    text = re.sub(r'\^\{([^}]*)\}', r'^\1', text)

    # Remove \left and \right (just delimiters)
    text = re.sub(r'\\left', '', text)
    text = re.sub(r'\\right', '', text)

    # Remove \quad, \qquad, \; \: \, (spacing commands)
    text = re.sub(r'\\[q]?quad|[;:,\!]', ' ', text)

    # Remove \text{-} → just -
    text = text.replace(r'\text{-}', '-')
    text = text.replace(r'\text{ }', ' ')

    # Remove LaTeX environment wrappers: \begin{...}, \end{...}
    text = re.sub(r'\\begin\{[^}]*\}', '', text)
    text = re.sub(r'\\end\{[^}]*\}', '', text)

    # Convert \\ (line continuation) to newline
    text = re.sub(r'\s*\\\\\s*', '\n', text)

    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)

    # Remove trailing \backslash (line continuation at end of formula)
    text = re.sub(r'\s*\\backslash\s*$', '', text)

    return text.strip()


def convert_all_formulas(content: str) -> str:
    """
    Convert all $...$ and $$...$$ formulas in content to inline code blocks.
    """
    # Handle display math $$...$$ first (multi-line)
    def replace_display(match):
        formula = match.group(1).strip()
        converted = convert_formula(formula)
        # Split converted result into lines, wrap each non-empty line
        lines = [l.strip() for l in converted.split('\n') if l.strip()]
        if len(lines) <= 1:
            return f"`{converted}`"
        else:
            return '\n'.join(f"`{l}`" for l in lines)

    content = re.sub(r'\$\$([^$]+)\$\$', replace_display, content, flags=re.DOTALL)

    # Handle inline math $...$
    def replace_inline(match):
        formula = match.group(1)
        # Skip if already processed (has backticks)
        if formula.startswith('`') or formula.endswith('`'):
            return f'${formula}$'
        converted = convert_formula(formula)
        return f"`{converted}`"

    content = re.sub(r'\$([^$\n]+)\$', replace_inline, content)

    return content


# ============================================================================
# Document cleanup
# ============================================================================

def remove_page_markers(content: str) -> str:
    """Remove HTML page markers and repeated page headers."""
    # <!-- Page X -->
    content = re.sub(r'<!--\s*Page\s+\d+\s*-->', '', content)

    # Repeated document title headers with # prefix
    content = re.sub(r'\n#\s*P\s+[\d.\u2014—]+\s*\n', '\n', content)
    content = re.sub(r'\n#\s*Р\s+[\d.\u2014—]+\s*\n', '\n', content)  # Cyrillic P

    # Bare page headers (no # prefix) - standalone lines like "P 1323565.1.013—2017"
    content = re.sub(r'^P\s+[\d.\u2014—]+\s*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^Р\s+[\d.\u2014—]+\s*$', '', content, flags=re.MULTILINE)  # Cyrillic P

    # Cross-reference lines: "1323565.1.010—2017 Информационная технология..."
    # These are header/footer artifacts from PDF extraction
    content = re.sub(r'^[\d.\u2014—]+\s+Информационная технология.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^БЗ\s+[\d—]+/[\d]+\s*$', '', content, flags=re.MULTILINE)  # "БЗ 1—2018/153"

    return content


def remove_table_continuation_markers(content: str) -> str:
    """Remove "Продолжение таблицы X" and similar."""
    content = re.sub(r'[#|]+\s*Продолжение\s+таблицы?\s+\d+\s*[|]*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'[#|]+\s*Окончание\s+таблицы?\s+\d+\s*[|]*', '', content, flags=re.IGNORECASE)
    return content


def normalize_whitespace(content: str) -> str:
    """Collapse excessive blank lines and trailing whitespace."""
    # Replace 3+ consecutive newlines with 2
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Remove trailing whitespace on each line
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)

    # Remove leading/trailing blank lines
    content = content.strip()

    return content


def remove_trailing_line_continuations(content: str) -> str:
    """Remove trailing \\ line continuation markers from plain text lines."""
    lines = content.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith(' \\\\'):
            # Line ends with \ continuation - remove it
            cleaned.append(stripped[:-2].rstrip())
        elif stripped.endswith('\\\\'):
            cleaned.append(stripped[:-2].rstrip())
        else:
            cleaned.append(stripped)
    return '\n'.join(cleaned)


def clean_document(content: str) -> str:
    """
    Full cleaning pipeline:
    1. Remove page markers
    2. Remove table continuation markers
    3. Convert LaTeX formulas to Unicode code blocks
    4. Remove trailing line continuation markers (\\)
    5. Normalize whitespace
    """
    content = remove_page_markers(content)
    content = remove_table_continuation_markers(content)
    content = convert_all_formulas(content)
    content = remove_trailing_line_continuations(content)
    content = normalize_whitespace(content)
    return content


# ============================================================================
# Main
# ============================================================================

def find_md_files(docstore: str) -> list:
    """Find all .md files in document store."""
    md_files = []
    for root, dirs, filenames in os.walk(docstore):
        for f in filenames:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))
    return sorted(md_files)


def process_file(fpath: str, dry_run: bool = False) -> dict:
    """
    Process a single .md file.
    Returns stats dict.
    """
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        original = f.read()

    cleaned = clean_document(original)

    # Count changes
    latex_count_orig = len(re.findall(r'\$[^$\n]+\$', original))
    display_count_orig = len(re.findall(r'\$\$[^$]+\$\$', original, re.DOTALL))
    latex_count_new = len(re.findall(r'\$[^$\n]+\$', cleaned))
    display_count_new = len(re.findall(r'\$\$[^$]+\$\$', cleaned, re.DOTALL))
    code_block_count = len(re.findall(r'`[^`]+`', cleaned))
    page_markers_orig = len(re.findall(r'<!--\s*Page\s+\d+\s*-->', original))

    stats = {
        'file': os.path.basename(fpath),
        'original_size': len(original),
        'cleaned_size': len(cleaned),
        'formulas_converted': (latex_count_orig - latex_count_new) + (display_count_orig - display_count_new),
        'code_blocks_created': code_block_count,
        'page_markers_removed': page_markers_orig,
        'size_reduction': len(original) - len(cleaned),
    }

    if not dry_run:
        # Write clean .txt file alongside .md
        txt_path = fpath[:-3] + '.txt'  # Replace .md with .txt
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        stats['output'] = txt_path
    else:
        stats['output'] = '(dry run)'

    return stats


def main():
    parser = argparse.ArgumentParser(description='Clean .md files for LLM chunking')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change without writing')
    parser.add_argument('--file', type=str, help='Process single file only')
    args = parser.parse_args()

    if args.file:
        files = [args.file]
    else:
        files = find_md_files(DOCSTORE)

    print(f"Found {len(files)} .md files to process")
    if args.dry_run:
        print("*** DRY RUN - no files will be modified ***\n")

    total_formulas = 0
    total_markers = 0
    total_code = 0

    for fpath in files:
        try:
            stats = process_file(fpath, dry_run=args.dry_run)
            if stats['formulas_converted'] > 0 or stats['page_markers_removed'] > 0:
                print(f"  {stats['file']}: "
                      f"{stats['formulas_converted']} formulas → code, "
                      f"{stats['page_markers_removed']} page markers removed, "
                      f"{stats['code_blocks_created']} code blocks total")
            total_formulas += stats['formulas_converted']
            total_markers += stats['page_markers_removed']
            total_code += stats['code_blocks_created']
        except Exception as e:
            print(f"  ERROR {os.path.basename(fpath)}: {e}")

    print(f"\nSummary:")
    print(f"  Files processed: {len(files)}")
    print(f"  Formulas converted: {total_formulas}")
    print(f"  Page markers removed: {total_markers}")
    print(f"  Total code blocks created: {total_code}")


if __name__ == '__main__':
    main()
