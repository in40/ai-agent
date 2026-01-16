"""
Utility module for rendering markdown content in the terminal.
"""

import re
from typing import Optional
import emoji


def render_markdown(text: str) -> str:
    """
    Render markdown content in the terminal with basic formatting.

    Args:
        text: The markdown text to render

    Returns:
        The formatted text suitable for terminal display
    """
    if not text:
        return ""

    # Convert emojis from :emoji: format to actual emojis
    text = emoji.emojize(text, variant="emoji_type")

    # Process markdown elements
    lines = text.split('\n')
    processed_lines = []

    in_code_block = False
    code_language = ""

    for line in lines:
        # Handle headings
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            heading_level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            # Create a simple heading representation for terminal with enhanced colors
            if heading_level == 1:
                processed_lines.append(f"\033[1;35m{'=' * min(heading_level * 2, 10)} {heading_text} {'=' * min(heading_level * 2, 10)}\033[0m")  # Magenta
            elif heading_level == 2:
                processed_lines.append(f"\033[1;33m{'=' * min(heading_level * 2, 10)} {heading_text} {'=' * min(heading_level * 2, 10)}\033[0m")  # Yellow
            else:
                processed_lines.append(f"\033[1;36m{'=' * min(heading_level * 2, 10)} {heading_text} {'=' * min(heading_level * 2, 10)}\033[0m")  # Cyan
            continue

        # Handle code blocks (```lang or ``` alone)
        if line.strip().startswith('```'):
            if not in_code_block:
                # Starting a code block
                in_code_block = True
                code_language = line.strip()[3:].strip()  # Get language after ```
                processed_lines.append("\033[48;5;235m\033[38;5;15m")  # Dark background
            else:
                # Ending a code block
                in_code_block = False
                code_language = ""
                processed_lines.append("\033[0m")  # Reset formatting
            continue

        # Handle inline code (`code`)
        if '`' in line:
            # Replace inline code with highlighted version
            line = re.sub(r'`([^`]+)`', r'\033[48;5;235m\033[38;5;15m \1 \033[0m', line)

        # Handle bold (**text** or __text__)
        if '**' in line or '__' in line:
            line = re.sub(r'\*\*(.*?)\*\*', r'\033[1;37m\1\033[0m', line)  # White bold
            line = re.sub(r'__(.*?)__', r'\033[1;37m\1\033[0m', line)      # White bold

        # Handle italic (*text* or _text_)
        if '*' in line or '_' in line:
            line = re.sub(r'(?<!\*)\*([^\*]+)\*(?!\*)', r'\033[3;36m\1\033[0m', line)  # Cyan italic
            line = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'\033[3;36m\1\033[0m', line)      # Cyan italic

        # Handle bullet points
        if re.match(r'^\s*[\-\*\+]\s+', line):
            line = re.sub(r'^(\s*)([\-\*\+])\s+', r'\1\033[32m•\033[0m ', line)

        # Handle numbered lists
        if re.match(r'^\s*\d+\.\s+', line):
            line = re.sub(r'^(\s*)(\d+)\.(\s+)', r'\1\033[32m\2.\033[0m\3', line)

        # Handle links [text](url)
        if '](' in line:
            line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\033[4;34m\1\033[0m\033[94m (\2)\033[0m', line)  # Blue underlined link text

        # Handle horizontal rules
        if re.match(r'^\s*[-*_]{3,}\s*$', line):
            line = "\033[90m" + "-" * 50 + "\033[0m"

        # Add the line to processed lines
        if in_code_block:
            processed_lines.append(line)
        else:
            processed_lines.append(line)

    # Join the processed lines
    result = '\n'.join(processed_lines)

    # Ensure we close any open formatting
    if in_code_block:
        result += "\033[0m"

    return result


def print_markdown(text: str) -> None:
    """
    Print markdown content to the terminal with formatting applied.
    
    Args:
        text: The markdown text to print
    """
    formatted_text = render_markdown(text)
    print(formatted_text)


if __name__ == "__main__":
    # Test the markdown renderer
    sample_markdown = """
# Heading 1
## Heading 2
### Heading 3

This is **bold text** and this is *italic text*.
Also, this is `inline code`.

- Item 1
- Item 2
- Item 3

1. First item
2. Second item
3. Third item

[Link text](https://example.com)

Horizontal rule:
---

Code block:
```python
def hello():
    print("Hello, world!")
```

More `inline code` here.
"""
    
    print("Original text:")
    print(sample_markdown)
    print("\nRendered text:")
    print_markdown(sample_markdown)