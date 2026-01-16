#!/usr/bin/env python3
"""
Test script to verify emoji and color support in LLM response rendering
"""

from utils.markdown_renderer import print_markdown

def test_emoji_and_color_rendering():
    """Test the new emoji and color rendering functionality"""
    
    print("Testing Emoji and Color Support in LLM Response Rendering\n")
    print("="*60)
    
    # Sample text with emojis and markdown formatting
    sample_text = """
# Heading 1 :star:
## Heading 2 :rocket:
### Heading 3 :gear:

This is **bold text** :white_check_mark: and this is *italic text* :grey_question:.
Also, this is `inline code` :computer:.

- Item 1 :one:
- Item 2 :two:
- Item 3 :three:

1. First item :arrow_right:
2. Second item :arrow_right:
3. Third item :arrow_right:

[Link text](https://example.com) :link:

Horizontal rule:
---

Code block:
```python
def hello():
    print("Hello, world!")  # :wave:
```

More `inline code` here with :bulb: emoji.
"""

    print("Sample text with emojis and markdown formatting:")
    print("-" * 40)
    print_markdown(sample_text)
    print("-" * 40)
    
    print("\nAdditional emoji test:")
    print("-" * 40)
    emoji_test = """
# Emojis in Different Contexts :smile:

- Emojis in **bold** :fire: :boom:
- Emojis in *italic* :heart: :sparkles:
- Emojis in `code` :robot: :computer:
- Emojis in links [click here :point_up:](https://example.com)
- Emojis in headings :tada:

:thumbs_up: All emojis should render properly!
"""
    print_markdown(emoji_test)
    print("-" * 40)

if __name__ == "__main__":
    test_emoji_and_color_rendering()